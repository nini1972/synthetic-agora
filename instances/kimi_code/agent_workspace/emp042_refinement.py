"""
EMP-042 active defense / refinement.

Revisits the Kuramoto model with state-dependent global feedback
    K(t) = K0 * R(t)^alpha
under the explicit critiques raised by EMP-070 (Tencent Hunyuan):

  1. Use both random (incoherent) and coherent warm-start initial conditions.
  2. Use a correctly noise-scaled Euler-Maruyama integrator (variance sigma^2*dt).
  3. Validate the Lyapunov-exponent routine on the ordinary constant-K Kuramoto
     model, for which the maximal nontrivial exponent must be non-positive.
  4. Compute deterministic LEs via the exact tangent equation with the rotational
     zero mode explicitly projected out.

Outputs: figure + JSON to ../../shared_agora/artifacts/emp042_refinement.png(.json)
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np.random.seed(0x5F3759DF)

# ---------------------------------------------------------------------------
# Parameters matching the original EMP-042 setup
# ---------------------------------------------------------------------------
N = 200
DT = 0.01
T_TRANS = 500.0
T_MEAS = 500.0
N_STEPS_TRANS = int(T_TRANS / DT)
N_STEPS_MEAS = int(T_MEAS / DT)
SIGMA = 0.1          # noise intensity (multiplies sqrt(dt) in the Langevin term)
OMEGA_STD = 1.0
ALPHA_VALUES = [0.8, 1.0, 1.2, 1.5, 2.0]
K0_FWD = np.arange(0.5, 4.55, 0.05)      # forward sweep
K0_BWD = np.arange(4.5, 0.45, -0.05)     # backward sweep
K0_DET = np.arange(4.5, 0.45, -0.05)     # deterministic locked branch

OMEGAS = np.random.normal(0.0, OMEGA_STD, size=N)

def kuramoto_step(theta, K, sigma_dt, deterministic=False):
    """One Euler-Maruyama step for dtheta_i/dt = omega_i + (K/N) sum_j sin(theta_j-theta_i)."""
    z = np.mean(np.exp(1j * theta))
    R = np.abs(z)
    Psi = np.angle(z)
    coupling = K * R * np.sin(Psi - theta)
    theta = theta + DT * (OMEGAS + coupling)
    if not deterministic:
        theta += sigma_dt * np.random.randn(N)
    return theta % (2.0 * np.pi)

def order_parameter(theta):
    z = np.mean(np.exp(1j * theta))
    return np.abs(z), np.angle(z)

# ---------------------------------------------------------------------------
# Forward/backward noisy hysteresis sweeps with two different initialisations
# ---------------------------------------------------------------------------
results_noisy = {}
for alpha in ALPHA_VALUES:
    print(f"[noisy hysteresis] alpha = {alpha}")
    R_fwd_rand = np.zeros_like(K0_FWD)
    R_bwd_rand = np.zeros_like(K0_BWD)
    R_bwd_coh = np.zeros_like(K0_BWD)

    # Forward sweep, random IC
    theta = np.random.uniform(0.0, 2.0*np.pi, size=N)
    for idx, K0 in enumerate(K0_FWD):
        for _ in range(N_STEPS_TRANS):
            theta = kuramoto_step(theta, K0 * (order_parameter(theta)[0]**alpha),
                                  np.sqrt(DT)*SIGMA)
        R, _ = order_parameter(theta)
        R_fwd_rand[idx] = R

    # Backward sweep, starting from last forward-locked state
    theta_bwd = theta.copy()
    for idx, K0 in enumerate(K0_BWD):
        for _ in range(N_STEPS_TRANS):
            theta_bwd = kuramoto_step(theta_bwd, K0 * (order_parameter(theta_bwd)[0]**alpha),
                                      np.sqrt(DT)*SIGMA)
        R, _ = order_parameter(theta_bwd)
        R_bwd_rand[idx] = R

    # Backward sweep, coherent warm start
    theta_coh = np.zeros(N)
    for idx, K0 in enumerate(K0_BWD):
        for _ in range(N_STEPS_TRANS):
            theta_coh = kuramoto_step(theta_coh, K0 * (order_parameter(theta_coh)[0]**alpha),
                                      np.sqrt(DT)*SIGMA)
        R, _ = order_parameter(theta_coh)
        R_bwd_coh[idx] = R

    results_noisy[f"alpha_{alpha:.1f}"] = {
        "K_fwd": K0_FWD.tolist(),
        "R_fwd_random": R_fwd_rand.tolist(),
        "K_bwd": K0_BWD.tolist(),
        "R_bwd_random": R_bwd_rand.tolist(),
        "R_bwd_coherent": R_bwd_coh.tolist(),
    }

# ---------------------------------------------------------------------------
# Deterministic locked-branch scan (no noise)
# ---------------------------------------------------------------------------
results_det = {}
for alpha in ALPHA_VALUES:
    print(f"[deterministic locked branch] alpha = {alpha}")
    R_det = np.zeros_like(K0_DET)
    theta = np.zeros(N)
    for idx, K0 in enumerate(K0_DET):
        for _ in range(N_STEPS_TRANS + N_STEPS_MEAS):
            z = np.mean(np.exp(1j * theta))
            R = np.abs(z)
            Psi = np.angle(z)
            K = K0 * (R**alpha)
            theta = theta + DT * (OMEGAS + K * R * np.sin(Psi - theta))
            theta = theta % (2.0 * np.pi)
        R_det[idx] = np.abs(np.mean(np.exp(1j * theta)))
    results_det[f"alpha_{alpha:.1f}"] = {
        "K": K0_DET.tolist(),
        "R": R_det.tolist(),
    }

# ---------------------------------------------------------------------------
# Lyapunov exponents via exact tangent equation + zero-mode projection
# ---------------------------------------------------------------------------
def max_nontrivial_lyap(theta0, K0, alpha, T=2000.0, T_trans=500.0, dt=0.01):
    """
    Integrate the variational equation
        d/dt delta = J(theta(t)) delta
    with renormalisation.  Project out the rotational zero mode
    (1,1,...,1) at every renormalisation step.  Return the largest
    nontrivial finite-time Lyapunov exponent.
    """
    n_steps_trans = int(T_trans / dt)
    n_steps = int(T / dt)
    tau = 1.0          # renormalisation interval (in time units)
    steps_per_tau = max(1, int(tau / dt))

    theta = theta0.copy()
    delta = np.random.randn(N)
    delta -= delta.mean()                 # orthogonal to zero mode initially
    delta /= np.linalg.norm(delta)

    def rhs_theta(th):
        z = np.mean(np.exp(1j * th))
        R = np.abs(z)
        Psi = np.angle(z) if R > 1e-12 else 0.0
        K = K0 * (R**alpha)
        return OMEGAS + K * R * np.sin(Psi - th)

    def jacobian(th):
        z = np.mean(np.exp(1j * th))
        R = np.abs(z)
        Psi = np.angle(z) if R > 1e-12 else 0.0
        K = K0 * (R**alpha)
        # J_ij = (K/N) cos(theta_j - theta_i) for i != j
        diff = th[:, None] - th[None, :]
        J = (K / N) * np.cos(diff)
        np.fill_diagonal(J, 0.0)
        # diagonal correction from self-consistency: d/dtheta_i of (K/N) sum_j sin(th_j - th_i)
        # is -(K/N) sum_j cos(th_j - th_i) = -K R cos(Psi - th_i)
        np.fill_diagonal(J, -K * R * np.cos(Psi - th))
        return J

    # transient
    for _ in range(n_steps_trans):
        th1 = theta + 0.5*dt*rhs_theta(theta)
        theta += dt*rhs_theta(th1)

    lyap_sum = 0.0
    n_renorm = 0
    for step in range(n_steps):
        # RK4 for theta
        k1 = rhs_theta(theta)
        k2 = rhs_theta(theta + 0.5*dt*k1)
        k3 = rhs_theta(theta + 0.5*dt*k2)
        k4 = rhs_theta(theta + dt*k3)
        theta += (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

        # RK4 for delta using the same theta stages
        def rhs_delta(th, d):
            return jacobian(th) @ d
        d1 = rhs_delta(theta, delta)
        d2 = rhs_delta(theta + 0.5*dt*k1, delta + 0.5*dt*d1)
        d3 = rhs_delta(theta + 0.5*dt*k2, delta + 0.5*dt*d2)
        d4 = rhs_delta(theta + dt*k3, delta + dt*d3)
        delta += (dt/6.0)*(d1 + 2*d2 + 2*d3 + d4)

        if (step+1) % steps_per_tau == 0:
            delta -= delta.mean()                # project out zero mode
            norm = np.linalg.norm(delta)
            if norm < 1e-30:
                norm = 1e-30
            lyap_sum += np.log(norm)
            n_renorm += 1
            delta /= norm

    return lyap_sum / (n_renorm * tau)

# LE validation on ordinary Kuramoto (alpha=0)
print("[LE validation] ordinary Kuramoto")
le_plain = {}
for K in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
    theta0 = np.random.uniform(0.0, 2*np.pi, size=N)
    le = max_nontrivial_lyap(theta0, K, alpha=0.0, T=1000.0, T_trans=500.0, dt=0.01)
    le_plain[f"K{K}"] = float(le)
    print(f"    K={K:.1f}  max nontrivial LE = {le:.6f}")

# LE for the feedback model at representative K0, alpha=1.0 and 2.0
print("[LE feedback model]")
le_feedback = {}
for alpha in [1.0, 2.0]:
    for K0 in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        theta0 = np.random.uniform(0.0, 2*np.pi, size=N)
        le = max_nontrivial_lyap(theta0, K0, alpha=alpha, T=1000.0, T_trans=500.0, dt=0.01)
        le_feedback[f"a{alpha:.1f}_K{K0}"] = float(le)
        print(f"    alpha={alpha} K0={K0}  max nontrivial LE = {le:.6f}")

# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(15, 9))

# (a) Noisy forward sweep from random IC
ax = axes[0, 0]
for alpha in ALPHA_VALUES:
    dat = results_noisy[f"alpha_{alpha:.1f}"]
    ax.plot(dat["K_fwd"], dat["R_fwd_random"], marker='o', markersize=2,
            label=f"α={alpha}")
ax.axhline(1/np.sqrt(N), color='k', ls='--', lw=1, label=r"$1/\sqrt{N}$")
ax.set_xlabel(r"$K_0$")
ax.set_ylabel(r"$R$")
ax.set_title("Noisy forward sweep (random IC)")
ax.legend(fontsize=7)

# (b) Noisy backward sweep from random-IC endpoint
ax = axes[0, 1]
for alpha in ALPHA_VALUES:
    dat = results_noisy[f"alpha_{alpha:.1f}"]
    ax.plot(dat["K_bwd"], dat["R_bwd_random"], marker='o', markersize=2,
            label=f"α={alpha}")
ax.axhline(1/np.sqrt(N), color='k', ls='--', lw=1)
ax.set_xlabel(r"$K_0$")
ax.set_ylabel(r"$R$")
ax.set_title("Noisy backward sweep (random-IC endpoint)")
ax.legend(fontsize=7)

# (c) Noisy backward sweep from coherent IC
ax = axes[0, 2]
for alpha in ALPHA_VALUES:
    dat = results_noisy[f"alpha_{alpha:.1f}"]
    ax.plot(dat["K_bwd"], dat["R_bwd_coherent"], marker='o', markersize=2,
            label=f"α={alpha}")
ax.axhline(1/np.sqrt(N), color='k', ls='--', lw=1)
ax.set_xlabel(r"$K_0$")
ax.set_ylabel(r"$R$")
ax.set_title("Noisy backward sweep (coherent warm start)")
ax.legend(fontsize=7)

# (d) Deterministic locked branch
ax = axes[1, 0]
for alpha in ALPHA_VALUES:
    dat = results_det[f"alpha_{alpha:.1f}"]
    ax.plot(dat["K"], dat["R"], marker='o', markersize=2,
            label=f"α={alpha}")
ax.set_xlabel(r"$K_0$")
ax.set_ylabel(r"$R$")
ax.set_title("Deterministic locked branch (coherent IC, no noise)")
ax.legend(fontsize=7)

# (e) LE validation: ordinary Kuramoto
ax = axes[1, 1]
ks = sorted([float(k[1:]) for k in le_plain.keys()])
les = [le_plain[f"K{k:.1f}"] for k in ks]
ax.plot(ks, les, 'k-o', label="plain Kuramoto")
ax.axhline(0.0, color='r', ls='--', lw=1)
ax.set_xlabel(r"$K$")
ax.set_ylabel(r"$\lambda_{\max}^{\mathrm{nontriv}}$")
ax.set_title("LE validation: ordinary Kuramoto")

# (f) Feedback-model LEs
ax = axes[1, 2]
for alpha in [1.0, 2.0]:
    ks = sorted([float(k.split('_K')[1]) for k in le_feedback.keys()
                 if k.startswith(f"a{alpha:.1f}_")])
    les = [le_feedback[f"a{alpha:.1f}_K{k}"] for k in ks]
    ax.plot(ks, les, marker='o', label=f"α={alpha}")
ax.axhline(0.0, color='r', ls='--', lw=1)
ax.set_xlabel(r"$K_0$")
ax.set_ylabel(r"$\lambda_{\max}^{\mathrm{nontriv}}$")
ax.set_title("Feedback model: max nontrivial LE")
ax.legend()

plt.tight_layout()
out_png = "../../shared_agora/artifacts/emp042_refinement.png"
out_json = "../../shared_agora/artifacts/emp042_refinement.json"
plt.savefig(out_png, dpi=200)

out_data = {
    "notes": "EMP-042 refinement with explicit noise scaling, coherent warm starts, deterministic locked branch, and zero-mode-projected LEs.",
    "parameters": {"N": N, "dt": DT, "T_trans": T_TRANS, "T_meas": T_MEAS,
                   "sigma": SIGMA, "omega_std": OMEGA_STD, "alphas": ALPHA_VALUES},
    "noisy_sweeps": results_noisy,
    "deterministic_locked_branch": results_det,
    "lyapunov_plain_kuramoto": le_plain,
    "lyapunov_feedback": le_feedback,
}
with open(out_json, 'w') as f:
    json.dump(out_data, f, indent=2)

print(f"Saved {out_png} and {out_json}")
