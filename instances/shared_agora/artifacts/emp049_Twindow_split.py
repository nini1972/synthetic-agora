"""Split-run version: python emp049_Twindow_split.py A|B|C|D|E  -> emp049_Tw_<P>.json"""
import numpy as np, json, sys, time

ALPHA, SIGMA = 0.6, 0.008
N, SEEDS = 150, 3
KGRID = np.arange(0.2, 6.41, 0.4)
PROT = {
    "A": (0.0, SIGMA, 500, 1500, 0.1),
    "B": (0.0, SIGMA, 500, 6000, 0.1),
    "C": (0.0, SIGMA, 500, 8000, 0.25),
    "D": (1.0, SIGMA, 500, 1500, 0.1),
    "E": (0.0, 0.0,   500, 1500, 0.1),
}

def main(p):
    ostd, sg, tr, tm, dt = PROT[p]
    rng = np.random.default_rng(20260919)
    nK = len(KGRID)
    th = rng.uniform(0, 2*np.pi, size=(nK, SEEDS, N))
    om = rng.normal(0, ostd, size=(nK, SEEDS, N)) if ostd > 0 else 0.0
    ns, ntrans = int((tr + tm) / dt), int(tr / dt)
    acc = np.zeros((nK, SEEDS))
    scale = sg * np.sqrt(dt)
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
    meanR = acc.mean(axis=1)
    above = np.where(meanR >= 0.5)[0]
    kc = float(KGRID[above[0]]) if len(above) else None
    out = {"omega_std": ostd, "sigma": sg, "TMEAS": tm, "dt": dt, "Kc": kc,
           "meanR": {f"{k:.1f}": round(float(m), 4) for k, m in zip(KGRID, meanR)}}
    with open(f"emp049_Tw_{p}.json", "w") as f:
        json.dump(out, f, indent=1)
    print(p, "Kc=", kc, f"({time.time():.0f})", flush=True)

main(sys.argv[1])
