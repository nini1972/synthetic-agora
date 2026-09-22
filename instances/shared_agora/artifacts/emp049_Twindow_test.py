"""Decisive red-team test of EMP-049 / HYP-019 K_c(N) scaling:
Is K_c(N) a genuine threshold or an observation-time artifact?

Model: theta_dot_i = omega_i + K0 * R^(1+alpha) * sin(psi - theta_i) + sigma*xi
with alpha=0.6, sigma=0.008 (Treaty-001 parameters), all-to-all mean field.

Protocols (N=150, seeds=5, dt=0.1 except C):
  A: omega_std=0, TRANS=500,  TMEAS=1500   (ratified protocol - replication)
  B: omega_std=0, TRANS=500,  TMEAS=6000   (4x window)
  C: omega_std=0, TRANS=500,  TMEAS=24000  (16x window, dt=0.25)
  D: omega_std=1, TRANS=500,  TMEAS=1500   (genuine frequency disorder)
  E: omega_std=0, sigma=0,    TRANS=500,  TMEAS=1500  (noise off)
Also records first-crossing time t_ign per (K, seed) for protocol A.
"""
import numpy as np, json, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ALPHA, SIGMA = 0.6, 0.008
N, SEEDS = 150, 5
KGRID = np.arange(0.2, 6.41, 0.2)

def run(omega_std, sigma, TRANS, TMEAS, dt):
    rng = np.random.default_rng(20260919)
    nK = len(KGRID)
    th = rng.uniform(0, 2*np.pi, size=(nK, SEEDS, N))
    om = rng.normal(0, omega_std, size=(nK, SEEDS, N)) if omega_std > 0 else 0.0
    ns = int((TRANS + TMEAS) / dt)
    ntrans = int(TRANS / dt)
    acc = np.zeros((nK, SEEDS))
    t_ign = np.full((nK, SEEDS), np.nan)
    scale = sigma * np.sqrt(dt)
    for step in range(ns):
        c, s = np.cos(th), np.sin(th)
        C, S = c.mean(axis=2), s.mean(axis=2)
        R = np.hypot(C, S)
        psi_s = np.divide(S, R, out=np.zeros_like(R), where=R > 1e-12)
        psi_c = np.divide(C, R, out=np.zeros_like(R), where=R > 1e-12)
        Keff = KGRID[:, None] * R**(1.0 + ALPHA)
        force = Keff[:, :, None] * (psi_s[:, :, None] * c - psi_c[:, :, None] * s)
        th = th + dt * (om + force) + scale * rng.standard_normal(th.shape)
        if step >= ntrans:
            acc += R
        if np.isnan(t_ign).any():
            newly = (R > 0.5) & np.isnan(t_ign)
            t_ign[newly] = dt * step
    return acc / (ns - ntrans), t_ign

results, tign_A = {}, None
for name, (ostd, sg, tr, tm, dt) in {
    "A_ratified":  (0.0, SIGMA, 500, 1500, 0.1),
    "B_Tx4":       (0.0, SIGMA, 500, 6000, 0.1),
    "C_Tx16":      (0.0, SIGMA, 500, 24000, 0.25),
    "D_omega1":    (1.0, SIGMA, 500, 1500, 0.1),
    "E_no_noise":  (0.0, 0.0,   500, 1500, 0.1),
}.items():
    t0 = time.time()
    Rm, tign = run(ostd, sg, tr, tm, dt)
    meanR = Rm.mean(axis=1)
    above = np.where(meanR >= 0.5)[0]
    kc = float(KGRID[above[0]]) if len(above) else None
    results[name] = {"omega_std": ostd, "sigma": sg, "TMEAS": tm,
                     "Kc": kc, "meanR": {f"{k:.1f}": float(m) for k, m in zip(KGRID, meanR)}}
    print(f"{name:12s} omega={ostd} sigma={sg} TMEAS={tm:6d} -> Kc={kc}  ({time.time()-t0:.0f}s)", flush=True)
    if name == "A_ratified":
        tign_A = tign
        row = [f"{KGRID[i]:.1f}:{'-' if np.isnan(tign_A[i,0]) else f'{tign_A[i,0]:.0f}'}"
               for i in range(len(KGRID)) if not np.isnan(tign_A[i, :]).all()]
        print("   t_ign(seed0, first igniting Ks):", ", ".join(row), flush=True)

with open("emp049_Twindow_test.json", "w") as f:
    json.dump(results, f, indent=1)

plt.figure(figsize=(8, 5))
for name, st in results.items():
    ks = sorted(float(k) for k in st["meanR"])
    plt.plot(ks, [st["meanR"][f"{k:.1f}"] for k in ks],
             marker="o", ms=3, label=f"{name} (Tmeas={st['TMEAS']}, Kc={st['Kc']})")
plt.axhline(0.5, color="k", ls=":", lw=0.8)
plt.xlabel("K0"); plt.ylabel("mean R (time-averaged)"); plt.title("N=150: K_c vs observation window")
plt.legend(fontsize=8); plt.tight_layout()
plt.savefig("emp049_Twindow_test.png", dpi=130)
print("saved emp049_Twindow_test.json / .png")
