"""Thomas Attractor Lyapunov - GLM optimized for speed"""
import math, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def compute_lyap(b, dt=0.1, n_trans=2000, n_lyap=2000, seed=42):
    rng = np.random.RandomState(seed)
    x, y, z = rng.uniform(-3,3,3)
    # transient
    for _ in range(n_trans):
        k1x = math.sin(y) - b*x; k1y = math.sin(z) - b*y; k1z = math.sin(x) - b*z
        x2,y2,z2 = x+0.5*dt*k1x, y+0.5*dt*k1y, z+0.5*dt*k1z
        k2x = math.sin(y2) - b*x2; k2y = math.sin(z2) - b*y2; k2z = math.sin(x2) - b*z2
        x3,y3,z3 = x+0.5*dt*k2x, y+0.5*dt*k2y, z+0.5*dt*k2z
        k3x = math.sin(y3) - b*x3; k3y = math.sin(z3) - b*y3; k3z = math.sin(x3) - b*z3
        x4,y4,z4 = x+dt*k3x, y+dt*k3y, z+dt*k3z
        k4x = math.sin(y4) - b*x4; k4y = math.sin(z4) - b*y4; k4z = math.sin(x4) - b*z4
        x += (dt/6.0)*(k1x+2*k2x+2*k3x+k4x)
        y += (dt/6.0)*(k1y+2*k2y+2*k3y+k4y)
        z += (dt/6.0)*(k1z+2*k2z+2*k3z+k4z)
    # tangent
    tx,ty,tz = rng.randn(3)
    n = math.sqrt(tx*tx+ty*ty+tz*tz)
    tx,ty,tz = tx/n,ty/n,tz/n
    ri = 20
    log_sum = 0.0
    rc = 0
    for i in range(n_lyap):
        # state RK4
        k1x = math.sin(y)-b*x; k1y = math.sin(z)-b*y; k1z = math.sin(x)-b*z
        x2,y2,z2 = x+0.5*dt*k1x, y+0.5*dt*k1y, z+0.5*dt*k1z
        k2x = math.sin(y2)-b*x2; k2y = math.sin(z2)-b*y2; k2z = math.sin(x2)-b*z2
        x3,y3,z3 = x+0.5*dt*k2x, y+0.5*dt*k2y, z+0.5*dt*k2z
        k3x = math.sin(y3)-b*x3; k3y = math.sin(z3)-b*y3; k3z = math.sin(x3)-b*z3
        x4,y4,z4 = x+dt*k3x, y+dt*k3y, z+dt*k3z
        k4x = math.sin(y4)-b*x4; k4y = math.sin(z4)-b*y4; k4z = math.sin(x4)-b*z4
        # tangent RK4: d(tan)/dt = J(state)*tan
        # J = [[-b, cos(y), 0], [0, -b, cos(z)], [cos(x), 0, -b]]
        # Use midpoint state for tangent Jacobian
        xm,ym,zm = x+0.5*dt*k1x, y+0.5*dt*k1y, z+0.5*dt*k1z
        cy_m = math.cos(ym); cz_m = math.cos(zm); cx_m = math.cos(xm)
        # k1t = J(state)*tan
        tk1x = -b*tx + math.cos(y)*ty
        tk1y = -b*ty + math.cos(z)*tz
        tk1z = math.cos(x)*tx - b*tz
        # k2t = J(mid)*tan + 0.5*dt*k1t
        tx2,ty2,tz2 = tx+0.5*dt*tk1x, ty+0.5*dt*tk1y, tz+0.5*dt*tk1z
        tk2x = -b*tx2 + cy_m*ty2
        tk2y = -b*ty2 + cz_m*tz2
        tk2z = cx_m*tx2 - b*tz2
        # k3t
        tx3,ty3,tz3 = tx+0.5*dt*tk2x, ty+0.5*dt*tk2y, tz+0.5*dt*tk2z
        tk3x = -b*tx3 + cy_m*ty3
        tk3y = -b*ty3 + cz_m*tz3
        tk3z = cx_m*tx3 - b*tz3
        # k4t
        tx4,ty4,tz4 = tx+dt*tk3x, ty+dt*tk3y, tz+dt*tk3z
        tk4x = -b*tx4 + math.cos(y+dt*k1y)*ty4
        tk4y = -b*ty4 + math.cos(z+dt*k1z)*tz4
        tk4z = math.cos(x+dt*k1x)*tx4 - b*tz4
        # update state
        x += (dt/6.0)*(k1x+2*k2x+2*k3x+k4x)
        y += (dt/6.0)*(k1y+2*k2y+2*k3y+k4y)
        z += (dt/6.0)*(k1z+2*k2z+2*k3z+k4z)
        # update tangent
        tx += (dt/6.0)*(tk1x+2*tk2x+2*tk3x+tk4x)
        ty += (dt/6.0)*(tk1y+2*tk2y+2*tk3y+tk4y)
        tz += (dt/6.0)*(tk1z+2*tk2z+2*tk3z+tk4z)
        if (i+1) % ri == 0:
            norm = math.sqrt(tx*tx+ty*ty+tz*tz)
            if norm > 0:
                log_sum += math.log(norm)
                tx,ty,tz = tx/norm, ty/norm, tz/norm
                rc += 1
    return log_sum / (rc * ri * dt)

print("=" * 60)
print("Thomas Attractor Lyapunov - GLM Independent")
print("dt=0.1, n_trans=2000, n_lyap=2000, 2 seeds")
print("=" * 60)

b_all = [0.05,0.08,0.10,0.12,0.15,0.17,0.18,0.19,0.20,0.205,
         0.208,0.21,0.215,0.22,0.23,0.25,0.28,0.30]

results = []
print(f"{'b':>8} {'s42':>10} {'s123':>10} {'mean':>10} {'std':>10}")
print("-" * 52)
for b in b_all:
    s1 = compute_lyap(b, seed=42)
    s2 = compute_lyap(b, seed=123)
    m = (s1+s2)/2
    sd = abs(s1-s2)/2
    results.append((b, m, sd, s1, s2))
    print(f"{b:>8.3f} {s1:>10.6f} {s2:>10.6f} {m:>10.6f} {sd:>10.6f}")

print("\n" + "=" * 60)
print("ADJUDICATION")
print("=" * 60)
idx = min(range(len(results)), key=lambda i: abs(results[i][0]-0.208))
b_r, m_r, sd_r, _, _ = results[idx]
print(f"\nAt b={b_r:.3f} (claimed b_c=0.208186):")
print(f"  GLM: lam1={m_r:.6f} +/- {sd_r:.6f}")
print(f"  Dossier#002: ~0.035")
print(f"  EMP-011(MiniMax): 0.22-0.36")
print(f"  EMP-014(DeepSeek): 0.024")

print("\nSign changes:")
for i in range(1, len(results)):
    if results[i-1][1]*results[i][1] < 0:
        print(f"  {results[i-1][0]:.3f}({results[i-1][1]:.6f}) -> {results[i][0]:.3f}({results[i][1]:.6f})")

# Plot
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
b_arr = np.array([r[0] for r in results])
lam_arr = np.array([r[1] for r in results])
std_arr = np.array([r[2] for r in results])

ax1 = axes[0]
ax1.errorbar(b_arr, lam_arr, yerr=std_arr, fmt='bo-', capsize=3, markersize=6, label='GLM (2 seeds)')
ax1.axhline(y=0, color='k', linestyle='--', alpha=0.5)
ax1.axvline(x=0.208, color='r', linestyle='--', alpha=0.5, label='b_c=0.208186')
ax1.set_xlabel('b (dissipation)')
ax1.set_ylabel('lambda_1')
ax1.set_title('Thomas Attractor: Max Lyapunov (GLM)')
ax1.legend(); ax1.grid(True, alpha=0.3)

ax2 = axes[1]
ax2.plot(b_arr, lam_arr, 'bo-', markersize=6, label='GLM')
b_e11 = [0.05,0.10,0.15,0.20,0.25,0.30]
l_e11 = [0.34,0.28,0.22,0.15,0.05,0.015]
ax2.plot(b_e11, l_e11, 'rs--', markersize=7, label='EMP-011(MiniMax)')
b_e14 = [0.05,0.10,0.15,0.18,0.19,0.20,0.205,0.208,0.21,0.215,0.22,0.23,0.25,0.28,0.30]
l_e14 = [0.091,0.075,0.004,0.046,0.003,0.030,0.006,0.024,0.020,0.001,0.006,0.009,0.0005,-0.001,0.002]
ax2.plot(b_e14, l_e14, 'g^--', markersize=6, label='EMP-014(DeepSeek)')
ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
ax2.axvline(x=0.208, color='gray', linestyle='--', alpha=0.5)
ax2.set_xlabel('b'); ax2.set_ylabel('lambda_1')
ax2.set_title('Cross-Model Comparison')
ax2.legend(); ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/thomas_lyapunov_glm.png', dpi=150)
print("\nSaved: ../../shared_agora/artifacts/thomas_lyapunov_glm.png")
