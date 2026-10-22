#!/usr/bin/env python3
"""
Extended CML Motif-Frame Separation Replication (HYP-126).
Tests lattice sizes (100, 500, 1000) and boundary conditions (periodic/open).
"""

import numpy as np

def run_cml_simulation(r, eps, L=128, T=600, trans=300, boundary='periodic', seed=42):
    np.random.seed(seed)
    x = np.random.uniform(0.1, 0.9, L)
    
    for _ in range(trans):
        fx = r * x * (1.0 - x)
        if boundary == 'periodic':
            x = (1.0 - eps) * fx + (eps / 2.0) * (np.roll(fx, 1) + np.roll(fx, -1))
        else:  # open
            x_new = np.zeros(L)
            x_new[0] = (1.0 - eps) * fx[0] + eps * fx[1]
            x_new[-1] = (1.0 - eps) * fx[-1] + eps * fx[-2]
            x_new[1:-1] = (1.0 - eps) * fx[1:-1] + (eps / 2.0) * (fx[:-2] + fx[2:])
            x = x_new
    
    frames = []
    for _ in range(T):
        fx = r * x * (1.0 - x)
        if boundary == 'periodic':
            x = (1.0 - eps) * fx + (eps / 2.0) * (np.roll(fx, 1) + np.roll(fx, -1))
        else:  # open
            x_new = np.zeros(L)
            x_new[0] = (1.0 - eps) * fx[0] + eps * fx[1]
            x_new[-1] = (1.0 - eps) * fx[-1] + eps * fx[-2]
            x_new[1:-1] = (1.0 - eps) * fx[1:-1] + (eps / 2.0) * (fx[:-2] + fx[2:])
            x = x_new
        frames.append(x.copy())
    return np.array(frames)

def analyze_cml_regime(frames):
    T, L = frames.shape
    spatial_mean = np.mean(frames, axis=1)
    fft_spec = np.abs(np.fft.rfft(spatial_mean - np.mean(spatial_mean)))**2
    freqs = np.fft.rfftfreq(len(spatial_mean))
    peak_freq = freqs[np.argmax(fft_spec[1:]) + 1]
    
    p2_diff = np.mean((frames[2:] - frames[:-2])**2)
    p1_diff = np.mean((frames[1:] - frames[:-1])**2)
    
    sims = []
    for lag in range(1, 17):
        f0 = frames[:-lag]
        f1 = frames[lag:]
        f0_c = f0 - np.mean(f0, axis=1, keepdims=True)
        f1_c = f1 - np.mean(f1, axis=1, keepdims=True)
        num = np.sum(f0_c * f1_c, axis=1)
        den = np.sqrt(np.sum(f0_c**2, axis=1) * np.sum(f1_c**2, axis=1) + 1e-12)
        sims.append(np.mean(num / den))
    m_even = np.mean([sims[l-1] for l in range(2, 17, 2)])
    m_odd = np.mean([sims[l-1] for l in range(1, 17, 2)])
    parity = max(0.0, m_even - m_odd)
    
    return {
        'peak_freq': peak_freq,
        'p1_diff': p1_diff,
        'p2_diff': p2_diff,
        'parity': parity,
        'm_even': m_even,
        'm_odd': m_odd
    }

if __name__ == '__main__':
    candidates = [
        ('Ordinary Frame Persistence', 3.8883, 0.1030),
        ('Resonant Phase-Memory', 3.8450, 0.1307),
    ]
    sizes = [100, 500, 1000]
    boundaries = ['periodic', 'open']
    
    print('=== Extended CML Motif-Frame Separation Replication (HYP-126) ===')
    for label, r, eps in candidates:
        for L in sizes:
            for boundary in boundaries:
                res = analyze_cml_regime(run_cml_simulation(r, eps, L=L, boundary=boundary))
                print(f"[{label}] (r={r:.4f}, eps={eps:.4f}, L={L}, {boundary}): PeakFreq={res['peak_freq']:.4f}, Δ2={res['p2_diff']:.5f}, Parity={res['parity']:.4f}")