"""
EMP/CRT-030 artifact: Instrument calibration of
colony_lib.bifurcation_cartography.extract_critical_exponent.

Three independent diagnostics, all reproducible without any external data:

 (A) GROUND-TRUTH CALIBRATION. Feed synthetic series r=(mu-mu_c)^beta_true with a
     KNOWN beta_true, read back the estimator's beta. Reveals a hard clip floor.

 (B) NOISE NULL. Feed pure white noise (no transition at all) and record the
     distribution of returned beta. If the modal value is 0.05, then "beta~0.05"
     carries zero evidential weight.

 (C) ZERO-OBSERVABLE SCAN. Run the DOSSIER-173 Lenia configuration and confirm
     mean state == 0 across the whole scan yet the estimator still fires.

Outputs: emp140_estimator_calibration.json + .png
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from colony_lib.bifurcation_cartography import extract_critical_exponent

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "emp140_estimator_calibration")
rng = np.random.default_rng(12345)


def call_est(K, r, window=5):
    res = extract_critical_exponent(np.asarray(K), np.asarray(r), window=window)
    try:
        beta = float(res[0])
        kc = float(res[1])
    except Exception:
        beta = float(res.beta)
        kc = float(getattr(res, "k_critical", np.nan))
    return beta, kc


# ---------------------------------------------------------------- (A) calibration
MU = np.linspace(0.10, 0.25, 61)
MU_C = 0.155


def synth(beta_true, mu_c=MU_C, noise=1e-4, seed=0):
    g = np.random.default_rng(seed)
    r = np.where(MU > mu_c, (MU - mu_c) ** beta_true, 0.0)
    r = r + noise * g.standard_normal(MU.size)
    return np.maximum(r, 0.0)


beta_grid = [0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.50, 0.70, 1.00]
calib = []
for bt in beta_grid:
    ests = [call_est(MU, synth(bt, seed=s))[0] for s in range(20)]
    calib.append(dict(beta_true=bt, beta_est_mean=float(np.mean(ests)),
                      beta_est_std=float(np.std(ests)), beta_est_min=float(np.min(ests))))
    print(f"beta_true={bt:5.2f} -> est={np.mean(ests):.6f} +/- {np.std(ests):.6f}")

clip_floor = min(c["beta_est_min"] for c in calib)
at_floor = [c["beta_true"] for c in calib if abs(c["beta_est_mean"] - 0.05) < 1e-6]
print("clip floor (min returned):", clip_floor, " saturated at:", at_floor)

# ---------------------------------------------------------------- (B) noise null
N_MU = 40
K_null = np.linspace(0.12, 0.19, N_MU)
null_betas = []
for _ in range(200):
    r = 0.25 + 0.01 * rng.standard_normal(N_MU)
    b, _ = call_est(K_null, r)
    null_betas.append(b)
null_betas = np.asarray(null_betas)
frac_005 = float(np.mean(np.isclose(null_betas, 0.05)))
print(f"NOISE NULL: frac(beta==0.05)={frac_005:.3f}  mean={null_betas.mean():.5f} "
      f" median={np.median(null_betas):.5f} min={null_betas.min():.5f}")

# ---------------------------------------------------------------- (C) zero observable
try:
    from colony_lib.dynamics import Lenia2D
    mu_scan = np.linspace(0.12, 0.19, 25)
    means = []
    for mu in mu_scan:
        L = Lenia2D(grid_size=64, R=15, sigma=0.05, mu=float(mu), dt=0.1)
        for _ in range(200):
            L.step()
        means.append(float(np.clip(L.state, 0, 1).mean()))
    means = np.asarray(means)
    beta_zero, _ = call_est(mu_scan, means)
    print(f"ZERO-INIT SCAN: max mean state={means.max():.3e}  -> est beta={beta_zero:.6f}")
    zero_ok = True
except Exception as e:  # pragma: no cover
    print("Lenia2D unavailable/failed:", repr(e))
    means = np.zeros_like(mu_scan) if 'mu_scan' in dir() else None
    beta_zero, zero_ok = float("nan"), False
    mu_scan = np.linspace(0.12, 0.19, 25)

# ---------------------------------------------------------------- report
result = dict(
    clip_floor=clip_floor,
    saturated_true_betas=at_floor,
    calibration=calib,
    noise_null=dict(frac_at_005=frac_005, mean=float(null_betas.mean()),
                    median=float(np.median(null_betas)), std=float(null_betas.std())),
    zero_scan=dict(max_mean_state=float(np.max(means)) if means is not None else None,
                   beta_est=beta_zero, ran_ok=zero_ok),
)
with open(OUT + ".json", "w") as f:
    json.dump(result, f, indent=2)

fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
ax[0].plot([c["beta_true"] for c in calib], [c["beta_est_mean"] for c in calib],
           "o-", color="crimson", label="estimator")
ax[0].plot([0.02, 1.0], [0.02, 1.0], "k--", lw=1, label="identity")
ax[0].axhline(0.05, color="navy", ls=":", label="clip floor = 0.05")
ax[0].set_xlabel("beta_true (ground truth)"); ax[0].set_ylabel("beta_est")
ax[0].set_title("(A) Ground-truth calibration:\nhard clip floor at 0.05"); ax[0].legend()

ax[1].hist(null_betas, bins=25, color="steelblue")
ax[1].axvline(0.05, color="navy", ls=":", label=f"0.05 used in {frac_005*100:.0f}%")
ax[1].set_xlabel("beta_est on PURE NOISE"); ax[1].set_ylabel("count")
ax[1].set_title("(B) Noise null (transition-free):\nmode IS 0.05"); ax[1].legend()

ax[2].plot(mu_scan, means, "o-", color="darkgreen")
ax[2].set_xlabel("mu"); ax[2].set_ylabel("mean state (200 steps, zero init)")
ax[2].set_title(f"(C) DOSSIER-173 protocol:\nobservable==0 everywhere, est beta={beta_zero:.4f}")

plt.tight_layout()
plt.savefig(OUT + ".png", dpi=130)
print("saved", OUT + ".json / .png")
