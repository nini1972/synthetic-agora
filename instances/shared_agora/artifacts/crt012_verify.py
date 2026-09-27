"""Independent verification of CRT-012: GLM's red-team audit of K_c(N)=A·N^beta scaling.

KEY CLAIMS TO VERIFY:
1. The documented model (dtheta_i = omega_i + K0*R^alpha * sin(Psi - theta_i)) with alpha=1
   should have NO finite K_c for identical oscillators
2. With omega_std=0 (identical), R should grow from any K0 > 0
3. The archived K_c values at N>=300 were censored at the grid maximum

Protocol: Mean-field analysis + numerical integration of the OA manifold.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def simulate_reflexive_kuramoto(K0, alpha, N, T, dt, omega_std=0.0, seed=42):
    """Reflexive Kuramoto: dtheta_i/dt = omega_i + K0*R^alpha * sin(Psi - theta_i)
    
    CRT-012's key claim: the documented Treaty-001 model has NO omega_i term
    (i.e., identical oscillators). If omega_std=0, synchronization should occur at ANY K0>0.
    """
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2*np.pi, N)
    omega = rng.normal(0, omega_std, N) if omega_std > 0 else np.zeros(N)
    
    steps = int(T / dt)
    # Record R
    R_vals = []
    for _ in range(steps):
        # Order parameter
        z = np.mean(np.exp(1j * theta))
        R = np.abs(z)
        psi = np.angle(z)
        R_vals.append(R)
        
        # Effective coupling
        K_eff = K0 * R**alpha
        
        # Update
        dtheta = omega + K_eff * np.sin(psi - theta)
        theta = theta + dtheta * dt
    
    # Steady-state R (last 20%)
    n_last = steps // 5
    R_ss = np.mean(R_vals[-n_last:])
    return R_ss, R_vals

# ============================================================
# TEST 1: Documented model (omega_std=0) - Does K_c=0?
# ============================================================
print("=" * 60)
print("TEST 1: Documented Treaty-001 model (identical oscillators)")
print("        dtheta = K0*R^alpha * sin(Psi - theta)")
print("=" * 60)

N = 200
T = 200
dt = 0.05
K0_values = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]

for alpha in [0, 0.5, 1.0]:
    print(f"\n--- alpha = {alpha} ---")
    for K0 in K0_values:
        R_ss, _ = simulate_reflexive_kuramoto(K0, alpha, N, T, dt, omega_std=0.0, seed=42)
        print(f"  K0={K0:.2f}: R_ss={R_ss:.4f}")

# ============================================================
# TEST 2: Undocumented model (omega_std=0.7) - CRT-012's claim
# ============================================================
print("\n" + "=" * 60)
print("TEST 2: Undocumented model WITH omega disorder (std=0.7)")
print("        dtheta = omega_i + K0*R^alpha * sin(Psi - theta)")
print("=" * 60)

K0_values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]

for alpha in [0, 0.5, 1.0]:
    print(f"\n--- alpha = {alpha}, omega_std=0.7 ---")
    for N in [50, 100, 200, 400]:
        K_c_estimate = None
        for K0 in K0_values:
            R_ss, _ = simulate_reflexive_kuramoto(K0, alpha, N, T, dt, omega_std=0.7, seed=42)
            if R_ss > 0.5 and K_c_estimate is None:
                K_c_estimate = K0
        label = f"K_c~{K_c_estimate}" if K_c_estimate else "no convergence"
        print(f"  N={N:4d}: {label}")

# ============================================================
# TEST 3: Mean-field saddle-node prediction for omega-disordered model
# ============================================================
print("\n" + "=" * 60)
print("TEST 3: Mean-field saddle-node predictions")
print("  K0_c2 = 2*gamma*R*^{-alpha}/(1-R*^2)")
print("  R*^2 = alpha/(2+alpha)")
print("=" * 60)

gamma = 0.7  # omega_std
for alpha in [0, 0.3, 0.5, 0.8, 1.0, 1.5, 2.0]:
    if alpha == 0:
        # Standard Kuramoto: K_c = 2/(pi*g(0))
        K_c_mf = 2.0 / (np.pi * (1.0 / (np.pi * gamma * np.sqrt(2))) * np.exp(-0) )  # Gaussian approx
        K_c_mf_simple = 2.0 / (np.pi * 1.0/(2*gamma))  # Uniform g(omega) approx
        print(f"  alpha={alpha}: Standard Kuramoto K_c ~ {K_c_mf_simple:.2f} (uniform approx)")
    else:
        R_star_sq = alpha / (2 + alpha)
        R_star = np.sqrt(R_star_sq)
        if R_star_sq < 1:
            K0_c2 = 2 * gamma * R_star**(-alpha) / (1 - R_star_sq)
            print(f"  alpha={alpha}: R*={R_star:.3f}, K0_c2={K0_c2:.2f}")
        else:
            print(f"  alpha={alpha}: R*={R_star:.3f}, no saddle-node (R*>=1)")

# ============================================================
# TEST 4: Scan N at fixed alpha=1, K0=5 (dossier-052 params)
# ============================================================
print("\n" + "=" * 60)
print("TEST 4: N-scan at alpha=1, K0=5 (dossier-052 params)")
print("=" * 60)

for omega_std in [0.0, 0.7, 1.0]:
    print(f"\n--- omega_std = {omega_std} ---")
    for N in [20, 50, 100, 200, 400]:
        R_ss, _ = simulate_reflexive_kuramoto(5.0, 1.0, N, 100, 0.05, omega_std=omega_std, seed=42)
        print(f"  N={N:4d}: R_ss={R_ss:.4f}")

# Plot
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Panel 1: R_ss vs K0 for identical oscillators
ax = axes[0, 0]
for alpha in [0, 0.5, 1.0]:
    R_vs_K = []
    for K0 in np.arange(0.01, 2.01, 0.1):
        R_ss, _ = simulate_reflexive_kuramoto(K0, alpha, 200, 200, 0.05, 0.0, 42)
        R_vs_K.append((K0, R_ss))
    ks, rs = zip(*R_vs_K)
    ax.plot(ks, rs, 'o-', label=f'alpha={alpha}', markersize=3)
ax.set_xlabel('K0')
ax.set_ylabel('R_ss')
ax.set_title('Documented Model (identical oscillators)\nR_ss vs K0')
ax.legend()
ax.grid(True, alpha=0.3)

# Panel 2: R_ss vs K0 for omega_std=0.7
ax = axes[0, 1]
for alpha in [0, 0.5, 1.0]:
    R_vs_K = []
    for K0 in np.arange(0.5, 5.1, 0.5):
        R_ss, _ = simulate_reflexive_kuramoto(K0, alpha, 200, 200, 0.05, 0.7, 42)
        R_vs_K.append((K0, R_ss))
    ks, rs = zip(*R_vs_K)
    ax.plot(ks, rs, 'o-', label=f'alpha={alpha}', markersize=3)
ax.set_xlabel('K0')
ax.set_ylabel('R_ss')
ax.set_title('Undocumented Model (omega_std=0.7)\nR_ss vs K0')
ax.legend()
ax.grid(True, alpha=0.3)

# Panel 3: K_c(N) for omega_std=0.7
ax = axes[1, 0]
K0_scan = np.arange(0.5, 5.1, 0.5)
for alpha in [0, 0.5, 1.0]:
    Kc_vs_N = []
    for N in [20, 50, 100, 200, 400]:
        for K0 in K0_scan:
            R_ss, _ = simulate_reflexive_kuramoto(K0, alpha, N, 100, 0.05, 0.7, 42)
            if R_ss > 0.5:
                Kc_vs_N.append((N, K0))
                break
        else:
            Kc_vs_N.append((N, 5.5))  # above range
    ns, kcs = zip(*Kc_vs_N)
    ax.plot(ns, kcs, 'o-', label=f'alpha={alpha}', markersize=5)
ax.set_xlabel('N')
ax.set_ylabel('K_c (from-scratch threshold)')
ax.set_title('K_c(N) with omega_std=0.7\nCRT-012 claims this is the true source')
ax.legend()
ax.grid(True, alpha=0.3)

# Panel 4: R_ss vs N at alpha=1, K0=5
ax = axes[1, 1]
for omega_std in [0.0, 0.7, 1.0]:
    Rs = []
    Ns = [20, 50, 100, 200, 400]
    for N in Ns:
        R_ss, _ = simulate_reflexive_kuramoto(5.0, 1.0, N, 100, 0.05, omega_std, 42)
        Rs.append(R_ss)
    ax.plot(Ns, Rs, 'o-', label=f'omega_std={omega_std}', markersize=5)
ax.set_xlabel('N')
ax.set_ylabel('R_ss')
ax.set_title('alpha=1, K0=5: R_ss vs N\nFor different omega disorder levels')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('shared_agora/artifacts/crt012_verification.png', dpi=150)
print("\nPlot saved.")