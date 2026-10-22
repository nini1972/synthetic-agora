import numpy as np

def run_cml_simulation(r, eps, L=128, T=600, trans=300, seed=42):
    np.random.seed(seed)
    x = np.random.uniform(0.1, 0.9, L)
    for _ in range(trans):
        fx = r * x * (1.0 - x)
        x = (1.0 - eps) * fx + (eps / 2.0) * (np.roll(fx, 1) + np.roll(fx, -1))
        
    frames = []
    for _ in range(T):
        fx = r * x * (1.0 - x)
        x = (1.0 - eps) * fx + (eps / 2.0) * (np.roll(fx, 1) + np.roll(fx, -1))
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
    
    # Parity index:
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
        ('Ordinary Frame Persistence', 3.9050, 0.1030),
        ('Resonant Phase-Memory', 3.8450, 0.1307),
        ('Resonant Phase-Memory', 3.8450, 0.1200),
        ('Fully Developed Spatio-Temporal Chaos', 4.0000, 0.2000),
    ]
    print('=== CML Motif-Frame Separation Empirical Verification (DOSSIER-006) ===')
    for label, r, eps in candidates:
        res = analyze_cml_regime(run_cml_simulation(r, eps))
        print(f"[{label}] (r={r:.4f}, eps={eps:.4f}): PeakFreq={res['peak_freq']:.4f}, Δ2={res['p2_diff']:.5f}, Parity={res['parity']:.4f}")
