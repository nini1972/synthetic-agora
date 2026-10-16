import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Data from EMP-109 N-scan
N = np.array([100,200,400,800,1600,3200,6400], dtype=float)
alpha_c = np.array([2.35,2.10,1.85,1.85,1.55,1.55,1.55])
sigma = 0.05  # reported rounding precision

# models
def free_pow(N, a, c, p):
    return a + c * N**(-p)

def pinned_pow(N, c, p):
    return 1.0 + c * N**(-p)

def flat_pow(N, a):
    return np.full_like(N, a)

def rms(pred, obs):
    return np.sqrt(np.mean((pred-obs)**2))

def log_likelihood(pred, obs, sig):
    n = len(obs)
    return -0.5*n*np.log(2*np.pi*sig**2) - 0.5*np.sum((obs-pred)**2/sig**2)

def aic(loglike, k, n):
    return 2*k - 2*loglike

def aicc(aic_v, k, n):
    return aic_v + 2*k*(k+1)/(n-k-1)

# fits
popt_free, _ = curve_fit(free_pow, N, alpha_c, p0=[1.0,5.0,0.3], maxfev=20000)
popt_pinned, _ = curve_fit(pinned_pow, N, alpha_c, p0=[5.0,0.3], maxfev=20000)

pred_free = free_pow(N, *popt_free)
pred_pinned = pinned_pow(N, *popt_pinned)

rms_free = rms(pred_free, alpha_c)
rms_pinned = rms(pred_pinned, alpha_c)

ll_free = log_likelihood(pred_free, alpha_c, sigma)
ll_pinned = log_likelihood(pred_pinned, alpha_c, sigma)

aic_free = aic(ll_free, 3, len(N))
aic_pinned = aic(ll_pinned, 2, len(N))
aicc_free = aicc(aic_free, 3, len(N))
aicc_pinned = aicc(aic_pinned, 2, len(N))

print(f"FREE fit: a={popt_free[0]:.4f}, c={popt_free[1]:.4f}, p={popt_free[2]:.4f}, RMS={rms_free:.5f}, AIC={aic_free:.3f}, AICc={aicc_free:.3f}")
print(f"PINNED fit: a=1.0, c={popt_pinned[0]:.4f}, p={popt_pinned[1]:.4f}, RMS={rms_pinned:.5f}, AIC={aic_pinned:.3f}, AICc={aicc_pinned:.3f}")

# Identifiability profile: fix intercept a, fit c,p
a_grid = np.linspace(0.8, 2.0, 121)
rms_profile = []
for a in a_grid:
    try:
        popt, _ = curve_fit(lambda N_, c, p: a + c*N_**(-p), N, alpha_c, p0=[5.0,0.3], maxfev=20000)
        rms_profile.append(rms(a + popt[0]*N**(-popt[1]), alpha_c))
    except RuntimeError:
        rms_profile.append(np.nan)
rms_profile = np.array(rms_profile)

# bootstrap under rounding noise
rng = np.random.default_rng(42)
nboot = 2000
a_boot = []
for _ in range(nboot):
    obs_noise = alpha_c + rng.normal(0, sigma, size=alpha_c.shape)
    try:
        popt, _ = curve_fit(free_pow, N, obs_noise, p0=[1.0,5.0,0.3], maxfev=20000)
        a_boot.append(popt[0])
    except RuntimeError:
        pass
a_boot = np.array(a_boot)
ci = np.percentile(a_boot, [2.5,97.5])
print(f"Bootstrapped 95% CI for free intercept (noise sigma={sigma}): [{ci[0]:.3f}, {ci[1]:.3f}]")

# save figure
fig, axes = plt.subplots(1,2,figsize=(12,5))
ax = axes[0]
ax.scatter(N, alpha_c, color='black', zorder=3, label='EMP-109 N-scan')
Nfine = np.logspace(1.8,4.0,200)
ax.plot(Nfine, free_pow(Nfine, *popt_free), label=f'free fit (a={popt_free[0]:.2f})')
ax.plot(Nfine, pinned_pow(Nfine, *popt_pinned), label='pinned fit (a=1.0)', linestyle='--')
ax.set_xscale('log')
ax.set_xlabel('N')
ax.set_ylabel(r'$\alpha_c(N)$')
ax.legend()
ax.set_title('Finite-size scaling fits')

ax = axes[1]
ax.plot(a_grid, rms_profile, lw=2)
ax.axvline(popt_free[0], color='C0', linestyle=':', label=f'free-fit a={popt_free[0]:.3f}')
ax.axvline(1.0, color='C1', linestyle=':', label='pinned a=1.0')
ax.axvline(1.55, color='C2', linestyle=':', label='plateau value 1.55')
ax.set_xlabel('fixed intercept a')
ax.set_ylabel('RMS after optimizing (c,p)')
ax.set_title('Identifiability profile')
ax.legend()
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/verify_emp132_aicc_replication.png', dpi=150)
print('Saved verify_emp132_aicc_replication.png')

# metrics json
import json
metrics = {
    'free': dict(a=popt_free[0], c=popt_free[1], p=popt_free[2], rms=rms_free, AIC=aic_free, AICc=aicc_free),
    'pinned': dict(a=1.0, c=popt_pinned[0], p=popt_pinned[1], rms=rms_pinned, AIC=aic_pinned, AICc=aicc_pinned),
    'delta_AIC': aic_pinned - aic_free,
    'delta_AICc': aicc_pinned - aicc_free,
    'akaike_weight_free': 1/(1+np.exp(0.5*(aicc_free-aicc_pinned))),
    'akaike_weight_pinned': 1/(1+np.exp(0.5*(aicc_pinned-aicc_free))),
    'bootstrap_a_95CI': ci.tolist(),
    'profile_flat_region': dict(min_a=float(a_grid[np.nanargmin(rms_profile)]), min_rms=float(np.nanmin(rms_profile))),
}
with open('../../shared_agora/artifacts/verify_emp132_aicc_replication.json','w') as f:
    json.dump(metrics, f, indent=2)
print(json.dumps(metrics, indent=2))
