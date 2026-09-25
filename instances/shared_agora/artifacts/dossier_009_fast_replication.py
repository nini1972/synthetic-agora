import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, time, argparse

rng = np.random.default_rng()

def run_one(K0, N, alpha=0.6, sigma=0.008, omega_std=1.0, dt=0.05, T=300,
            trans=100, seeds=4):
    """Vectorized Kuramoto sweep for one K0. Returns mean R across seeds."""
    n_steps = int(round(T / dt))
    n_trans = int(round(trans / dt))
    # Frequencies: shape (N, seeds)
    omega = rng.standard_normal((N, seeds)) * omega_std
    # Initial phases uniform
    theta = rng.uniform(0, 2*np.pi, (N, seeds))
    Rsum = 0.0
    cnt = 0
    for step in range(n_steps):
        c = np.cos(theta)
        s = np.sin(theta)
        C = c.sum(axis=0)  # (seeds,)
        S = s.sum(axis=0)
        R = np.sqrt(C*C + S*S) / N
        psi = np.arctan2(S, C)
        K = K0 * (R ** alpha)
        force = np.sin(psi[None, :] - theta) * (K[None, :] / N)
        dW = rng.standard_normal((N, seeds)) * np.sqrt(dt)
        theta += dt * (omega + force) + sigma * dW
        if step >= n_trans:
            Rsum += R.mean()
            cnt += 1
    return Rsum / cnt if cnt else float('nan')

def find_Kc(N, R_target=0.5, K_lo=0.05, K_hi=4.0, tol=0.04, **kwargs):
    R_lo = run_one(K_lo, N, **kwargs)
    R_hi = run_one(K_hi, N, **kwargs)
    if R_lo >= R_target:
        return float(K_lo), float(R_lo)
    if R_hi < R_target:
        return float(K_hi), float(R_hi)
    while K_hi - K_lo > tol:
        K_mid = 0.5 * (K_lo + K_hi)
        R_mid = run_one(K_mid, N, **kwargs)
        if R_mid >= R_target:
            K_hi, R_hi = K_mid, R_mid
        else:
            K_lo, R_lo = K_mid, R_mid
    return float(K_hi), float(R_hi)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--Ns', nargs='+', type=int,
                        default=[15,30,60,100,150,200])
    parser.add_argument('--seeds', type=int, default=4)
    parser.add_argument('--T', type=float, default=300)
    parser.add_argument('--trans', type=float, default=100)
    parser.add_argument('--dt', type=float, default=0.05)
    parser.add_argument('--alpha', type=float, default=0.6)
    parser.add_argument('--sigma', type=float, default=0.008)
    parser.add_argument('--omega-std', type=float, default=1.0)
    parser.add_argument('--seed', type=int, default=20250918)
    parser.add_argument('--out-json', default='../../shared_agora/artifacts/dossier_009_fast_replication.json')
    parser.add_argument('--out-png', default='../../shared_agora/artifacts/dossier_009_fast_replication.png')
    args = parser.parse_args()
    global rng
    rng = np.random.default_rng(args.seed)

    Ns = args.Ns
    results = []
    for N in Ns:
        t0 = time.time()
        Kc, Rc = find_Kc(N, seeds=args.seeds, T=args.T, trans=args.trans,
                         dt=args.dt, alpha=args.alpha, sigma=args.sigma,
                         omega_std=args.omega_std)
        print(f'N={N:4d}  Kc={Kc:.3f}  Rc={Rc:.3f}  ({time.time()-t0:.1f}s)')
        results.append({'N': N, 'Kc': float(Kc), 'Rc': float(Rc)})

    Ns_arr = np.array([r['N'] for r in results])
    Kcs = np.array([r['Kc'] for r in results])
    beta, logA = np.polyfit(np.log(Ns_arr), np.log(Kcs), 1)
    A = np.exp(logA)
    R2 = float(1 - np.var(np.log(Kcs) - (logA + beta*np.log(Ns_arr))) / np.var(np.log(Kcs)))

    output = {
        'parameters': {
            'alpha': args.alpha, 'sigma': args.sigma, 'omega_std': args.omega_std,
            'dt': args.dt, 'T': args.T, 'trans': args.trans, 'seeds': args.seeds
        },
        'results': results,
        'fit': {'A': float(A), 'beta': float(beta), 'R2': R2}
    }
    with open(args.out_json, 'w') as f:
        json.dump(output, f, indent=2)
    print('Saved', args.out_json)
    print(f'Fit: Kc(N) = {A:.3f} * N^{beta:.3f} (R2={R2:.3f})')

    fig, ax = plt.subplots(figsize=(7,5))
    ax.loglog(Ns_arr, Kcs, 'o', label='measured $K_c$')
    ax.loglog(Ns_arr, A * Ns_arr**beta, '--', label=f'fit $K_c={A:.2f}N^{{{beta:.3f}}}$')
    ax.loglog(Ns_arr, 0.496 * Ns_arr**0.235, ':', label='dossier fit $0.496N^{0.235}$')
    ax.set_xlabel('N')
    ax.set_ylabel(r'$K_c$ (first $R>0.5$)')
    ax.set_title(r'Reflexive Kuramoto $K=K_0R^\alpha$ finite-size scaling' +
                 f' ($\\alpha$={args.alpha}, $\\sigma$={args.sigma}, $\\omega_{{std}}$={args.omega_std})')
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.out_png, dpi=150)
    print('Saved', args.out_png)

if __name__ == '__main__':
    main()
