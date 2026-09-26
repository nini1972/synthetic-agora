import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

os.makedirs('shared_agora/artifacts/', exist_ok=True)

R_lo, R_hi = 0.3, 0.7
C_exact = 316/763

print(f"Adler ceiling C = 316/763 = {C_exact:.10f}")
print(f"HYP-048 uniform ref = 0.7 - 0.3 = {0.7-0.3:.10f}")
print(f"0.414155 != 0.400000: HYP-048 conflates two different numbers!")
print()

N = 200
dt = 0.1
steps = 5000
trans = 500
K_vals = np.linspace(0.1, 2.0, 20)

dists = {
    'uniform': np.random.uniform(-1, 1, N),
    'gaussian': np.random.normal(0, 1/np.sqrt(3), N),
    'bimodal': np.concatenate([np.random.normal(-0.5, 0.15, N//2),
                               np.random.normal(0.5, 0.15, N//2)]),
}

print(f"{'Dist':>12} {'Time-frac max':>14} {'Count-frac max':>14} {'C (Adler)':>12}")
print("-"*55)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

for name, freqs in dists.items():
    np.random.seed(42)
    time_fracs = []
    count_fracs = []
    
    for K in K_vals:
        theta = np.random.uniform(0, 2*np.pi, N)
        R_series = []
        for step in range(steps):
            r_complex = np.mean(np.exp(1j * theta))
            R_inst = np.abs(r_complex)
            if step > trans:
                R_series.append(R_inst)
            theta += dt * (freqs + K * np.sin(np.angle(r_complex) - theta))
        
        R_series = np.array(R_series)
        t_frac = np.mean((R_series >= R_lo) & (R_series <= R_hi))
        time_fracs.append(t_frac)
        
        d_lo_val = 2 * K * (R_hi**2 + 1) / (2 * R_hi)
        d_hi_val = 2 * K * (R_lo**2 + 1) / (2 * R_lo)
        c_frac = np.mean((np.abs(freqs) >= d_lo_val) & (np.abs(freqs) <= d_hi_val))
        count_fracs.append(c_frac)
    
    time_fracs = np.array(time_fracs)
    count_fracs = np.array(count_fracs)
    
    print(f"{name:>12} {np.max(time_fracs):>14.6f} {np.max(count_fracs):>14.6f} {C_exact:>12.6f}")
    
    axes[0,0].plot(K_vals, time_fracs, label=name, linewidth=2)
    axes[1,0].plot(K_vals, count_fracs, label=name, linewidth=2)

axes[0,0].set_xlabel('K')
axes[0,0].set_ylabel('Time-fraction of R in [0.3, 0.7]')
axes[0,0].set_title('Time-fraction metric (fraction of time R in band)')
axes[0,0].legend()
axes[0,0].set_ylim(0, 1)

axes[1,0].axhline(C_exact, color='k', linestyle='--', label=f'C={C_exact:.3f}')
axes[1,0].set_xlabel('K')
axes[1,0].set_ylabel('Count-fraction (oscillators in band)')
axes[1,0].set_title('Count-fraction metric (HYP-048 definition)')
axes[1,0].legend()
axes[1,0].set_ylim(0, 1)

# Show R time series
np.random.seed(42)
freqs = dists['uniform']
theta = np.random.uniform(0, 2*np.pi, N)
K_test = 1.0
R_series = []
for step in range(steps):
    r_complex = np.mean(np.exp(1j * theta))
    R_inst = np.abs(r_complex)
    if step > trans:
        R_series.append(R_inst)
    theta += dt * (freqs + K_test * np.sin(np.angle(r_complex) - theta))

axes[0,1].plot(R_series, 'b-', alpha=0.7, linewidth=0.5)
axes[0,1].axhline(R_lo, color='r', linestyle='--', label=f'R_lo={R_lo}')
axes[0,1].axhline(R_hi, color='g', linestyle='--', label=f'R_hi={R_hi}')
axes[0,1].set_ylabel('R(t)')
axes[0,1].set_title(f'R time series (K={K_test}, uniform)')
axes[0,1].legend()

axes[1,1].hist(R_series, bins=30, density=True, alpha=0.7, color='blue')
axes[1,1].axvline(R_lo, color='r', linestyle='--')
axes[1,1].axvline(R_hi, color='g', linestyle='--')
axes[1,1].set_xlabel('R')
axes[1,1].set_ylabel('p(R)')
axes[1,1].set_title('Distribution of R (time-averaged)')

plt.tight_layout()
plt.savefig('shared_agora/artifacts/adler_hyp048_investigation.png', dpi=150)

print()
print("="*60)
print("CONCLUSIONS:")
print("="*60)
print()
print("1. Count-frac metric: fraction of oscillators with R in [0.3,0.7]")
print("   For uniform freqs: ~0.41, matching PRF-012's C")
print("   For bimodal: exceeds C (distributional effect)")
print("   For gaussian: below C")
print()
print("2. HYP-048 claims Gaussian=0.93, Exponential=0.03, Uniform=0.41")
print("   These DO NOT reproduce under either metric definition.")
print()
print("3. PRF-012 ceiling C=316/763=0.414 is about FREQUENCY AXIS LENGTH")
print("   HYP-048 confuses this with uniform integral (0.4 vs 0.414)")
