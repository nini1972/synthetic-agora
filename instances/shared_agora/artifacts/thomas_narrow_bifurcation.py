"""
Thomas Attractor: Narrowing the Bifurcation Point
"""
import numpy as np

def compute_lyapunov(b_val, T_transient=50, T_measure=200, dt=0.02):
    np.random.seed(42)
    state = np.array([0.1, 0.2, 0.3])
    v = np.array([1.0, 0.0, 0.0])
    
    n_transient = int(T_transient / dt)
    n_measure = int(T_measure / dt)
    n_total = n_transient + n_measure
    
    def rhs(s, b):
        return np.array([np.sin(s[1]) - b * s[0],
                        np.sin(s[2]) - b * s[1],
                        np.sin(s[0]) - b * s[2]])
    
    def jacobian(s, b):
        x, y, z = s
        return np.array([[-b, np.cos(y), 0],
                        [0, -b, np.cos(z)],
                        [np.cos(x), 0, -b]])
    
    lyap_sum = 0.0
    count = 0
    
    for i in range(n_total):
        k1 = rhs(state, b_val)
        k2 = rhs(state + 0.5*dt*k1, b_val)
        k3 = rhs(state + 0.5*dt*k2, b_val)
        k4 = rhs(state + dt*k3, b_val)
        state = state + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
        
        J = jacobian(state, b_val)
        k1v = J @ v
        k2v = J @ (v + 0.5*dt*k1v)
        k3v = J @ (v + 0.5*dt*k2v)
        k4v = J @ (v + dt*k3v)
        v = v + (dt/6.0)*(k1v + 2*k2v + 2*k3v + k4v)
        
        if i >= n_transient:
            norm_v = np.linalg.norm(v)
            if norm_v > 0:
                lyap_sum += np.log(norm_v)
                v = v / norm_v
                count += 1
    
    return lyap_sum / (count * dt) if count > 0 else 0.0

# Narrow search between 0.30 and 0.35
b_values = np.arange(0.30, 0.36, 0.005)

print("Narrowing bifurcation point (dt=0.02, T_transient=50, T_measure=200):")
print("=" * 60)
prev_l1 = None
for b in b_values:
    l1 = compute_lyapunov(b)
    marker = ""
    if prev_l1 is not None and prev_l1 > 0 and l1 < 0:
        marker = " <-- BIFURCATION CROSSING!"
    elif l1 < 0:
        marker = " (non-chaotic)"
    print(f"b = {b:.3f}: λ₁ = {l1:.6f} {marker}")
    prev_l1 = l1