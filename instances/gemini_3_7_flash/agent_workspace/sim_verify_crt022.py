import numpy as np

# We test CML: x_{i, t+1} = (1 - eps)*f(x_{i,t}) + eps/2 * (f(x_{i-1,t}) + f(x_{i+1,t}))
# with f(x) = r * x * (1 - x)
# Test regimes:
# 1) Ordinary: r=3.8, eps=0.1
# 2) Resonant: r=3.8, eps=0.35 (or similar parameters from HYP-126)
# 3) STS-Chaos: r=4.0, eps=0.2

def simulate_cml(r, eps, L=128, T=1000, sigma=0.1, seed=42):
    rng = np.random.RandomState(seed)
    x = 0.5 + rng.normal(0, sigma, size=L)
    x = np.clip(x, 0.01, 0.99)
    
    # Burn-in
    for _ in range(500):
        fx = r * x * (1.0 - x)
        x = (1.0 - eps) * fx + 0.5 * eps * (np.roll(fx, 1) + np.roll(fx, -1))
        
    history = np.zeros((T, L))
    for t in range(T):
        fx = r * x * (1.0 - x)
        x = (1.0 - eps) * fx + 0.5 * eps * (np.roll(fx, 1) + np.roll(fx, -1))
        history[t] = x
        
    # Temporal power spectrum for each spatial site
    fft_vals = np.abs(np.fft.rfft(history, axis=0))**2
    freqs = np.fft.rfftfreq(T)
    # Exclude DC (f=0)
    mean_psd = np.mean(fft_vals[1:], axis=1)
    peak_f = freqs[1:][np.argmax(mean_psd)]
    
    # Lag-2 drift: Delta_2 = < (x_{t+2} - x_t)^2 >
    delta_2 = np.mean((history[2:] - history[:-2])**2)
    
    return peak_f, delta_2

print("Running test across regimes and IC dispersions...")
for regime_name, r, eps in [("Ordinary", 3.8, 0.1), ("Resonant", 3.8, 0.35), ("STS-Chaos", 4.0, 0.2)]:
    for sigma in [0.001, 0.01, 0.1]:
        peak_fs = []
        d2s = []
        for seed in range(5):
            pf, d2 = simulate_cml(r, eps, L=128, T=1000, sigma=sigma, seed=seed)
            peak_fs.append(pf)
            d2s.append(d2)
        print(f"Regime {regime_name:10s} | sigma={sigma:5.3f} | peak_f={np.mean(peak_fs):.3f} +/- {np.std(peak_fs):.3f} | Delta_2={np.mean(d2s):.5f}")
