import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
import json, os, time

# Thomas cyclically symmetric labyrinth attractor
# dx/dt = sin(y) - b x, dy/dt = sin(z) - b y, dz/dt = sin(x) - b z

rng = np.random.default_rng(42)
DT = 0.05
T_TRANS = 400.0
T_LYAP = 400.0
T_D2 = 400.0
T_LZ = 200.0
N_POINTS_D2 = 2048
GRID_M = 24  # block complexity grid resolution per dimension

def rhs_state(x, b):
    return np.array([np.sin(x[1]) - b*x[0],
                     np.sin(x[2]) - b*x[1],
                     np.sin(x[0]) - b*x[2]], dtype=float)

def jacobian(x, b):
    return np.array([[-b, np.cos(x[1]), 0.0],
                     [0.0, -b, np.cos(x[2])],
                     [np.cos(x[0]), 0.0, -b]], dtype=float)

def rhs_tangent(x, d, b):
    return jacobian(x, b) @ d

def lyap_and_sample(b, x0=None, d0=None):
    if x0 is None:
        x0 = rng.uniform(-2.0, 2.0, 3)
    if d0 is None:
        d0 = rng.standard_normal(3)
        d0 /= np.linalg.norm(d0)
    x = x0.copy().astype(float)
    d = d0.copy().astype(float)

    # transient
    n_trans = int(T_TRANS / DT)
    for _ in range(n_trans):
        k1x = rhs_state(x, b)
        k1d = rhs_tangent(x, d, b)
        k2x = rhs_state(x + 0.5*DT*k1x, b)
        k2d = rhs_tangent(x + 0.5*DT*k1x, d + 0.5*DT*k1d, b)
        k3x = rhs_state(x + 0.5*DT*k2x, b)
        k3d = rhs_tangent(x + 0.5*DT*k2x, d + 0.5*DT*k2d, b)
        k4x = rhs_state(x + DT*k3x, b)
        k4d = rhs_tangent(x + DT*k3x, d + DT*k3d, b)
        x += DT/6.0*(k1x + 2*k2x + 2*k3x + k4x)
        d += DT/6.0*(k1d + 2*k2d + 2*k3d + k4d)

    # maximal Lyapunov exponent
    n_lyap = int(T_LYAP / DT)
    lyap_sum = 0.0
    for _ in range(n_lyap):
        k1x = rhs_state(x, b)
        k1d = rhs_tangent(x, d, b)
        k2x = rhs_state(x + 0.5*DT*k1x, b)
        k2d = rhs_tangent(x + 0.5*DT*k1x, d + 0.5*DT*k1d, b)
        k3x = rhs_state(x + 0.5*DT*k2x, b)
        k3d = rhs_tangent(x + 0.5*DT*k2x, d + 0.5*DT*k2d, b)
        k4x = rhs_state(x + DT*k3x, b)
        k4d = rhs_tangent(x + DT*k3x, d + DT*k3d, b)
        x += DT/6.0*(k1x + 2*k2x + 2*k3x + k4x)
        d += DT/6.0*(k1d + 2*k2d + 2*k3d + k4d)
        norm = np.linalg.norm(d)
        lyap_sum += np.log(norm)
        d /= norm
    lambda1 = lyap_sum / T_LYAP

    # sample trajectory for D2 and block complexity after additional transient
    n_d2 = int(T_D2 / DT)
    traj = []
    skip = max(1, n_d2 // N_POINTS_D2)
    for i in range(n_d2):
        k1x = rhs_state(x, b)
        k2x = rhs_state(x + 0.5*DT*k1x, b)
        k3x = rhs_state(x + 0.5*DT*k2x, b)
        k4x = rhs_state(x + DT*k3x, b)
        x += DT/6.0*(k1x + 2*k2x + 2*k3x + k4x)
        if i % skip == 0 and len(traj) < N_POINTS_D2:
            traj.append(x.copy())
    traj = np.array(traj)

    # correlation dimension via Grassberger-Procaccia
    D2 = np.nan
    try:
        tree = cKDTree(traj)
        # choose radii from small to covering range
        dists = tree.query(traj, k=2)[0][:, 1]
        r_min = max(dists.min()*1.5, 1e-12)
        r_max = dists.max()*0.5
        rs = np.geomspace(r_min, r_max, 20)
        counts = tree.count_neighbors(tree, rs)
        N = len(traj)
        C = counts / (N*(N-1))
        valid = (C > 0) & (C < 0.5)
        if valid.sum() >= 5:
            lr = np.log(rs[valid])
            lC = np.log(C[valid])
            slope = np.polyfit(lr, lC, 1)[0]
            D2 = slope
    except Exception as e:
        D2 = np.nan

    # block complexity: occupied cells in coarse-grained 3D grid over trajectory box
    low = traj.min(axis=0)
    high = traj.max(axis=0)
    eps = 1e-9
    idx = np.clip(((traj - low) / (high - low + eps) * (GRID_M - 1)).astype(int), 0, GRID_M - 1)
    block_count = len(np.unique(idx, axis=0))

    # LZ complexity of binarized x-coordinate
    n_lz = int(T_LZ / DT)
    xs = []
    for _ in range(n_lz):
        k1x = rhs_state(x, b)
        k2x = rhs_state(x + 0.5*DT*k1x, b)
        k3x = rhs_state(x + 0.5*DT*k2x, b)
        k4x = rhs_state(x + DT*k3x, b)
        x += DT/6.0*(k1x + 2*k2x + 2*k3x + k4x)
        xs.append(x[0])
    xs = np.array(xs)
    binary = (xs >= np.median(xs)).astype(int)
    lz = lempel_ziv_complexity(binary)
    lz_norm = lz / len(binary)

    return lambda1, D2, block_count, lz_norm, traj

def lempel_ziv_complexity(seq):
    """Lempel-Ziv 76 factor count for a binary sequence."""
    n = len(seq)
    if n == 0:
        return 0
    c = 1
    w_start = 0
    w_end = 1
    while w_end < n:
        word = seq[w_start:w_end+1]
        # search for word as a contiguous substring in the prefix before word start,
        # but in LZ76 the word is compared to the concatenation of all previous factors.
        prefix = seq[:w_start]
        found = False
        L = len(word)
        for i in range(max(0, w_start - L - 1), w_start):
            if i + L <= w_start and np.array_equal(prefix[i:i+L], word):
                found = True
                break
        if found:
            w_end += 1
        else:
            c += 1
            w_start = w_end + 1
            w_end = w_start + 1
    return c

if __name__ == '__main__':
    #b_values = np.linspace(0.16, 0.22, 61)  # fine sweep around claimed threshold
    # Quick but informative sweep
    b_values = np.linspace(0.16, 0.22, 61)
    results = []
    t0 = time.time()
    for idx, b in enumerate(b_values):
        lam, D2, block, lz, traj = lyap_and_sample(b)
        results.append({'b': float(b), 'lambda1': float(lam), 'D2': float(D2),
                        'block_count': int(block), 'lz_norm': float(lz)})
        if idx % 10 == 0:
            print(f"b={b:.4f}  lambda1={lam:.5f}  D2={D2:.3f}  blocks={block}  lz_norm={lz:.4f}")
    print(f"Total time: {time.time()-t0:.1f}s")

    # save JSON
    out_json = '../../shared_agora/artifacts/dossier_002_thomas_results.json'
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2)

    # plots
    bs = np.array([r['b'] for r in results])
    lams = np.array([r['lambda1'] for r in results])
    D2s = np.array([r['D2'] for r in results])
    blocks = np.array([r['block_count'] for r in results])
    lzs = np.array([r['lz_norm'] for r in results])

    fig, axs = plt.subplots(2, 3, figsize=(14, 8))
    axs[0,0].plot(bs, lams, 'ko-')
    axs[0,0].axvline(0.208186, color='r', ls='--', label='claimed $b_c$')
    axs[0,0].axhline(0, color='gray', ls=':')
    axs[0,0].set_xlabel('dissipation b')
    axs[0,0].set_ylabel(r'$\lambda_1$')
    axs[0,0].set_title('Maximal Lyapunov exponent')
    axs[0,0].legend()

    axs[0,1].plot(bs, D2s, 'bs-')
    axs[0,1].axvline(0.208186, color='r', ls='--')
    axs[0,1].set_xlabel('dissipation b')
    axs[0,1].set_ylabel(r'$D_2$')
    axs[0,1].set_title('Grassberger-Procaccia dimension')

    axs[0,2].plot(bs, blocks, 'g^-')
    axs[0,2].axvline(0.208186, color='r', ls='--')
    axs[0,2].set_xlabel('dissipation b')
    axs[0,2].set_ylabel('occupied coarse cells')
    axs[0,2].set_title('Block complexity (coarse-grained)')

    axs[1,0].plot(bs, lzs, 'mD-')
    axs[1,0].axvline(0.208186, color='r', ls='--')
    axs[1,0].set_xlabel('dissipation b')
    axs[1,0].set_ylabel('LZ complexity / length')
    axs[1,0].set_title('Normalized Lempel-Ziv complexity of x(t)')

    # approximate topological entropy = lambda1 if positive, else 0
    topo = np.maximum(lams, 0.0)
    axs[1,1].plot(bs, topo, 'r*-')
    axs[1,1].axvline(0.208186, color='r', ls='--')
    axs[1,1].set_xlabel('dissipation b')
    axs[1,1].set_ylabel(r'$h_{top} \approx \lambda_1^+$')
    axs[1,1].set_title('Approx. topological entropy')

    # example trajectory below and above threshold
    b_low = bs[np.argmin(np.abs(bs - 0.18))]
    b_high = bs[np.argmin(np.abs(bs - 0.21))]
    _, _, _, _, traj_low = lyap_and_sample(b_low)
    _, _, _, _, traj_high = lyap_and_sample(b_high)
    ax3d = fig.add_subplot(2, 3, 6, projection='3d')
    ax3d.plot(traj_low[:,0], traj_low[:,1], traj_low[:,2], alpha=0.4, label=f'b={b_low:.3f}')
    ax3d.plot(traj_high[:,0], traj_high[:,1], traj_high[:,2], alpha=0.4, label=f'b={b_high:.3f}')
    ax3d.set_xlabel('x')
    ax3d.set_ylabel('y')
    ax3d.set_zlabel('z')
    ax3d.set_title('Sample trajectories')
    ax3d.legend()

    fig.tight_layout()
    out_png = '../../shared_agora/artifacts/dossier_002_thomas_replication.png'
    fig.savefig(out_png, dpi=150)
    print(f"Saved {out_png} and {out_json}")
