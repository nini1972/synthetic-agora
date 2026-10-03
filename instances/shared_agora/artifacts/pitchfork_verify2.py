import numpy as np

def integrate(r, x0, T=50.0, dt=0.001):
    x = x0
    for _ in range(int(T/dt)):
        x = x + (r*x - x**3)*dt
    return x

# Correct test points
tests = [(-0.5, 0.0), (0.5, 0.7071), (1.0, 1.0), (1.25, 1.1180), (2.0, 1.4142)]
print("r | x_num(+,−) | analytic sqrt(r) | PASS?")
all_pass = True
for r, analytic in tests:
    xp = integrate(r, 0.05)
    xm = integrate(r, -0.05)
    exp_p = np.sqrt(max(r,0)) if r>0 else 0.0
    ok = abs(xp-exp_p)<0.02 and abs(xm+exp_p)<0.02
    all_pass &= ok
    print(f"{r:5.2f} | {xp:+.4f},{xm:+.4f} | {exp_p:.4f} | {'PASS' if ok else 'FAIL'}")

# Check r<0 -> origin stable, r>0 -> x=0 unstable
print("\nStability check:")
print("  r=-1: x=0 globally stable (xp,xm -> 0):", abs(integrate(-1,0.05))<1e-3, abs(integrate(-1,-0.05))<1e-3)
print("  r=+1: x=0 unstable (perturb grows to sqrt(1)):", abs(integrate(1,0.05)-1.0)<0.02)
print("\nOVERALL:", "PASS - supercritical pitchfork bifurcation confirmed at r_c=0" if all_pass else "FAIL")
