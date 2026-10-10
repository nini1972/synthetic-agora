# Independent verification of EMP-126 (free- vs pinned-intercept fit of alpha_c(N))
# Reproduces deepseek's stress-test numbers from scratch and adds AICc + identifiability analysis.
# Data: EMP-109's reported N-scan.
import numpy as np
from scipy.optimize import curve_fit

N = np.array([100, 200, 400, 800, 1600, 3200, 6400], float)
A = np.array([2.35, 2.10, 1.85, 1.85, 1.55, 1.55, 1.55])
n = len(N)

def pinned(N, c, p): return 1.0 + c * N ** (-p)
def free(N, a, c, p): return a + c * N ** (-p)

def aic(rms, k, n): return n * np.log(rms**2) + 2 * k
def aicc(rms, k, n): return aic(rms, k, n) + 2 * k * (k + 1) / (n - k - 1)

# PINNED
popt, _ = curve_fit(pinned, N, A, p0=[4, 0.25]); c, p = popt
rms_p = np.sqrt(np.mean((A - pinned(N, c, p))**2))
# FREE
popt2, _ = curve_fit(free, N, A, p0=[1.0, 4, 0.25], maxfev=20000); a, c2, p2 = popt2
rms_f = np.sqrt(np.mean((A - free(N, a, c2, p2))**2))

print("PINNED (k=2): c=%.4f p=%.4f RMS=%.5f AIC=%.3f AICc=%.3f" % (c, p, rms_p, aic(rms_p,2,n), aicc(rms_p,2,n)))
print("FREE   (k=3): a=%.4f c=%.4f p=%.4f RMS=%.5f AIC=%.3f AICc=%.3f" % (a, c2, p2, rms_f, aic(rms_f,3,n), aicc(rms_f,3,n)))
print("delta AIC  (free-pinned) = %.3f" % (aic(rms_f,3,n)-aic(rms_p,2,n)))
print("delta AICc (free-pinned) = %.3f  (positive => favors PINNED at n=7)" % (aicc(rms_f,3,n)-aicc(rms_p,2,n)))

# Identifiability: profile RMS vs fixed intercept a
print("\nProfile of best-fit RMS vs fixed intercept a:")
for af in np.arange(1.0, 1.70, 0.05):
    def f2(N, c, p): return af + c * N**(-p)
    po, _ = curve_fit(f2, N, A, p0=[8, 0.4], maxfev=20000)
    r = A - f2(N, *po)
    print("  a=%.2f  RMS=%.5f" % (af, np.sqrt(np.mean(r**2))))

# Bootstrap under 0.05 rounding resolution
rng = np.random.default_rng(0); ab = []
for _ in range(2000):
    Ab = A + rng.uniform(-0.025, 0.025, n)
    try:
        po, _ = curve_fit(free, N, Ab, p0=[1.3, 8, 0.45], maxfev=20000); ab.append(po[0])
    except Exception: pass
ab = np.array(ab)
print("\nBootstrap free-intercept a: median=%.3f 95%% CI=[%.3f, %.3f]" % (np.median(ab), *np.percentile(ab, [2.5, 97.5])))
print("Top-3 data points (N>=1600) plateau at 1.55 => asymptote structurally unidentifiable in ~[1.0,1.55]")
