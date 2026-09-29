import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sim_alpha_vec(N, alpha, K0, T=25.0, dt=0.02, n_seed=4):
    """Vectorize across seeds via broadcasting."""
    rng = np.random.default_rng(12345)
    theta = rng.uniform(0, 2*np.pi, (n_seed, N))   # (S,N)
    omega = rng.uniform(-1, 1, (n_seed, N))
    n_steps = int(T/dt)
    for _ in range(n_steps):
        z = np.exp(1j*theta).mean(axis=1)          # (S,)
        R = np.abs(z)
        Psi = np.angle(z)
        Keff = K0 * R**alpha                        # (S,)
        theta += (omega - Keff[:,None]*np.sin(theta-Psi[:,None]))*dt
    return np.abs(np.exp(1j*theta).mean(axis=1))    # (S,)

def onset(N, lo=1.0, hi=2.6, n_alpha=21, n_seed=4, thresh=0.5):
    alphas = np.linspace(lo, hi, n_alpha)
    onset_val = None
    for a in alphas:
        Rvals = sim_alpha_vec(N, a, K0, n_seed=n_seed)
        if Rvals.mean() > thresh:
            onset_val = a
    return onset_val

K0 = 5.0
Ns = [200, 400, 800, 1600, 3200]
onsets = []
for N in Ns:
    o = onset(N)
    onsets.append(o)
    print(f"N={N:5d}  onset_alpha ~ {o:.3f}", flush=True)

onsets = np.array(onsets)
Ns_arr = np.array(Ns, dtype=float)
from scipy.optimize import curve_fit
def model(N, c, p):
    return 1.0 + c * N**(-p)
try:
    popt, _ = curve_fit(model, Ns_arr, onsets, p0=[20, 0.5], maxfev=5000)
    c, p = popt
    print(f"Fit: alpha_onset(N) = 1 + {c:.2f} * N^(-{p:.3f})")
except Exception as e:
    print("Fit failed:", e)

plt.figure(figsize=(8,6))
plt.semilogx(Ns_arr, onsets, 'o-', label='measured onset')
if 'popt' in dir():
    fit = model(Ns_arr, *popt)
    plt.semilogx(Ns_arr, fit, '--', label='fit 1 + c N^-p')
plt.axhline(1.0, color='r', ls=':', label='alpha*=1 (gain criterion)')
plt.axhline(2.0, color='g', ls=':', label='alpha=2 (spacing criterion)')
plt.xlabel('N'); plt.ylabel('onset alpha')
plt.title('Reflexive-Kuramoto onset alpha vs N')
plt.legend(); plt.grid(True)
plt.savefig('alpha_onset_fit.png', dpi=100, bbox_inches='tight')
print("saved alpha_onset_fit.png")
