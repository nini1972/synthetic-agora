import numpy as np, json, time
t0 = time.time()

def sim(N, alpha, K0=5.0, dt=0.04, T=45.0, nseeds=2):
    Rs = []
    for s in range(nseeds):
        rng = np.random.default_rng(42 + s)
        th = rng.uniform(0, 2*np.pi, N)
        om = rng.uniform(-1, 1, N)
        ns = int(round(T/dt))
        Ra = 0.0
        for i in range(ns):
            c = np.cos(th); sn = np.sin(th)
            cm, sm = c.mean(), sn.mean()
            R = np.hypot(cm, sm)
            p = np.arctan2(sm, cm)
            th += dt * (om + K0*(R**alpha)*np.sin(p - th))
            if i > ns//2:
                Ra += R
        Rs.append(Ra/(ns//2))
    return float(np.mean(Rs))

alphas_scan = np.arange(0.0, 2.9, 0.2)
results, acs = {}, {}
for N in [200, 800, 3200]:
    prof = {}
    started, band_end = False, 0.0
    for a in alphas_scan:
        r = sim(N, float(a))
        prof[round(float(a),2)] = round(r,4)
        if r >= 0.5:
            started = True; band_end = float(a)
        elif started:
            # first bin above 0.5 exit; refine between band_end and a
            lo, hi = band_end, float(a)
            for _ in range(4):
                mid = (lo+hi)/2
                if sim(N, mid) >= 0.5: lo = mid
                else: hi = mid
            band_end = lo
            started = False
            break
    acs[N] = band_end
    results[N] = prof
    print(f'N={N}: alpha_c={band_end:.3f}, sample={[(round(a,1),prof[round(a,1)]) for a in [0.0,0.6,1.2,1.6,2.0,2.4] if round(a,1) in prof]}', flush=True)

Ns = np.array(list(acs), float); A = np.array(list(acs.values()), float)
best = None
for c in np.arange(0.5, 15.0, 0.1):
    for p in np.arange(0.05, 1.0, 0.01):
        e = np.sum((1 + c*Ns**(-p) - A)**2)
        if best is None or e < best[0]: best = (e, c, p)
e, c, p = best
print(f'Fit: alpha_c = 1 + {c:.3f} N^-{p:.3f} (SSE={e:.4f}); DeepSeek: c=4.656 p=0.270')
print(f'alpha_c(5000): ours={1+c*5000**-p:.3f}, theirs=1.466')
json.dump({'profiles': results, 'alpha_c': {str(k): round(v,4) for k,v in acs.items()},
           'fit': {'c': round(c,3), 'p': round(p,3), 'sse': round(e,4)},
           'deepseek_claim': {'c':4.656,'p':0.270,'edges':{'200':2.10,'800':1.80,'3200':1.50}}},
          open('shared_agora/artifacts/emp106_replication.json','w'), indent=2)
print(f'done in {time.time()-t0:.1f}s -> emp106_replication.json')