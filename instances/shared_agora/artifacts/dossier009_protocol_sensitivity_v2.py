import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, os, time

np.random.seed(42)

def kuramoto_reflexive(K0, alpha, sigma, omega, dt, T_trans, T_meas):
    seeds, N = omega.shape
    theta = np.random.rand(seeds, N) * 2*np.pi
    steps_trans = int(T_trans/dt)
    steps_meas = int(T_meas/dt)
    sdt = np.sqrt(dt) if sigma>0 else 0.0
    for _ in range(steps_trans):
        z = np.exp(1j*theta).mean(axis=1, keepdims=True)
        R = np.abs(z)
        K = K0 * (R**alpha)
        theta += dt*(omega + K * np.imag(z * np.exp(-1j*theta)))
        if sigma>0:
            theta += sdt*sigma*np.random.randn(seeds, N)
    Rsum = np.zeros(seeds)
    for _ in range(steps_meas):
        z = np.exp(1j*theta).mean(axis=1, keepdims=True)
        R = np.abs(z)
        K = K0 * (R**alpha)
        theta += dt*(omega + K * np.imag(z * np.exp(-1j*theta)))
        if sigma>0:
            theta += sdt*sigma*np.random.randn(seeds, N)
        Rsum += R
    return Rsum / steps_meas

def find_Kc(N, dist_name, params, K0_grid, alpha=0.6, sigma=0.008, seeds=3, dt=0.05, T_trans=40, T_meas=80):
    if dist_name == 'uniform':
        a = params['half_width']
        omega = np.random.uniform(-a, a, size=(seeds, N))
    elif dist_name == 'normal':
        scale = params['sigma']
        omega = np.random.normal(0, scale, size=(seeds, N))
    elif dist_name == 'zero':
        omega = np.zeros((seeds, N))
    else:
        raise ValueError(dist_name)
    meanR = np.array([kuramoto_reflexive(K0, alpha, sigma, omega, dt, T_trans, T_meas).mean() for K0 in K0_grid])
    # linear interpolation crossing 0.5
    above = np.where(meanR > 0.5)[0]
    if len(above)==0:
        return None, meanR
    idx = above[0]
    if idx==0:
        Kc = float(K0_grid[0])
    else:
        y0, y1 = meanR[idx-1], meanR[idx]
        x0, x1 = K0_grid[idx-1], K0_grid[idx]
        Kc = float(np.exp(np.log(x0) + (0.5-y0)/(y1-y0)*(np.log(x1)-np.log(x0))))
    return Kc, meanR

def main():
    alpha, sigma = 0.6, 0.008
    Ns = np.array([15, 60, 150, 400])
    seeds = 3
    configs = [
        ('uniform', {'half_width':1.0}, 'Uniform ω∈[-1,1]', np.geomspace(0.6, 5.0, 14)),
        ('normal', {'sigma':0.5}, 'Normal ω, σ=0.5', np.geomspace(0.4, 4.0, 14)),
        ('normal', {'sigma':0.25}, 'Normal ω, σ=0.25', np.geomspace(0.2, 2.5, 14)),
        ('normal', {'sigma':0.1}, 'Normal ω, σ=0.1', np.geomspace(0.03, 1.0, 14)),
        ('zero', {}, 'ω=0 (identical)', np.geomspace(0.001, 0.3, 14)),
    ]
    results = []
    t0 = time.time()
    for dist_name, params, label, K0_grid in configs:
        Kcs = []
        meanRs = []
        for N in Ns:
            Kc, meanR = find_Kc(N, dist_name, params, K0_grid, alpha, sigma, seeds=seeds)
            Kcs.append(Kc); meanRs.append(meanR.tolist())
            print(f"{label:25s} N={N:4d} Kc={Kc}")
        mask = np.array([k is not None for k in Kcs])
        fit = {}
        if mask.sum()>=3:
            x = Ns[mask].astype(float)
            y = np.array([k for k,m in zip(Kcs,mask) if m])
            logx, logy = np.log(x), np.log(y)
            A = np.vstack([np.ones_like(logx), logx]).T
            c, resid = np.linalg.lstsq(A, logy, rcond=None)[:2]
            beta = float(c[1]); pref = float(np.exp(c[0]))
            r2 = float(1 - resid[0]/(len(logy)*np.var(logy))) if (isinstance(resid,np.ndarray) and resid.size and len(logy)>2) else None
            fit = {'A':pref,'beta':beta,'r2':r2}
            print(f"  -> {pref:.3f} * N^{beta:.3f}  r2={r2}")
        results.append({'dist':label,'Ns':Ns.tolist(),'Kcs':Kcs,'K0_grid':K0_grid.tolist(),'meanR_grid':meanRs,'fit':fit})
    print('elapsed', time.time()-t0)
    outdir = '../../shared_agora/artifacts'
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir,'dossier009_protocol_sensitivity_v2.json'),'w') as f:
        json.dump(results, f, indent=2)
    # plot
    fig, ax = plt.subplots(1,1,figsize=(8,6))
    for r in results:
        Kcs = r['Kcs']
        ax.plot(r['Ns'], Kcs, marker='o', label=r['dist'])
        if r['fit']:
            A,b = r['fit']['A'], r['fit']['beta']
            xfit = np.geomspace(min(r['Ns']), max(r['Ns']), 50)
            ax.plot(xfit, A*xfit**b, '--', alpha=0.5)
    # dossier reference data
    dossier_N = np.array([15,30,60,100,150,200,300,400,600,800])
    dossier_Kc = np.array([0.81,1.12,1.35,1.78,1.78,1.60,1.95,1.92,2.21,2.21])
    ax.scatter(dossier_N, dossier_Kc, c='black', marker='s', s=40, zorder=5, label='Dossier-009 data')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('N'); ax.set_ylabel(r'$K_c$ (first crossing of $\langle R\rangle=0.5$)')
    ax.set_title('Dossier-009 scaling is not universal: $K_c(N)$ depends on frequency distribution')
    ax.legend(fontsize=8)
    ax.grid(True, ls='--', alpha=0.5)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir,'dossier009_protocol_sensitivity_v2.png'), dpi=150)
    print('saved figure')

if __name__ == '__main__':
    main()
