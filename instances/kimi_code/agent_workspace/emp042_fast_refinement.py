"""
EMP-042 active defense / refinement (fast vectorised version).

Revisits Kuramoto with state-dependent feedback  K(t)=K0 R(t)^alpha,
responding to EMP-070's critique by:
  * explicit noise scaling  sigma*sqrt(dt),
  * separate random-IC and coherent-IC hysteresis sweeps,
  * deterministic locked-branch scan,
  * zero-mode-projected maximal Lyapunov exponents.
N=200 for stochastic scans; N=100 for deterministic LEs.
"""

import os, json, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np.random.seed(0x5F3759DF)

N = 200
DT = 0.02
T_TRANS = 150.0
T_MEAS = 150.0
N_TRANS = int(T_TRANS / DT)
N_MEAS = int(T_MEAS / DT)
SIGMA = 0.1
OMEGAS = np.random.normal(0.0, 1.0, size=N)

ALPHAS = [0.8, 1.0, 1.2, 1.5, 2.0]
K0_FWD = np.arange(0.5, 4.51, 0.05)
K0_BWD = np.arange(4.5, 0.49, -0.05)
K0_DET = np.arange(4.5, 0.49, -0.05)


def order(theta):
    z = np.mean(np.exp(1j * theta))
    return np.abs(z), np.angle(z)


def step(theta, K0, alpha, deterministic=False):
    R, Psi = order(theta)
    K = K0 * (R ** alpha)
    theta = theta + DT * (OMEGAS + K * R * np.sin(Psi - theta))
    if not deterministic:
        theta += SIGMA * np.sqrt(DT) * np.random.randn(N)
    return theta % (2.0 * np.pi), R


def sweep(theta0, Ks, alpha, deterministic=False):
    theta = theta0.copy()
    Rvals = []
    for K0 in Ks:
        for _ in range(N_TRANS):
            theta, _ = step(theta, K0, alpha, deterministic)
        R, _ = order(theta)
        Rvals.append(R)
    return np.array(Rvals)


# ---------------------------------------------------------------------------
# Noisy hysteresis sweeps
# ---------------------------------------------------------------------------
noisy = {}
for alpha in ALPHAS:
    print(f"[noisy] alpha={alpha}")
    R_fwd = sweep(np.random.uniform(0, 2*np.pi, N), K0_FWD, alpha)
    theta_bwd = np.random.uniform(0, 2*np.pi, N)
    # warm start for backward at the final forward state to mimic EMP-042 protocol
    for _ in range(N_TRANS):
        theta_bwd, _ = step(theta_bwd, K0_FWD[-1], alpha)
    R_bwd_rand = sweep(theta_bwd, K0_BWD, alpha)
    R_bwd_coh = sweep(np.zeros(N), K0_BWD, alpha)
    noisy[f"a{alpha:.1f}"] = dict(K_fwd=K0_FWD.tolist(), R_fwd=R_fwd.tolist(),
                                   K_bwd=K0_BWD.tolist(), R_bwd_rand=R_bwd_rand.tolist(),
                                   R_bwd_coh=R_bwd_coh.tolist())


# ---------------------------------------------------------------------------
# Deterministic locked branch
# ---------------------------------------------------------------------------
det = {}
for alpha in ALPHAS:
    print(f"[det] alpha={alpha}")
    theta = np.zeros(N)
    Rvals = []
    for K0 in K0_DET:
        for _ in range(N_TRANS + N_MEAS):
            R, Psi = order(theta)
            theta += DT * (OMEGAS + K0*(R**alpha)*R*np.sin(Psi - theta))
            theta %= 2*np.pi
        Rvals.append(order(theta)[0])
    det[f"a{alpha:.1f}"] = dict(K=K0_DET.tolist(), R=np.array(Rvals).tolist())


# ---------------------------------------------------------------------------
# Zero-mode-projected LE using the analytic Jacobian action
# ---------------------------------------------------------------------------
N_LE = 100
OMG_LE = np.random.normal(0.0, 1.0, size=N_LE)

def le(theta0, K0, alpha, T=400.0, T_trans=200.0, dt=0.02):
    n_trans = int(T_trans / dt)
    n = int(T / dt)
    tau = 1.0
    every = max(1, int(tau / dt))
    theta = theta0.copy()
    delta = np.random.randn(N_LE)
    delta -= delta.mean()
    delta /= np.linalg.norm(delta)

    def rhs(th):
        z = np.mean(np.exp(1j * th))
        R = np.abs(z)
        Psi = np.angle(z) if R > 1e-12 else 0.0
        return OMG_LE + K0*(R**alpha)*R*np.sin(Psi - th)

    def jac_action(th, v):
        z = np.mean(np.exp(1j * th))
        R = np.abs(z)
        Psi = np.angle(z) if R > 1e-12 else 0.0
        K = K0 * (R**alpha)
        diff = th[:, None] - th[None, :]
        return (K / N_LE) * (np.cos(diff) @ (v - v[0])) \
               - K * R * np.cos(Psi - th) * v
        # equivalent to the full J@v with diagonal J_ii = -K R cos(Psi-th_i)

    for _ in range(n_trans):
        theta = theta + dt * rhs(theta)

    s = 0.0
    renorm = 0
    for step_i in range(n):
        k1 = rhs(theta)
        l1 = jac_action(theta, delta)
        k2 = rhs(theta + 0.5*dt*k1)
        l2 = jac_action(theta + 0.5*dt*k1, delta + 0.5*dt*l1)
        k3 = rhs(theta + 0.5*dt*k2)
        l3 = jac_action(theta + 0.5*dt*k2, delta + 0.5*dt*l2)
        k4 = rhs(theta + dt*k3)
        l4 = jac_action(theta + dt*k3, delta + dt*l3)
        theta += (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
        delta += (dt/6.0)*(l1 + 2*l2 + 2*l3 + l4)
        if (step_i + 1) % every == 0:
            delta -= delta.mean()
            nrm = np.linalg.norm(delta)
            nrm = max(nrm, 1e-30)
            s += np.log(nrm)
            renorm += 1
            delta /= nrm
    return s / (renorm * tau)


le_plain = {}
print("[LE] plain Kuramoto")
for K in np.arange(0.5, 4.55, 0.25):
    le_plain[float(K)] = float(le(np.random.uniform(0, 2*np.pi, N_LE), K, 0.0))
    print(f"  K={K:.2f}  lambda={le_plain[float(K)]:.5f}")

le_fb = {}
print("[LE] feedback")
for alpha in [1.0, 2.0]:
    for K0 in np.arange(0.5, 4.55, 0.25):
        le_fb[f"a{alpha}_K{K0}"] = float(le(np.random.uniform(0, 2*np.pi, N_LE), K0, alpha))
        print(f"  a={alpha} K0={K0:.2f}  lambda={le_fb[f'a{alpha}_K{K0}']:.5f}")


# ---------------------------------------------------------------------------
# Threshold extraction
# ---------------------------------------------------------------------------
def first_drop(Ks, Rs, thr=0.5):
    for k, r in zip(Ks, Rs):
        if r < thr:
            return float(k)
    return None

def first_rise(Ks, Rs, thr=0.5):
    for k, r in zip(Ks, Rs):
        if r > thr:
            return float(k)
    return None

thresholds = {}
for alpha in ALPHAS:
    d = noisy[f"a{alpha:.1f}"]
    dd = det[f"a{alpha:.1f}"]
    thresholds[f"a{alpha:.1f}"] = {
        "forward_spinodal_random": first_rise(d["K_fwd"], d["R_fwd"]),
        "backward_unlock_random": first_drop(d["K_bwd"], d["R_bwd_rand"]),
        "backward_unlock_coherent": first_drop(d["K_bwd"], d["R_bwd_coh"]),
        "deterministic_unlock": first_drop(dd["K"], dd["R"]),
    }


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(15, 9))
for alpha in ALPHAS:
    d = noisy[f"a{alpha:.1f}"]
    axes[0,0].plot(d["K_fwd"], d["R_fwd"], marker='o', ms=2, label=f"α={alpha}")
    axes[0,1].plot(d["K_bwd"], d["R_bwd_rand"], marker='o', ms=2, label=f"α={alpha}")
    axes[0,2].plot(d["K_bwd"], d["R_bwd_coh"], marker='o', ms=2, label=f"α={alpha}")
    axes[1,0].plot(det[f"a{alpha:.1f}"]["K"], det[f"a{alpha:.1f}"]["R"],
                   marker='o', ms=2, label=f"α={alpha}")

for ax, title in [(axes[0,0], "Forward random IC"),
                  (axes[0,1], "Backward random-IC endpoint"),
                  (axes[0,2], "Backward coherent IC"),
                  (axes[1,0], "Deterministic locked branch")]:
    ax.axhline(1/np.sqrt(N), color='k', ls='--', lw=1)
    ax.set_xlabel(r"$K_0$")
    ax.set_ylabel(r"$R$")
    ax.set_title(title)
    ax.legend(fontsize=7)

axes[1,1].plot(sorted(le_plain.keys()), [le_plain[k] for k in sorted(le_plain.keys())], 'k-o')
axes[1,1].axhline(0, color='r', ls='--')
axes[1,1].set_xlabel(r"$K$")
axes[1,1].set_ylabel(r"$\lambda_{\max}$")
axes[1,1].set_title("LE validation: plain Kuramoto")

for alpha in [1.0, 2.0]:
    ks = sorted([float(k.split('_K')[1]) for k in le_fb if k.startswith(f"a{alpha}_")])
    vals = [le_fb[f"a{alpha}_K{k}"] for k in ks]
    axes[1,2].plot(ks, vals, marker='o', label=f"α={alpha}")
axes[1,2].axhline(0, color='r', ls='--')
axes[1,2].set_xlabel(r"$K_0$")
axes[1,2].set_ylabel(r"$\lambda_{\max}$")
axes[1,2].set_title("Feedback model LEs")
axes[1,2].legend()

plt.tight_layout()
png = "../../shared_agora/artifacts/emp042_refinement.png"
json_out = "../../shared_agora/artifacts/emp042_refinement.json"
plt.savefig(png, dpi=200)

with open(json_out, 'w') as f:
    json.dump({"parameters": {"N": N, "N_LE": N_LE, "dt": DT, "sigma": SIGMA,
                              "T_trans": T_TRANS, "T_meas": T_MEAS, "alphas": ALPHAS},
               "noisy_sweeps": noisy,
               "deterministic_locked": det,
               "thresholds": thresholds,
               "lyap_plain": le_plain,
               "lyap_feedback": le_fb}, f, indent=2)
print("Saved", png, json_out)
