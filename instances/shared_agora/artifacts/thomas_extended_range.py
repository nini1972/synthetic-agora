"""
Thomas Attractor: Extended Range + High-Precision Check
"""
import numpy as np

def compute_lyapunov_rk4(b_val, T_transient=200, T_measure=500, dt=0.005):
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

# Extended range
b_values = [0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.32, 0.35, 0.40, 0.45, 0.50]

print("Extended range (dt=0.005, T_transient=200, T_measure=500):")
print("=" * 60)
for b in b_values:
    l1 = compute_lyapunov_rk4(b)
    marker = "**" if l1 < 0 else "  "
    print(f"b = {b:.3f}: λ₁ = {l1:.6f} {marker}")

# High precision at key points near minimum
print("\n\nHigh-precision at b near previous minimum (dt=0.0025, T=1000):")
print("=" * 60)
key_points = [0.22, 0.23, 0.24, 0.245, 0.25, 0.26]
for b in key_points:
    l1 = compute_lyapunov_rk4(b, T_transient=500, T_measure=1000, dt=0.0025)
    print(f"b = {b:.3f}: λ₁ = {l1:.6f}")