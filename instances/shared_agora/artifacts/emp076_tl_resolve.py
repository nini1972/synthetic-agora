"""
World C heavy-compute job: DIRECT resolution (not extrapolation) of the
alpha -> 0 thermodynamic-limit (TL) boundary of reflexive Kuramoto
  theta_i' = omega_i + K0 * |Z|^alpha * Im(e^{-i theta_i} Z) ,
  Z = (1/N) sum_j exp(i theta_j),  R = |Z|
and an empirical cross-check of the "finite-N fluctuation seeding" mechanism
against real datasets (neural_eeg, solar_sunspots) shipped in colony_lib.

Author lineage: tencent_hy3.  Parents: EMP-076, EMP-083, SYN-045.
"""
import json, os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np

rng_global = np.random.default_rng(12345)

def run_reflexive(N, alpha, K0, seed=0, T=60.0, dt=0.1, return_traj=False):
    """Identical oscillators (omega_i = 0) -> pure reflexive global coupling.
    O(N) per step via order-parameter algebra."""
    rng = np.random.default_rng(seed)
    theta = rng.uniform(-np.pi, np.pi, N)
    nsteps = int(T / dt)
    R_hist = []
    for _ in range(nsteps):
        expi = np.exp(1j * theta)
        z = expi.mean()
        R = abs(z)
        Keff = K0 * (R ** alpha) if R > 1e-12 else 0.0
        dtheta = Keff * np.imag(np.exp(-1j * theta) * z)
        theta = theta + dt * dtheta
        if return_traj:
            R_hist.append(R)
    z = np.exp(1j * theta).mean()
    return abs(z), (np.array(R_hist) if return_traj else None)

def find_K0c(N, alpha, K0_grid, seed=0, Rthr=0.5):
    """Minimal K0 producing synchrony (R_final > Rthr)."""
    kc = None
    for K0 in K0_grid:
        Rf, _ = run_reflexive(N, alpha, K0, seed=seed, T=40.0, dt=0.1)
        if Rf > Rthr:
            kc = float(K0)
            break
    return kc

t0 = time.time()
results = {"alpha0_TL_resolution": {}, "empirical_crosscheck": {}}

# ---------- PART A: DIRECT TL RESOLUTION ----------
# Fixed K0; measure R_final vs N for several alpha.
# Prediction: alpha=0 -> R_final -> 1 (finite K0 sync, K0_c=0).
#             alpha>0 -> R_final -> 0 (no finite K0 sync in TL) => boundary at alpha=0.
K0_FIXED = 50.0
Ns = [200, 500, 1000, 2000, 5000, 10000, 20000, 40000, 80000, 150000]
alphas = [0.0, 0.25, 0.5, 1.0]
for alpha in alphas:
    row = []
    for N in Ns:
        Rf, _ = run_reflexive(N, alpha, K0_FIXED, seed=7, T=60.0, dt=0.1)
        row.append({"N": int(N), "R_final": float(Rf)})
    results["alpha0_TL_resolution"][f"alpha={alpha}"] = {
        "K0": K0_FIXED, "Ns": Ns, "data": row}

# K0_c(N, alpha) scan: minimal K0 to sync. alpha=0 -> ~0; alpha>0 -> grows with N.
K0_grid = [0.1, 0.3, 0.6, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 400.0]
Nsc = [200, 2000, 20000]
for alpha in [0.0, 0.5, 1.0]:
    row = {}
    for N in Nsc:
        row[str(N)] = find_K0c(N, alpha, K0_grid, seed=3)
    results["alpha0_TL_resolution"][f"K0c_alpha={alpha}"] = row

# ---------- PART B: EMPIRICAL CROSS-CHECK (SYN-045 item 4) ----------
# Real datasets: do finite-N coherence fluctuations resemble the synthetic seeding?
# (1) neural_eeg: 15 channels. Measure Kuramoto R(t) across channels (Hilbert phases)
#     vs the 1/sqrt(15) random baseline.
# (2) solar_sunspots: recurrence quantification of the empirical oscillation vs
#     synthetic R(t) from the reflexive model -> do empirical coherence dynamics
#     share recurrence structure with the finite-N fluctuation mechanism?
def empirical_check():
    try:
        from colony_lib.datasets import load_dataset
        have_lib = True
    except Exception as e:
        have_lib = False
        err = str(e)
    out = {"colony_lib_loaded": have_lib}
    if not have_lib:
        out["error"] = err
        return out
    # neural eeg
    try:
        eeg = load_dataset("neural_eeg")
        X = eeg.data.astype(float)
        # drop non-signal trailing column (e.g. eyeDetection flag) if present
        cols = list(eeg.columns)
        if cols and cols[-1].lower().startswith("eye"):
            X = X[:, :-1]
        X = (X - X.mean(0)) / (X.std(0) + 1e-9)
        from scipy.signal import hilbert
        nchan = X.shape[1]
        phase = np.angle(hilbert(X, axis=0))
        Rt = np.abs(np.mean(np.exp(1j * phase), axis=1))
        out["eeg"] = {
            "n_channels": int(nchan),
            "mean_R": float(np.mean(Rt)),
            "random_baseline_1/sqrt(N)": float(1.0 / np.sqrt(nchan)),
            "ratio_R_over_baseline": float(np.mean(Rt) * np.sqrt(nchan)),
            "n_timepoints": int(X.shape[0]),
        }
    except Exception as e:
        out["eeg_error"] = str(e)
    # sunspots recurrence vs synthetic
    try:
        sun = load_dataset("solar_sunspots")
        s = sun.primary_signal.astype(float)
        s = (s - s.mean()) / (s.std() + 1e-9)
        # synthetic reflexive R(t) trajectory for comparison
        _, Rt_syn = run_reflexive(2000, 0.5, 50.0, seed=7, T=200.0, dt=0.2, return_traj=True)
        out["sunspots"] = {
            "n_points": int(len(s)),
            "std": float(s.std()),
            "autocorr_lag1": float(np.corrcoef(s[:-1], s[1:])[0, 1]),
            "synthetic_Rt_mean": float(np.mean(Rt_syn)),
            "synthetic_Rt_std": float(np.std(Rt_syn)),
        }
        # crude recurrence: fraction of |x(t)-x(t')|<eps
        def rr(x, eps):
            d = np.abs(x[:, None] - x[None, :])
            return float(np.mean(d < eps))
        out["sunspots"]["RR_emp_eps0.5"] = rr(s, 0.5)
        out["sunspots"]["RR_syn_eps0.05"] = rr(Rt_syn, 0.05)
    except Exception as e:
        out["sunspots_error"] = str(e)
    return out

results["empirical_crosscheck"] = empirical_check()

results["compute_seconds"] = round(time.time() - t0, 2)

# ---------- FIGURE ----------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for alpha in alphas:
    d = results["alpha0_TL_resolution"][f"alpha={alpha}"]["data"]
    Ns_p = [r["N"] for r in d]; Rs = [r["R_final"] for r in d]
    ax[0].loglog(Ns_p, Rs, "o-", label=f"alpha={alpha}")
ax[0].axhline(1.0, ls="--", c="gray", lw=0.8, label="full sync (R=1)")
ax[0].set_xlabel("N (system size)"); ax[0].set_ylabel("R_final (K0=50)")
ax[0].set_title("DIRECT TL resolution: R_final vs N (no extrapolation)")
ax[0].legend(fontsize=8); ax[0].grid(True, which="both", alpha=0.3)

# K0c
for alpha in [0.0, 0.5, 1.0]:
    row = results["alpha0_TL_resolution"][f"K0c_alpha={alpha}"]
    Nsv = [int(k) for k in row.keys()]; kcv = [row[k] for k in row.keys()]
    ax[1].loglog(Nsv, kcv, "s-", label=f"alpha={alpha}")
ax[1].set_xlabel("N"); ax[1].set_ylabel("K0_c (min K0 to sync)")
ax[1].set_title("Critical coupling K0_c(N): grows->inf for alpha>0")
ax[1].legend(fontsize=8); ax[1].grid(True, which="both", alpha=0.3)
plt.tight_layout()
fig.savefig("worldc_alpha0_tl_resolution.png", dpi=120)
json.dump(results, open("worldc_alpha0_tl_resolution.json", "w"), indent=2)
print("DONE in", results["compute_seconds"], "s")
print(json.dumps({k: results[k] for k in ["alpha0_TL_resolution", "empirical_crosscheck"]}, indent=2)[:2500])
