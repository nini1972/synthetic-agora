import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, os, time

np.random.seed(0)

def kuramoto_reflexive(K0, alpha, sigma, omega, dt, T_trans, T_meas, seeds=1):
    """
    Vectorized Kuramoto with reflexive coupling K(t)=K0*R(t)^alpha.
    dtheta_i/dt = (K(t)/N) sum_j sin(theta_j-theta_i) + sigma*xi_i(t)
    omega: shape (seeds, N)
    Returns R_final mean over measurement window, shape (seeds,)
    """
    N = omega.shape[1]
    theta = np.random.rand(seeds, N) * 2*np.pi
    steps_trans = int(T_trans/dt)
    steps_meas = int(T_meas/dt)
    sdt = np.sqrt(dt) if sigma>0 else 0.0
    for _ in range(steps_trans):
        z = np.exp(1j*theta).mean(axis=1, keepdims=True)
        R = np.abs(z)
        K = K0 * (R**alpha)
        force = K * np.imag(z * np.exp(-1j*theta))
        theta += dt*(omega + force)
        if sigma>0:
            theta += sdt*sigma*np.random.randn(seeds, N)
    Rsum = 0.0
    for _ in range(steps_meas):
        z = np.exp(1j*theta).mean(axis=1, keepdims=True)
        R = np.abs(z)
        K = K0 * (R**alpha)
        force = K * np.imag(z * np.exp(-1j*theta))
        theta += dt*(omega + force)
        if sigma>0:
            theta += sdt*sigma*np.random.randn(seeds, N)
        Rsum += R
    return Rsum / steps_meas

def find_Kc(N, dist_name, dist_params, K0_grid, alpha=0.6, sigma=0.008, seeds=4, dt=0.05, T_trans=60, T_meas=100):
    # draw natural frequencies for each seed
    if dist_name == 'uniform':
        a = dist_params['half_width']
        omega = np.random.uniform(-a, a, size=(seeds, N))
    elif dist_name == 'normal':
        scale = dist_params['sigma']
        omega = np.random.normal(0, scale, size=(seeds, N))
    elif dist_name == 'zero':
        omega = np.zeros((seeds, N))
    else:
        raise ValueError(dist_name)
    meanR = []
    for K0 in K0_grid:
        Rf = kuramoto_reflexive(K0, alpha, sigma, omega, dt, T_trans, T_meas, seeds=seeds)
        meanR.append(Rf.mean())
    meanR = np.array(meanR)
    # Kc = smallest K0 with meanR > 0.5
    above = np.where(meanR > 0.5)[0]
    if len(above)==0:
        return None, meanR
    Kc = K0_grid[above[0]]
    return Kc, meanR

def main():
    alpha = 0.6
    sigma = 0.008
    Ns = np.array([15, 30, 60, 100, 150, 200, 300, 400])
    K0_grid = np.geomspace(0.3, 4.0, 10)
    seeds = 3
    configs = [
        ('uniform', {'half_width':1.0}, 'Uniform ω∈[-1,1]'),
        ('normal', {'sigma':0.5}, 'Normal ω, σ=0.5'),
        ('normal', {'sigma':0.1}, 'Normal ω, σ=0.1'),
        ('zero', {}, 'ω=0 (identical)'),
    ]
    results = []
    t0 = time.time()
    for dist_name, params, label in configs:
        Kcs = []
        for N in Ns:
            Kc, meanR = find_Kc(N, dist_name, params, K0_grid, alpha, sigma, seeds=seeds)
            Kcs.append(Kc)
            results.append({'dist':label,'N':int(N),'Kc':float(Kc) if Kc is not None else None,'meanR_grid':meanR.tolist()})
            print(f"{label:25s} N={N:4d} Kc={Kc}")
        # fit power law for finite Kcs
        mask = np.array([k is not None for k in Kcs])
        if mask.sum()>=3:
            x = Ns[mask].astype(float)
            y = np.array([k for k,m in zip(Kcs,mask) if m])
            logx = np.log(x); logy = np.log(y)
            A = np.vstack([np.ones_like(logx), logx]).T
            c, resid = np.linalg.lstsq(A, logy, rcond=None)[:2]
            beta = c[1]; pref = np.exp(c[0])
            r2 = float(1 - resid[0]/(len(logy)*np.var(logy))) if (isinstance(resid, np.ndarray) and resid.size>0 and len(logy)>2) else None
            results.append({'dist':label,'fit_beta':float(beta),'fit_A':float(pref),'fit_r2':r2})
            print(f"  fit Kc = {pref:.3f} * N^{beta:.3f}  r2={r2}")
    print('elapsed', time.time()-t0)
    # save json
    outdir = '../../shared_agora/artifacts'
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, 'dossier009_protocol_sensitivity_pilot.json'),'w') as f:
        json.dump(results, f, indent=2)
    # figure
    fig, ax = plt.subplots(1,1,figsize=(8,6))
    for dist_name, params, label in configs:
        Kcs = [r['Kc'] for r in results if r.get('dist')==label and 'N' in r]
        ax.plot(Ns, Kcs, marker='o', label=label)
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('N'); ax.set_ylabel(r'$K_c$ (smallest $K_0$ with $\langle R\rangle>0.5$)')
    ax.set_title('Dossier-009 finite-size scaling is strongly distribution-dependent')
    ax.legend()
    ax.grid(True, ls='--', alpha=0.5)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, 'dossier009_protocol_sensitivity_pilot.png'), dpi=150)
    print('saved artifacts')

if __name__ == '__main__':
    main()
