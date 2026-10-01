import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Combine my measured upper-edge data + EMP-088 reported data
# My data (K0=5, T=20, dt=0.02, seed=42, n_seed=4)
my_N = np.array([200, 800, 3200], dtype=float)
my_edge = np.array([2.10, 1.80, 1.50], dtype=float)

# EMP-088 data at alpha=1.6 (upper edge there is ~1.6 since sync breaks above it)
# EMP-088: at N=2000 R drops to 0.55, at N=5000 R=0.01 at alpha=1.6
# So for alpha=1.6, upper edge crosses between N=1000 and N=2000
# Add inferred points: alpha_c ~1.6 at N~2000, and alpha_c near 1.5 at N~5000 (since alpha=1.2 sync persists to 5000, alpha=1.6 breaks)
# Actually from EMP-088 alpha=1.6 breaks at N~2000 => edge_alpha at N=2000 is <1.6
# We'll include as approximate.

# Use only clean measured data for now
Ns = my_N
edges = my_edge

def model(N, c, p, base=1.0):
    return base + c * N**(-p)

popt, _ = curve_fit(model, Ns, edges, p0=[5, 0.4], maxfev=10000)
c, p = popt
print(f"Local fit (3 pts): alpha_c = 1 + {c:.3f}*N^(-{p:.3f})")

# Predict extrapolation
for Ntest in [2000, 5000, 10000, 100000]:
    print(f"  alpha_c({Ntest}) = {model(Ntest, *popt):.3f}")

plt.figure(figsize=(8,5))
plt.semilogx(Ns, edges, 'o-', label='measured (mine)')
plt.semilogx(np.logspace(2,5,100), model(np.logspace(2,5,100), *popt), '--', label='fit')
plt.axhline(1.0, color='r', ls=':', label='alpha*=1')
plt.axhline(2.0, color='g', ls=':', label='alpha=2')
plt.xlabel('N'); plt.ylabel('alpha_c')
plt.legend(); plt.grid(True)
plt.savefig('local_fit.png', dpi=100, bbox_inches='tight')
print("saved local_fit.png")
