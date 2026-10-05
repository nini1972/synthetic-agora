"""
EMP-042 refinement / active defence (fast local version).
Tests the claims in EMP-042 and EMP-070 for Kuramoto with state-dependent
feedback K(t)=K0 R(t)^alpha.
"""
import os, json, time, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np.random.seed(0x5F3759DF)

N = 200
DT = 0.02
SIGMA = 0.1
T_TRANS = 100.0
N_TRANS = int(T_TRANS / DT)          # 5000 steps
OMEGAS = np.random.normal(0.0, 1.0, size=N)
ALPHAS = [1.0, 1.5, 2.0]
K0_FWD = np.linspace(0.5, 4.5, 21)
K0_BWD = K0_FWD[::-1]
K0_DET = K0_BWD.copy()


def batch_evolve(theta, K0_arr, alpha, n_steps, deterministic=False):
    """theta shape (batch,N); K0_arr shape (batch,)."""
    for _ in range(n_steps):
        z = np.mean(np.exp(1j * theta), axis=1)
        R = np.abs(z)
        Psi = np.angle(z)
        K = K0_arr * (R ** alpha)
        dtheta = OMEGAS + (K * R)[:, None] * np.sin(Psi[:, None] - theta)
        if not deterministic:
            dtheta += SIGMA * np.sqrt(DT) * np.random.randn(*theta.shape)
        theta += DT * dtheta
        theta %= 2.0 * np.pi
    return theta


def order(theta):
    z = np.mean(np.exp(1j * theta), axis=1)
    return np.abs(z), np.angle(z)


# ---------------------------------------------------------------------------
# Noisy hysteresis sweeps (independent K0 batch)
# ---------------------------------------------------------------------------
noisy = {}
t0 = time.time()
for alpha in ALPHAS:
    theta = np.random.uniform(0, 2*np.pi, size=(len(K0_FWD), N))
    theta = batch_evolve(theta, K0_FWD, alpha, N_TRANS)
    R_fwd, _ = order(theta)

    # backward from an endpoint that has been warmed at high K0
    theta_hi = np.random.uniform(0, 2*np.pi, size=N)
    for _ in range(N_TRANS):
        theta_hi = batch_evolve(theta_hi[None, :], np.array([K0_FWD[-1]]), alpha, 1)[0]
    theta_b = np.tile(theta_hi, (len(K0_BWD), 1))
    theta_b = batch_evolve(theta_b, K0_BWD, alpha, N_TRANS)
    R_bwd_rand, _ = order(theta_b)

    theta_c = np.zeros((len(K0_BWD), N))
    theta_c = batch_evolve(theta_c, K0_BWD, alpha, N_TRANS)
    R_bwd_coh, _ = order(theta_c)

    noisy[f"a{alpha:.1f}"] = dict(K_fwd=K0_FWD.tolist(), R_fwd=R_fwd.tolist(),
                                   K_bwd=K0_BWD.tolist(), R_bwd_rand=R_bwd_rand.tolist(),
                                   R_bwd_coh=R_bwd_coh.tolist())
    print(f"alpha={alpha:.1f} fwd R range {R_fwd.min():.3f}-{R_fwd.max():.3f}  "
          f"coh back R range {R_bwd_coh.min():.3f}-{R_bwd_coh.max():.3f}")
print("sweeps elapsed", time.time()-t0)


# ---------------------------------------------------------------------------
# Deterministic locked branch (warm-started sequential scan)
# ---------------------------------------------------------------------------
det = {}
for alpha in ALPHAS:
    theta = np.zeros(N)
    Rvals = []
    for K0 in K0_DET:
        theta = batch_evolve(theta[None, :], np.array([K0]), alpha,
                             N_TRANS, deterministic=True)[0]
        Rvals.append(order(theta[None, :])[0][0])
    det[f"a{alpha:.1f}"] = dict(K=K0_DET.tolist(), R=Rvals)
    print(f"det alpha={alpha:.1f} R range {min(Rvals):.3f}-{max(Rvals):.3f}")


# ---------------------------------------------------------------------------
# Zero-mode-projected finite-difference LE
# ---------------------------------------------------------------------------
def le_feedback(K0, alpha, Nle=40, T=150.0, Ttrans=75.0):
    n = int(T / DT)
    nt = int(Ttrans / DT)
    tau = 1.0
    every = max(1, int(tau / DT))
    eps0 = 1e-8
    omeg = np.random.normal(0.0, 1.0, size=Nle)
    theta = np.random.uniform(0, 2*np.pi, size=Nle)

    def rhs(th):
        z = np.mean(np.exp(1j * th))
        R = np.abs(z)
        Psi = np.angle(z) if R > 1e-12 else 0.0
        return omeg + K0*(R**alpha)*R*np.sin(Psi - th)

    for _ in range(nt):
        k1 = rhs(theta)
        k2 = rhs(theta + 0.5*DT*k1)
        k3 = rhs(theta + 0.5*DT*k2)
        k4 = rhs(theta + DT*k3)
        theta += (DT/6.0)*(k1 + 2*k2 + 2*k3 + k4)

    d = np.random.randn(Nle)
    d -= d.mean()
    d /= np.linalg.norm(d)
    s = 0.0
    ren = 0
    for step in range(n):
        k1 = rhs(theta)
        k2 = rhs(theta + 0.5*DT*k1)
        k3 = rhs(theta + 0.5*DT*k2)
        k4 = rhs(theta + DT*k3)
        theta += (DT/6.0)*(k1 + 2*k2 + 2*k3 + k4)

        thp = theta + eps0*d
        k1p = rhs(thp)
        k2p = rhs(thp + 0.5*DT*k1p)
        k3p = rhs(thp + 0.5*DT*k2p)
        k4p = rhs(thp + DT*k3p)
        thp += (DT/6.0)*(k1p + 2*k2p + 2*k3p + 4*k4p)

        delta = thp - theta
        delta -= delta.mean()
        nrm = np.linalg.norm(delta)
        nrm = max(nrm, 1e-30)
        if (step + 1) % every == 0:
            s += np.log(nrm / eps0)
            ren += 1
            d = delta / nrm
    return s / (ren * tau) if ren else 0.0


le_plain = {}
le_fb = {}
t0 = time.time()
Kle = np.arange(0.5, 4.55, 0.5)
for K in Kle:
    le_plain[float(K)] = float(le_feedback(K, 0.0))
    print(f"plain K={K:.2f} lambda={le_plain[float(K)]:.5f}")
for alpha in [1.0, 2.0]:
    for K0 in Kle:
        le_fb[f"a{alpha}_K{K0}"] = float(le_feedback(K0, alpha))
        print(f"alpha={alpha} K0={K0:.2f} lambda={le_fb[f'a{alpha}_K{K0}']:.5f}")
print("LE elapsed", time.time()-t0)


# ---------------------------------------------------------------------------
# Thresholds
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
    dd = det[f"a{alpha:.1f}"]
    axes[1,0].plot(dd["K"], dd["R"], marker='o', ms=2, label=f"α={alpha}")

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
axes[1,1].set_title("LE control: plain Kuramoto")

for alpha in [1.0, 2.0]:
    ks = sorted([float(k.split('_K')[1]) for k in le_fb if k.startswith(f"a{alpha}_")])
    vals = [le_fb[f"a{alpha}_K{k}"] for k in ks]
    axes[1,2].plot(ks, vals, marker='o', label=f"α={alpha}")
axes[1,2].axhline(0, color='r', ls='--')
axes[1,2].set_xlabel(r"$K_0$")
axes[1,2].set_ylabel(r"$\lambda_{\max}$")
axes[1,2].set_title("Feedback LE (finite-difference)")
axes[1,2].legend()

plt.tight_layout()
os.makedirs('../../shared_agora/artifacts', exist_ok=True)
png = '../../shared_agora/artifacts/emp042_refinement.png'
json_out = '../../shared_agora/artifacts/emp042_refinement.json'
plt.savefig(png, dpi=200)

with open(json_out, 'w') as f:
    json.dump({"parameters": {"N": N, "dt": DT, "sigma": SIGMA, "T_trans": T_TRANS,
                              "alphas": ALPHAS, "K_grid": K0_FWD.tolist()},
               "noisy_sweeps": noisy,
               "deterministic_locked": det,
               "thresholds": thresholds,
               "lyap_plain": le_plain,
               "lyap_feedback": le_fb}, f, indent=2)
print("Saved", png, json_out)
