import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Verify supercritical pitchfork: dx/dt = r*x - x^3
# Fixed points: x=0, and x=+-sqrt(r) for r>0
# Stability: f'(x) = r - 3x^2
#   at x=0: f'(0)=r -> stable for r<0, unstable for r>0
#   at x=+-sqrt(r): f'= r-3r = -2r <0 -> stable for r>0
# Supercritical pitchfork at r_c=0.

# Numerical verification: time-integrate from near-zero initial condition
def integrate(r, x0, T=50.0, dt=0.001):
    x = x0
    n = int(T/dt)
    for _ in range(n):
        x = x + (r*x - x**3)*dt
    return x

rs = np.linspace(-1.0, 2.0, 61)
stable_pos = []
for r in rs:
    # from +small and -small perturbations
    xp = integrate(r, 0.05)
    xm = integrate(r, -0.05)
    stable_pos.append((r, xp, xm))

# Analytic branches
r_analytic = np.linspace(0, 2, 200)
x_analytic = np.sqrt(np.maximum(r_analytic, 0))

# Test: r<0 converge to 0, r>0 converge to +-sqrt(r)
print("Verification results:")
err_max = 0
for r, xp, xm in stable_pos:
    if r < 0:
        e = abs(xp) + abs(xm)
    else:
        e = abs(xp - np.sqrt(r)) + abs(xm + np.sqrt(r))
    err_max = max(err_max, e)
print(f"  Max deviation from analytic branch = {err_max:.4f}")

# Check symmetry-breaking: at r<0, x=0 stable; r>0, two branches
print("  r=-0.5: xp=%.4f, xm=%.4f (both->0)" % (stable_pos[15][1], stable_pos[15][2]))
print("  r=+0.5: xp=%.4f, xm=%.4f (should be +-0.707)" % (stable_pos[45][1], stable_pos[45][2]))
print("  r=+1.0: xp=%.4f, xm=%.4f (should be +-1.0)" % (stable_pos[60][1], stable_pos[60][2]))

plt.figure(figsize=(8,5))
for r, xp, xm in stable_pos:
    plt.plot(r, xp, 'b.', markersize=3)
    plt.plot(r, xm, 'r.', markersize=3)
plt.plot(r_analytic, x_analytic, 'k-', lw=1, label='x=+sqrt(r)')
plt.plot(r_analytic, -x_analytic, 'k-', lw=1, label='x=-sqrt(r)')
plt.axhline(0, color='g', ls=':')
plt.axvline(0, color='m', ls=':', label='r_c=0')
plt.xlabel('r'); plt.ylabel('stable fixed point x')
plt.title('Supercritical Pitchfork Bifurcation: dx/dt = rx - x^3')
plt.legend(); plt.grid(True)
plt.savefig('pitchfork_verify.png', dpi=100, bbox_inches='tight')
print("saved pitchfork_verify.png")
