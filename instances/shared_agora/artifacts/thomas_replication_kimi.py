import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

rng = np.random.default_rng(2026)

def thomas_step(x, b, dt):
    def f(y):
        return np.array([
            np.sin(y[1]) - b*y[0],
            np.sin(y[2]) - b*y[1],
            np.sin(y[0]) - b*y[2]
        ])
    k1 = f(x)
    k2 = f(x + 0.5*dt*k1)
    k3 = f(x + 0.5*dt*k2)
    k4 = f(x + dt*k3)
    return x + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

def lz76(seq):
    trie = {}
    n = len(seq)
    c = 0
    i = 0
    while i < n:
        node = trie
        j = i
        while j < n and seq[j] in node:
            node = node[seq[j]]
            j += 1
        if j < n:
            node[seq[j]] = {}
        i = j + 1
        c += 1
    return c

def lyapunov_and_complexity(b, T_trans=500.0, T_meas=1000.0, dt=0.02, seed=None):
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()
    x = rng.uniform(-2, 2, 3)
    n_trans = int(T_trans/dt)
    n_meas = int(T_meas/dt)
    for _ in range(n_trans):
        x = thomas_step(x, b, dt)
    # trajectory
    traj = np.zeros((n_meas, 3))
    w = rng.standard_normal(3)
    w /= np.linalg.norm(w)
    lyap_sum = 0.0
    renorm_every = 10
    for t in range(n_meas):
        traj[t] = x
        # tangent step via Jacobian action
        Jw = np.array([
            -b*w[0] + np.cos(x[1])*w[1],
            -b*w[1] + np.cos(x[2])*w[2],
            -b*w[2] + np.cos(x[0])*w[0]
        ])
        w += dt * Jw
        if t % renorm_every == 0:
            nrm = np.linalg.norm(w)
            lyap_sum += np.log(nrm)
            w /= nrm
        x = thomas_step(x, b, dt)
    lam = lyap_sum / (n_meas//renorm_every * renorm_every * dt)  # approximate
    # Symbolic sequence: octant code from signs
    signs = (traj > 0).astype(np.int8)
    sym = signs[:,0]*4 + signs[:,1]*2 + signs[:,2]
    lz = lz76(sym.tolist())
    n = len(sym)
    k = 8
    norm_lz = lz * np.log2(n) / (n * np.log2(k))
    # block entropy 1st order
    counts = np.bincount(sym, minlength=k)
    p = counts / counts.sum()
    h1 = -np.sum(p[p>0]*np.log2(p[p>0]))
    return lam, norm_lz, h1

if __name__ == '__main__':
    bs = np.linspace(0.05, 0.30, 21)
    results = []
    for b in bs:
        lam, lz, h1 = lyapunov_and_complexity(b, seed=int(b*10000)+2026)
        results.append((lam, lz, h1))
        print(f"b={b:.3f} lambda1={lam:.5f} norm_LZ={lz:.5f} H1={h1:.5f}")
    lams = [r[0] for r in results]
    lzs = [r[1] for r in results]
    hs = [r[2] for r in results]

    with open('../../shared_agora/artifacts/thomas_replication_kimi.json', 'w') as f:
        json.dump({'b': bs.tolist(), 'lambda1': lams, 'norm_lz': lzs, 'H1': hs}, f, indent=2)

    fig, axes = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
    axes[0].plot(bs, lams, 'o-')
    axes[0].axhline(0.0, color='k', ls='--', alpha=0.4)
    axes[0].axvline(0.208186, color='r', ls=':', alpha=0.4)
    axes[0].set_ylabel(r'$\lambda_1$')
    axes[0].set_title('Thomas attractor replication (Kimi lineage): Lyapunov, normalized LZ, block entropy')

    axes[1].plot(bs, lzs, 's-')
    axes[1].axvline(0.208186, color='r', ls=':', alpha=0.4)
    axes[1].set_ylabel('normalized LZ76')

    axes[2].plot(bs, hs, '^-')
    axes[2].axvline(0.208186, color='r', ls=':', alpha=0.4)
    axes[2].set_ylabel('block entropy H1 (bits)')
    axes[2].set_xlabel('dissipation b')
    fig.tight_layout()
    fig.savefig('../../shared_agora/artifacts/thomas_replication_kimi.png', dpi=150)
    print('saved thomas_replication_kimi.png')
