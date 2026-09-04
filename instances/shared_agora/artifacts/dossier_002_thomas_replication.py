import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
import json, time

rng = np.random.default_rng(42)
DT = 0.05
T_TRANS = 200.0
T_LYAP = 200.0
T_D2 = 200.0
N_POINTS_D2 = 1024
GRID_M = 20

if __name__ == '__main__':
    b_values = np.linspace(0.16, 0.22, 25)
    results = []
    t0 = time.time()
    for ib, b in enumerate(b_values):
        x, y, z = rng.uniform(-2.0, 2.0, 3)
        dt = DT
        # transient
        for _ in range(int(T_TRANS/dt)):
            k1x = np.sin(y) - b*x; k1y = np.sin(z) - b*y; k1z = np.sin(x) - b*z
            x2 = x + 0.5*dt*k1x; y2 = y + 0.5*dt*k1y; z2 = z + 0.5*dt*k1z
            k2x = np.sin(y2) - b*x2; k2y = np.sin(z2) - b*y2; k2z = np.sin(x2) - b*z2
            x3 = x + 0.5*dt*k2x; y3 = y + 0.5*dt*k2y; z3 = z + 0.5*dt*k2z
            k3x = np.sin(y3) - b*x3; k3y = np.sin(z3) - b*y3; k3z = np.sin(x3) - b*z3
            x4 = x + dt*k3x; y4 = y + dt*k3y; z4 = z + dt*k3z
            k4x = np.sin(y4) - b*x4; k4y = np.sin(z4) - b*y4; k4z = np.sin(x4) - b*z4
            x += dt/6.0*(k1x + 2*k2x + 2*k3x + k4x)
            y += dt/6.0*(k1y + 2*k2y + 2*k3y + k4y)
            z += dt/6.0*(k1z + 2*k2z + 2*k3z + k4z)

        # Lyapunov exponent via Heun-style tangent update
        dx, dy, dz = rng.standard_normal(3)
        nrm = np.sqrt(dx*dx + dy*dy + dz*dz); dx /= nrm; dy /= nrm; dz /= nrm
        lyap_sum = 0.0
        n_lyap = int(T_LYAP/dt)
        for _ in range(n_lyap):
            k1x = np.sin(y) - b*x; k1y = np.sin(z) - b*y; k1z = np.sin(x) - b*z
            x2 = x + 0.5*dt*k1x; y2 = y + 0.5*dt*k1y; z2 = z + 0.5*dt*k1z
            k2x = np.sin(y2) - b*x2; k2y = np.sin(z2) - b*y2; k2z = np.sin(x2) - b*z2
            x3 = x + 0.5*dt*k2x; y3 = y + 0.5*dt*k2y; z3 = z + 0.5*dt*k2z
            k3x = np.sin(y3) - b*x3; k3y = np.sin(z3) - b*y3; k3z = np.sin(x3) - b*z3
            x4 = x + dt*k3x; y4 = y + dt*k3y; z4 = z + dt*k3z
            k4x = np.sin(y4) - b*x4; k4y = np.sin(z4) - b*y4; k4z = np.sin(x4) - b*z4
            x += dt/6.0*(k1x + 2*k2x + 2*k3x + k4x)
            y += dt/6.0*(k1y + 2*k2y + 2*k3y + k4y)
            z += dt/6.0*(k1z + 2*k2z + 2*k3z + k4z)

            cx = np.cos(x); cy = np.cos(y); cz = np.cos(z)
            # Heun step for tangent
            d1x = (-b)*dx + cy*dy
            d1y = (-b)*dy + cz*dz
            d1z = (-b)*dz + cx*dx
            tx = dx + dt*d1x; ty = dy + dt*d1y; tz = dz + dt*d1z
            d2x = (-b)*tx + cy*ty
            d2y = (-b)*ty + cz*tz
            d2z = (-b)*tz + cx*tx
            dx += dt/2.0*(d1x + d2x)
            dy += dt/2.0*(d1y + d2y)
            dz += dt/2.0*(d1z + d2z)
            nrm = np.sqrt(dx*dx + dy*dy + dz*dz)
            lyap_sum += np.log(nrm)
            dx /= nrm; dy /= nrm; dz /= nrm
        lambda1 = lyap_sum / T_LYAP

        # sample trajectory for D2 / blocks
        n_d2 = int(T_D2/dt)
        skip = max(1, n_d2 // N_POINTS_D2)
        traj = np.zeros((min(N_POINTS_D2, n_d2//skip + 1), 3))
        k = 0
        for i in range(n_d2):
            k1x = np.sin(y) - b*x; k1y = np.sin(z) - b*y; k1z = np.sin(x) - b*z
            x2 = x + 0.5*dt*k1x; y2 = y + 0.5*dt*k1y; z2 = z + 0.5*dt*k1z
            k2x = np.sin(y2) - b*x2; k2y = np.sin(z2) - b*y2; k2z = np.sin(x2) - b*z2
            x3 = x + 0.5*dt*k2x; y3 = y + 0.5*dt*k2y; z3 = z + 0.5*dt*k2z
            k3x = np.sin(y3) - b*x3; k3y = np.sin(z3) - b*y3; k3z = np.sin(x3) - b*z3
            x4 = x + dt*k3x; y4 = y + dt*k3y; z4 = z + dt*k3z
            k4x = np.sin(y4) - b*x4; k4y = np.sin(z4) - b*y4; k4z = np.sin(x4) - b*z4
            x += dt/6.0*(k1x + 2*k2x + 2*k3x + k4x)
            y += dt/6.0*(k1y + 2*k2y + 2*k3y + k4y)
            z += dt/6.0*(k1z + 2*k2z + 2*k3z + k4z)
            if i % skip == 0 and k < traj.shape[0]:
                traj[k,0] = x; traj[k,1] = y; traj[k,2] = z
                k += 1
        traj = traj[:k]

        D2 = np.nan
        try:
            tree = cKDTree(traj)
            dists = tree.query(traj, k=2)[0][:,1]
            r_min = max(dists.min()*1.5, 1e-12)
            r_max = dists.max()*0.4
            rs = np.geomspace(r_min, r_max, 16)
            counts = tree.count_neighbors(tree, rs)
            N = len(traj)
            C = counts / (N*(N-1))
            valid = (C > 0) & (C < 0.4)
            if valid.sum() >= 5:
                D2 = np.polyfit(np.log(rs[valid]), np.log(C[valid]), 1)[0]
        except Exception:
            pass

        low = traj.min(axis=0); high = traj.max(axis=0); eps = 1e-9
        idx = np.clip(((traj - low)/(high-low+eps)*(GRID_M-1)).astype(int), 0, GRID_M-1)
        block_count = len(np.unique(idx, axis=0))

        results.append({'b': float(b), 'lambda1': float(lambda1), 'D2': float(D2), 'block_count': int(block_count)})
        if ib % 4 == 0:
            print(f"b={b:.4f}  lambda1={lambda1:.5f}  D2={D2:.3f}  blocks={block_count}")
    print(f"Total time: {time.time()-t0:.1f}s")

    with open('../../shared_agora/artifacts/dossier_002_thomas_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    bs = np.array([r['b'] for r in results])
    lams = np.array([r['lambda1'] for r in results])
    D2s = np.array([r['D2'] for r in results])
    blocks = np.array([r['block_count'] for r in results])

    fig, axs = plt.subplots(2, 2, figsize=(11, 9))
    axs[0,0].plot(bs, lams, 'ko-')
    axs[0,0].axvline(0.208186, color='r', ls='--', label='claimed $b_c$')
    axs[0,0].axhline(0, color='gray', ls=':')
    axs[0,0].set_xlabel('dissipation b'); axs[0,0].set_ylabel(r'$\lambda_1$')
    axs[0,0].set_title('Maximal Lyapunov exponent'); axs[0,0].legend()

    axs[0,1].plot(bs, D2s, 'bs-')
    axs[0,1].axvline(0.208186, color='r', ls='--')
    axs[0,1].set_xlabel('dissipation b'); axs[0,1].set_ylabel(r'$D_2$')
    axs[0,1].set_title('Correlation dimension')

    axs[1,0].plot(bs, blocks, 'g^-')
    axs[1,0].axvline(0.208186, color='r', ls='--')
    axs[1,0].set_xlabel('dissipation b'); axs[1,0].set_ylabel('occupied coarse cells')
    axs[1,0].set_title('Coarse-grained block count')

    topo = np.maximum(lams, 0.0)
    axs[1,1].plot(bs, topo, 'r*-')
    axs[1,1].axvline(0.208186, color='r', ls='--')
    axs[1,1].set_xlabel('dissipation b'); axs[1,1].set_ylabel(r'$h_{top}\approx\lambda_1^+$')
    axs[1,1].set_title('Approximate topological entropy')

    fig.tight_layout()
    out_png = '../../shared_agora/artifacts/dossier_002_thomas_replication.png'
    fig.savefig(out_png, dpi=150)
    print(f"Saved {out_png}")
