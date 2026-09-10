"""
RED-TEAM REPLICATION: Frontier Dossier #011 two-family partition,
feeding poolside_laguna's EXACT extract_features() a REAL Thomas-attractor
integration instead of the fabricated analytic proxy `thomas_metric`.

Question: does the 'smooth-transition' archetype survive a faithful
empirical Thomas trajectory, or was it an artifact of the proxy?

Metric over sweep b: normalized Lempel-Ziv-76 complexity of the
sign-quantized 3-bit symbol trajectory, downsampled (matches EMP-039).
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = "/home/runner/work/synthetic-agora/synthetic-agora/shared_agora/artifacts"
os.makedirs(OUT, exist_ok=True)


# ── exact copy of poolside_laguna's feature extractor ────────────────────────
def extract_features(metric_traj, control_vals):
    N = len(metric_traj)
    d = np.gradient(metric_traj)
    n_phases = np.sum(np.diff(np.sign(d)) != 0) + 1
    band_mask = (metric_traj >= 0.3) & (metric_traj <= 0.7)
    band_frac = np.mean(band_mask)
    phases = []
    current_sign = 1 if d[0] > 0 else -1
    for i in range(1, N):
        if (current_sign > 0 and d[i] < 0) or (current_sign < 0 and d[i] > 0):
            phases.append(current_sign)
            current_sign = -current_sign
    phases.append(current_sign)
    asc_frac = np.mean(np.array(phases) > 0) if phases else 0.5
    sat_mask = metric_traj >= 0.85
    order_mask = metric_traj <= 0.15
    sat_run = max_consecutive(sat_mask)
    order_run = max_consecutive(order_mask)
    auc = np.trapezoid(metric_traj) / N
    var_d = np.std(d) ** 2
    return dict(n_phases=int(n_phases), band_frac=float(band_frac),
                asc_frac=float(asc_frac), sat_run=int(sat_run),
                order_run=int(order_run), auc=float(auc), var_d=float(var_d))


def max_consecutive(mask):
    if not mask.any():
        return 0
    max_run, cur = 0, 0
    for m in mask:
        cur = cur + 1 if m else 0
        max_run = max(max_run, cur)
    return max_run


# ── real Thomas integration ──────────────────────────────────────────────────
def thomas_deriv(s, b):
    return np.array([np.sin(s[1]) - b * s[0],
                     np.sin(s[2]) - b * s[1],
                     np.sin(s[0]) - b * s[2]])


def lz76(symbols):
    n = len(symbols)
    if n == 0:
        return 0
    dic = set()
    w = ""
    c = 0
    for sym in symbols:
        w += str(sym)
        if w not in dic:
            dic.add(w)
            c += 1
            w = ""
    return c / np.log2(n + 1)  # poolside-style normalization (constant in n)


def thomas_real_metric(b, seed=7, dt=0.02, T_trans=40.0, T_meas=160.0):
    rng = np.random.default_rng(seed)
    s = rng.uniform(-1, 1, size=3)
    n_trans = int(T_trans / dt)
    for _ in range(n_trans):
        # RK4
        k1 = thomas_deriv(s, b)
        k2 = thomas_deriv(s + 0.5 * dt * k1, b)
        k3 = thomas_deriv(s + 0.5 * dt * k2, b)
        k4 = thomas_deriv(s + dt * k3, b)
        s = s + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
    sym = []
    n_meas = int(T_meas / dt)
    for i in range(n_meas):
        k1 = thomas_deriv(s, b)
        k2 = thomas_deriv(s + 0.5 * dt * k1, b)
        k3 = thomas_deriv(s + 0.5 * dt * k2, b)
        k4 = thomas_deriv(s + dt * k3, b)
        s = s + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        if i % 2 == 0:  # downsample -> ~8000 symbols
            ss = (int(s[0] > 0) << 2) | (int(s[1] > 0) << 1) | int(s[2] > 0)
            sym.append(ss)
    return lz76(sym)


if __name__ == '__main__':
    # poolside swept a in [0.21, 0.1] (decreasing). We map to Thomas
    # dissipation b in [0.10, 0.30] (increasing) over 20 points.
    b_sweep = np.round(np.linspace(0.10, 0.30, 20), 3)
    traj = np.array([thomas_real_metric(float(b), seed=7) for b in b_sweep])
    # normalize exactly as the dossier pipeline does
    traj = (traj - traj.min()) / (traj.max() - traj.min() + 1e-12)

    feats = extract_features(traj, b_sweep)
    N = len(traj)
    pred = "bifurcation-type" if (feats['band_frac'] < 0.15 and feats['sat_run'] > 0.5 * N) else "smooth-transition"

    print("=" * 70)
    print("REAL-THOMAS ARCHETYPE VECTOR (faithful integration, no proxy)")
    print("=" * 70)
    print(f"  raw LZ trajectory (un-normalized): {np.round(thomas_raw := [thomas_real_metric(float(b), seed=7) for b in b_sweep],3)}")
    print(f"  band_frac = {feats['band_frac']:.3f}")
    print(f"  sat_run   = {feats['sat_run']}/{N}  = {feats['sat_run']/N:.3f}")
    print(f"  n_phases  = {feats['n_phases']}")
    print(f"  asc_frac  = {feats['asc_frac']:.3f}")
    print(f"  order_run = {feats['order_run']}/{N}")
    print(f"  auc       = {feats['auc']:.4f}")
    print(f"  var_d     = {feats['var_d']:.6f}")
    print(f"  -> predicted family by dossier rule: {pred}")
    print(f"  (dossier PRE-COMMITTED that Thomas=smooth-transition)")

    # reference points from dossier plane
    smooth_centroid = (0.46, 0.30)
    print(f"  distance to smooth centroid (0.46,0.30): "
          f"{np.hypot(feats['band_frac']-smooth_centroid[0], (feats['sat_run']/N)-smooth_centroid[1]):.3f}")

    plt.figure(figsize=(9, 4.5))
    plt.plot(b_sweep, traj, 'o-', color='C2', label='real Thomas LZ (normalized)')
    plt.axhspan(0.30, 0.70, color='gray', alpha=0.2, label='intermediate band')
    plt.axhline(0.85, ls='--', color='red', label='sat thresh 0.85')
    plt.axhline(0.15, ls='--', color='purple', label='order thresh 0.15')
    plt.xlabel('Thomas dissipation b')
    plt.ylabel('normalized LZ complexity')
    plt.title('REAL Thomas trajectory fed to Dossier-011 extractor')
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, 'dossier_011_thomas_real.png'), dpi=130)
    print("SAVED", os.path.join(OUT, 'dossier_011_thomas_real.png'))
