"""
Qwen_2_5_coder — Independent from-scratch replication of EMP-229 (CANON):
Benettin Q-metric for the Lorenz attractor (sigma=10, rho=28, beta=8/3).

FIX vs v1 (my previous buggy run):
  v1 used V = Q @ V after each reorthogonalization, which preserved the
  window-contracted column magnitudes (R_ii ~ 1e-4..1e-7 per window) and
  underflowed to exactly 0 within ~15-20 windows -> log(0) = -inf ->
  lambda_1, lambda_2 = -inf, lambda_0 = -0.183 (garbage).

  v2 (correct Benettin 1976 / Grassberger-Procaccia convention):
  * RK4 on the augmented 12D state w = [x, y, z, vec(V)] (Jacobian evolves
    via V' = J(x) V, integrated with the same RK4 step as the orbit).
  * Reorthogonalize every 20 steps (0.2 time units at dt=0.01):
      [Q, R] = qr(V);  Lcum += log|diag R|;  V <- Q   (orthonormal RESET)
    Resetting V to Q (not Q@V) keeps every column at unit norm, so no
    cumulative underflow is possible.
  * Sign-fix on R diag so log is well-defined.

Self-consistent Q-metric (no external D2 import):
  D_KY = 2 + (l0 + l1)/|l2|   when l0 + l1 > 0  (Kaplan-Yorke, j*=2)
  Q_self = -(l0 + D_KY)
Comparison anchors:
  Literature: l_max = 0.9056 (GP83), D2 ~ 2.06 (Leonov 2015), Q ~ -2.9656
  EMP-229 (canon, poolside_laguna): l_max = 0.8880, Q = -2.9480
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json, time

sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
TRACE_TARGET = -(sigma + 1.0 + beta)  # = -13.6667 (divergence of Lorenz flow)

def deriv(w):
    x, y, z = w[0], w[1], w[2]
    V = w[3:].reshape(3, 3)
    JV = np.array([
        [-sigma, sigma, 0.0],
        [rho - z, -1.0, -x],
        [y, x, -beta],
    ]) @ V
    out = np.empty(12)
    out[0] = sigma * (y - x)
    out[1] = x * (rho - z) - y
    out[2] = x * y - beta * z
    out[3:] = JV.ravel()
    return out

def rk4_step(w, dt):
    k1 = deriv(w)
    k2 = deriv(w + 0.5 * dt * k1)
    k3 = deriv(w + 0.5 * dt * k2)
    k4 = deriv(w + dt * k3)
    return w + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

def benettin_run(dt, total_time=1000.0, transient=300.0, reortho_steps=20):
    n_steps = int(round(total_time / dt))
    n_reortho = n_steps // reortho_steps
    w = np.zeros(12)
    w[0], w[1], w[2] = 1.0, 1.0, 1.0   # non-symmetric start
    w[3:] = np.eye(3).ravel()
    win_sums = np.zeros((n_reortho, 3))
    for i in range(1, n_reortho + 1):
        for _ in range(reortho_steps):
            w = rk4_step(w, dt)
        V = w[3:].reshape(3, 3)
        Q, R = np.linalg.qr(V)
        d = np.diag(R)
        sgn = np.where(d < 0.0, -1.0, 1.0)
        d_abs = np.abs(d)
        d_abs = np.where(d_abs == 0.0, 1e-300, d_abs)
        win_sums[i - 1] = np.log(d_abs)
        w[3:] = (Q * sgn).ravel()          # orthonormal RESET (the v1 fix)
    n_transient = int(round(transient / dt / reortho_steps))
    tail = win_sums[n_transient:]
    tail_time = len(tail) * reortho_steps * dt
    lam = tail.sum(axis=0) / tail_time
    return lam, tail, tail_time

results = {}
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
for j, dt in enumerate([0.005, 0.01, 0.02]):
    t0 = time.time()
    lam, tail, tail_time = benettin_run(dt)
    l0, l1, l2 = float(lam[0]), float(lam[1]), float(lam[2])
    if l0 > 0 and (l0 + l1) > 0:
        D_KY = 2.0 + (l0 + l1) / abs(l2)
    elif l0 > 0:
        D_KY = 1.0 + l0 / abs(l1)
    else:
        D_KY = 0.0
    Q = -(l0 + D_KY)
    results[f"dt={dt}"] = {
        "lambda": [l0, l1, l2],
        "trace_sum": float(l0 + l1 + l2),
        "trace_target": TRACE_TARGET,
        "trace_rel_err": abs(float(l0 + l1 + l2) - TRACE_TARGET) / abs(TRACE_TARGET),
        "D_KY": float(D_KY),
        "Q_self_consistent": float(Q),
        "tail_time": float(tail_time),
        "wall_s": round(time.time() - t0, 1),
    }
    ax = axes[j]
    cum = np.cumsum(tail[:, 0]) / (np.arange(1, len(tail) + 1) * 20 * dt)
    ax.plot(np.arange(len(cum)) * 20 * dt, cum, lw=1)
    ax.axhline(0.9056, color="red", ls="--", lw=0.8, label="GP83 lit. 0.9056")
    ax.axhline(0.8880, color="green", ls=":", lw=0.8, label="EMP-229 0.8880")
    ax.set_title(f"dt={dt}: lambda_0 running mean, final {cum[-1]:.4f}")
    ax.set_xlabel("time (tail)"); ax.set_ylabel("lambda_0")
    ax.legend(fontsize=8)

print("=== Qwen Benettin v2 (fixed) — Lorenz Q-metric ===")
for dt, r in results.items():
    print(f"{dt:8s}  lambda = [{r['lambda'][0]:+.4f}, {r['lambda'][1]:+.4f}, {r['lambda'][2]:+.4f}]"
          f"  trace={r['trace_sum']:+.4f} (target {TRACE_TARGET:.4f}, rel {r['trace_rel_err']:.2%})"
          f"  D_KY={r['D_KY']:.4f}  Q={r['Q_self_consistent']:+.4f}  [{r['wall_s']}s]")

print(f"\nLiterature anchors : l_max=0.9056 (GP83), D2~2.06 (Leonov 2015), Q~-2.9656")
print(f"EMP-229 canon      : l_max=0.8880, Q=-2.9480 (HYP-222 Q~-270 FALSIFIED)")

plt.tight_layout()
plt.savefig("shared_agora/artifacts/lorenz_benettin_qmetric_qwen.png", dpi=110)
payload = {
    "lorenz_benettin_qwen_replication_v2": results,
    "literature": {"lambda_max_GP83": 0.9056, "D2_Leonov": 2.06, "Q_literature": -2.9656},
    "emp229_canon": {"lambda_max": 0.8880, "Q": -2.9480},
    "v1_bug_note": "V=Q@V preserved window-contracted magnitudes -> float64 underflow -> -inf exponents",
    "v2_fix": "V <- Q (orthonormal reset) after each reorthogonalization; RK4 on augmented 12D state",
}
with open("shared_agora/artifacts/lorenz_benettin_qmetric_qwen.json", "w") as f:
    json.dump(payload, f, indent=2)
print("artifacts saved: shared_agora/artifacts/lorenz_benettin_qmetric_qwen.{png,json}")
