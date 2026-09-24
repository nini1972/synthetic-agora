"""Protocol D (omega_std=1) N-scan to test whether the ratified EMP-049/HYP-019
K_c(N) archive values (1.004@N=20, 2.58@N=80, 3.2@N=600) are reproduced when
genuine frequency disorder is present (vs the documented identical-oscillator model).

Usage: python emp049_D_Nscan.py <N>
Estimator matches ratified protocol: K_c = smallest K0 with final time-averaged R > 0.5.
(Treaty-001 params otherwise: alpha=0.6, sigma=0.008, TRANS=500, TMEAS=1500.)
"""
import numpy as np, json, sys, time

ALPHA, SIGMA = 0.6, 0.008
TRANS, TMEAS = 500.0, 1500.0
OSTD = 1.0

CFG = {20:  dict(seeds=4, dt=0.10, kstep=0.2),
       80:  dict(seeds=3, dt=0.10, kstep=0.2),
       600: dict(seeds=2, dt=0.25, kstep=0.5)}

def main(N):
    cfg = CFG[N]
    dt, seeds, kstep = cfg["dt"], cfg["seeds"], cfg["kstep"]
    KGRID = np.arange(0.2, 6.41, kstep)
    rng = np.random.default_rng(777 + N)
    nK = len(KGRID)
    th = rng.uniform(0, 2*np.pi, size=(nK, seeds, N))
    om = rng.normal(0, OSTD, size=(nK, seeds, N))
    ns, ntrans = int((TRANS + TMEAS) / dt), int(TRANS / dt)
    acc = np.zeros((nK, seeds))
    scale = SIGMA * np.sqrt(dt)
    for step in range(ns):
        c, s = np.cos(th), np.sin(th)
        C, S = c.mean(axis=2), s.mean(axis=2)
        R = np.hypot(C, S)
        ps = np.divide(S, R, out=np.zeros_like(R), where=R > 1e-12)
        pc = np.divide(C, R, out=np.zeros_like(R), where=R > 1e-12)
        Keff = KGRID[:, None] * R**(1.0 + ALPHA)
        force = Keff[:, :, None] * (ps[:, :, None] * c - pc[:, :, None] * s)
        th = th + dt * (om + force) + scale * rng.standard_normal(th.shape)
        if step >= ntrans:
            acc += R
    meanR = acc / (ns - ntrans)          # proper time average per seed, then:
    meanR = meanR.mean(axis=1)           # over seeds
    above = np.where(meanR >= 0.5)[0]
    kc = float(KGRID[above[0]]) if len(above) else None
    out = {"N": N, "omega_std": OSTD, "sigma": SIGMA, "TMEAS": TMEAS, "dt": dt,
           "Kc": kc, "archive_Kc_ref": {20: 1.004, 80: 2.58, 600: 3.2}.get(N),
           "meanR": {f"{k:.2f}": round(float(m), 4) for k, m in zip(KGRID, meanR)}}
    with open(f"emp049_D_N{N}.json", "w") as f:
        json.dump(out, f, indent=1)
    print(f"N={N} omega=1 -> Kc={kc} (archive ref: {out['archive_Kc_ref']})", flush=True)

main(int(sys.argv[1]))
