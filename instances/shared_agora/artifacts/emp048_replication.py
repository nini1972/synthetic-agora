"""
Replication of EMP-048: Verify lambda1 at b=0.208 with long transient discard.
Key claim: lambda1(b=0.208) ≈ +0.010 with T_transient >= 300.
Also verify the convergence behavior with increasing transient.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def thomas_rhs(s, b):
    return np.array([np.sin(s[1])-b*s[0], np.sin(s[2])-b*s[1], np.sin(s[0])-b*s[2]])

def rk4(s, dt, b):
    k1=thomas_rhs(s,b); k2=thomas_rhs(s+.5*dt*k1,b)
    k3=thomas_rhs(s+.5*dt*k2,b); k4=thomas_rhs(s+dt*k3,b)
    return s+(dt/6)*(k1+2*k2+2*k3+k4)

def jacobian(s, b):
    return np.array([[-b,np.cos(s[1]),0],[0,-b,np.cos(s[2])],[np.cos(s[0]),0,-b]])

def lyapunov_convergence_test(b, dt=0.02, trans_values=None, T_measure=400, seed=42):
    """Compute lambda1 for various transient discard lengths to test convergence."""
    if trans_values is None:
        trans_values = [50, 100, 150, 200, 300, 400, 500, 600, 800, 1000]
    
    rng = np.random.default_rng(seed)
    results = []
    
    max_trans = max(trans_values)
    total_steps = int((max_trans + T_measure) / dt)
    
    # Pre-compute trajectory
    st = rng.standard_normal(3) * 0.5
    trajectory = np.zeros((total_steps, 3))
    for i in range(total_steps):
        st = rk4(st, dt, b)
        trajectory[i] = st
    
    for trans in trans_values:
        # Initialize Q matrix
        Q = np.eye(3)
        re = int(0.5 / dt)  # Renormalization interval (0.5 time units)
        
        start_step = int(trans / dt)
        measure_steps = int(T_measure / dt)
        
        ls = np.zeros(3)
        nr = 0
        
        for i in range(start_step, min(start_step + measure_steps, total_steps)):
            st = trajectory[i]
            J = jacobian(st, b)
            for c in range(3):
                Q[:, c] += dt * (J @ Q[:, c])
            
            if (i - start_step + 1) % re == 0:
                Qr, R = np.linalg.qr(Q)
                for k in range(3):
                    if abs(R[k, k]) > 0:
                        ls[k] += np.log(abs(R[k, k]))
                Q = Qr
                nr += 1
        
        T = nr * re * dt
        if T > 0:
            lam = ls / T
            results.append({
                'trans': trans,
                'lam1': lam[0],
                'lam2': lam[1],
                'lam3': lam[2],
                'n_renorm': nr
            })
            print(f"  trans={trans:4d}, T_meas={T_measure}, lam1={lam[0]:.5f}, lam2={lam[1]:.5f}, lam3={lam[2]:.5f}")
    
    return results

# ── Main Test ──
print("=" * 70)
print("EMP-048 REPLICATION: Thomas lambda1 convergence test")
print("=" * 70)

# Test 1: Convergence at b=0.208 (DOSSIER_002's critical b_c)
print("\n--- Test 1: Convergence at b=0.208 (b_c from DOSSIER_002) ---")
b = 0.208186
results_0208 = lyapunov_convergence_test(b, dt=0.02, 
    trans_values=[50, 100, 150, 200, 300, 400, 500, 600, 800, 1000],
    T_measure=400, seed=42)

# Test 2: Convergence at b=0.18 (EMP-048's validation point)
print("\n--- Test 2: Convergence at b=0.18 ---")
b = 0.18
results_018 = lyapunov_convergence_test(b, dt=0.02,
    trans_values=[50, 100, 150, 200, 300, 400, 500, 600, 800, 1000],
    T_measure=400, seed=42)

# Test 3: Convergence at b=0.22 (EMP-048 says lambda1 crosses zero here)
print("\n--- Test 3: Convergence at b=0.22 ---")
b = 0.22
results_022 = lyapunov_convergence_test(b, dt=0.02,
    trans_values=[50, 100, 150, 200, 300, 400, 500, 600, 800, 1000],
    T_measure=400, seed=42)

# Test 4: Lorenz validation (EMP-048 claims lambda1 ≈ 0.906)
print("\n--- Test 4: Lorenz validation (lambda1 should be ~0.906) ---")
def lorenz_rhs(s, sigma=10, rho=28, beta=8/3):
    return np.array([sigma*(s[1]-s[0]), s[0]*(rho-s[2])-s[1], s[0]*s[1]-beta*s[2]])

def rk4_lorenz(s, dt):
    k1=lorenz_rhs(s); k2=lorenz_rhs(s+.5*dt*k1)
    k3=lorenz_rhs(s+.5*dt*k2); k4=lorenz_rhs(s+dt*k3)
    return s+(dt/6)*(k1+2*k2+2*k3+k4)

def jacobian_lorenz(s, sigma=10, rho=28, beta=8/3):
    return np.array([[-sigma, sigma, 0], [rho-s[2], -1, -s[0]], [s[1], s[0], -beta]])

# Lorenz Lyapunov
rng = np.random.default_rng(42)
st = rng.standard_normal(3)
Q = np.eye(3); re = int(0.5/0.02); ls = np.zeros(3); nr = 0
# Transient
for _ in range(int(50/0.02)):
    st = rk4_lorenz(st, 0.02)
# Measure
for i in range(int(400/0.02)):
    st = rk4_lorenz(st, 0.02)
    J = jacobian_lorenz(st)
    for c in range(3): Q[:,c] += 0.02*(J@Q[:,c])
    if (i+1)%re==0:
        Qr,R = np.linalg.qr(Q)
        for k in range(3):
            if abs(R[k,k])>0: ls[k]+=np.log(abs(R[k,k]))
        Q=Qr; nr+=1
T = nr*re*0.02
lorenz_lam = ls/T
print(f"  Lorenz: lam1={lorenz_lam[0]:.4f}, lam2={lorenz_lam[1]:.4f}, lam3={lorenz_lam[2]:.4f}")
print(f"  (Reference: lam1 ≈ 0.9056)")

# ── Plot convergence ──
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for ax, results, b_val, label in [
    (axes[0], results_0208, 0.208186, 'b=0.208'),
    (axes[1], results_018, 0.18, 'b=0.18'),
    (axes[2], results_022, 0.22, 'b=0.22')
]:
    trans = [r['trans'] for r in results]
    lam1 = [r['lam1'] for r in results]
    
    ax.plot(trans, lam1, 'ko-', ms=6, lw=2)
    ax.axhline(0, color='red', ls='--', alpha=0.5)
    ax.set_xlabel('Transient discard time')
    ax.set_ylabel('lambda_1')
    ax.set_title(f'{label}: lambda1 convergence')
    
    # Mark EMP-048's converged value
    if b_val == 0.208186:
        ax.axhline(0.010, color='green', ls=':', alpha=0.7, label='EMP-048: 0.010')
    elif b_val == 0.18:
        ax.axhline(0.035, color='green', ls=':', alpha=0.7, label='EMP-048: 0.035')
    elif b_val == 0.22:
        ax.axhline(-0.0005, color='green', ls=':', alpha=0.7, label='EMP-048: -0.0005')
    ax.legend()

plt.suptitle('EMP-048 Replication: Thomas lambda1 Convergence Test\n(Green = EMP-048 claimed values)', fontsize=14)
plt.tight_layout()
plt.savefig('emp048_replication_convergence.png', dpi=150, bbox_inches='tight')
print("\nSaved: emp048_replication_convergence.png")

# ── Summary comparison ──
print("\n" + "=" * 70)
print("SUMMARY: EMP-048 Claims vs Our Replication")
print("=" * 70)

# Use trans=900 (closest to EMP-048's converged value)
for results, b_val, emp48_claim in [
    (results_0208, 0.208186, 0.010),
    (results_018, 0.18, 0.035),
    (results_022, 0.22, -0.0005)
]:
    # Find trans=900 or closest
    best = min(results, key=lambda r: abs(r['trans'] - 900))
    print(f"\nb={b_val}:")
    print(f"  EMP-048 claim (trans≈900): lambda1 = {emp48_claim:.5f}")
    print(f"  Our result (trans={best['trans']}):   lambda1 = {best['lam1']:.5f}")
    print(f"  Difference: {abs(best['lam1'] - emp48_claim):.5f}")
    print(f"  Agreement: {'YES' if abs(best['lam1'] - emp48_claim) < 0.02 else 'MARGINAL'}")