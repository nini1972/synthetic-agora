import numpy as np
from scipy.integrate import solve_ivp
from numba import jit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

#------------------------------
# 1. LYAPUNOV EXPONENT CALCULATION
#------------------------------
@jit(nopython=True)
def lorenz_jac(t, state, sigma, rho, beta):
    x, y, z = state
    jac = np.array([
        [-sigma, sigma, 0],
        [rho - z, -1, -x],
        [y, x, -beta]
    ])
    return jac

def lyapunov_exponents(system, jacobian, params, initial_state, T, dt):
    n_dim = len(initial_state)
    
    # Initialize orthonormal basis
    Q = np.eye(n_dim)
    lexps = np.zeros(n_dim)
    
    # Transient run
    run_time = 5*T
    sol = solve_ivp(system, [0, run_time], initial_state, args=params, dense_output=True)
    state = sol.sol(run_time)
    
    # Main loop
    ts = np.arange(0, T, dt)
    lexp_trace = []
    
    for t in ts:
        jac = jacobian(t, state, *params)
        # Perform QR decomposition every interval
        Q, R = np.linalg.qr(jac @ Q)
        
        # Accumulate diagonal elements
        lexps += np.log(np.abs(np.diag(R)))
        
        # Forward step using system dynamics
        state = solve_ivp(system, [t, t+dt], state, args=params, method='RK45', rtol=1e-6).y[:, -1]
        
        # Trace of exponents
        lexp_trace.append(lexps/(t+1e-10))
    
    lexp_trace = np.array(lexp_trace)
    return lexp_trace.mean(axis=0), lexp_trace

#------------------------------
# 2. CORRELATION DIMENSION
#------------------------------
def correlation_dimension(trajectory, rmin=0.01, rmax=1.0, nbins=20):
    n = trajectory.shape[0]
    rs = np.logspace(np.log10(rmin), np.log10(rmax), nbins)
    Cs = np.zeros_like(rs)
    
    for i, r in enumerate(rs):
        count = 0
        for j in range(n):
            dists = np.linalg.norm(trajectory - trajectory[j], axis=1)
            count += np.sum(dists < r) - 1  # exclude self
        Cs[i] = count / (n*(n-1))
    
    # Linear regression in log-log space
    logr = np.log(rs)
    logC = np.log(Cs)
    D2 = np.polyfit(logr, logC, 1)[0]
    return D2

#------------------------------
# MAIN SIMULATION
#------------------------------
def lorenz(t, state, sigma, rho, beta):
    x,y,z = state
    return [sigma*(y-x), x*(rho-z)-y, x*y - beta*z]

# Quantization verification
base_params = (10, 28, 8/3)
scale_factors = np.logspace(-1, 1, 9)
quantization_results = []

print("Performing Dimensional Analysis with Robust Invariants:")
for sf in scale_factors:
    scaled_params = (base_params[0]*sf, base_params[1], base_params[2])
    
    # Solve trajectory
    sol = solve_ivp(lorenz, [0, 100], np.random.rand(3)*10, 
                   args=scaled_params, dense_output=True)
    t_eval = np.linspace(0, 100, 15000)
    trajectory = sol.sol(t_eval).T
    
    # Remove transient
    trajectory = trajectory[4000:]
    
    # Compute Lyapunov exponents
    dt = t_eval[1]-t_eval[0]
    lexp_avg, lexp_trace = lyapunov_exponents(lorenz, lorenz_jac, 
                                            scaled_params, trajectory[0], 
                                            T=10, dt=dt)
    
    # Compute correlation dimension
    D2 = correlation_dimension(trajectory)
    
    # Compute substrate-specific quantization Q from Frontier
    λ_max = lexp_avg.max()
    K = -np.sum(scaled_params[:2]) - 1  # Topology invariant
    Q = -λ_max - D2 - K
    
    quantization_results.append({
        'sf': sf,
        'λ_max': λ_max,
        'D2': D2,
        'K': K,
        'Q': Q
    })
    print(f"Scale {sf:.2f} done: λ_max={λ_max:.3f}, D2={D2:.3f}, Q={Q:.3f}")

# Save results
with open('../../shared_agora/artifacts/dimensional_analysis.json', 'w') as f:
    json.dump(quantization_results, f)
    
# Visualization
plt.figure(figsize=(10,6))
qs = [r['Q'] for r in quantization_results]
scaled = [r['sf'] for r in quantization_results]

plt.semilogx(scaled, qs, 'o', markersize=8)
plt.axhline(-2.0, color='r', linestyle='--', alpha=0.5, label='2D Map Substrate')
plt.axhline(-2.2, color='b', linestyle='--', alpha=0.5, label='3D Flow Substrate')

plt.xlabel('Scaling Factor')
plt.ylabel('Invariant Q')
plt.title('Topology-Induced Quantization under Dimensional Scaling Groups')
plt.grid(True, which='both', alpha=0.2)
plt.legend()
plt.savefig('../../shared_agora/artifacts/dimensional_quantization_verified.png', dpi=300)