"""
Independent stress-test of HYP-126 (DOSSIER-006: Motif-Frame Separation in CMLs).
Written from scratch (Red-Team guild) to test ROBUSTNESS of the two claimed signatures
against INITIAL CONDITION DISPERSION and TEMPORAL HORIZON (factors not scanned in HYP-126).

CML: x_i(t+1) = (1-eps) f(x_i) + (eps/2)[f(x_{i-1}) + f(x_{i+1})],  f(x)=r x (1-x)

Signatures under test:
  (A) Ordinary Frame Persistence : spectral peak f ~ 0.265 (period-4 / band hopping)
  (B) Resonant Phase-Memory      : spectral peak f = 0.5 (Nyquist period-2 anti-phase)
"""
import numpy as np, json
from collections import defaultdict

def run_cml(r, eps, L, T, trans=800, sigma=0.05, seed=0, bc='periodic'):
    rng = np.random.default_rng(seed)
    x = np.clip(0.5 + rng.normal(0.0, sigma, L), 0.01, 0.99)
    def step(x):
        fx = r * x * (1.0 - x)
        if bc == 'periodic':
            nb = 0.5 * (np.roll(fx, 1) + np.roll(fx, -1))
        else:
            fL = np.concatenate(([fx[0]], fx)); fR = np.concatenate((fx, [fx[-1]]))
            nb = 0.5 * (fL[0:L] + fR[1:L+1])
        return (1.0 - eps) * fx + eps * nb
    for _ in range(trans):
        x = step(x)
    out = np.empty((T, L))
    for t in range(T):
        x = step(x); out[t] = x
    return out

def peak_freq_metric(frames):
    T = frames.shape[0]
    sm = np.mean(frames, axis=1); sm = sm - sm.mean()
    spec = np.abs(np.fft.rfft(sm))**2; freqs = np.fft.rfftfreq(T)
    return float(freqs[1:][np.argmax(spec[1:])])

def delta2_metric(frames):
    return float(np.mean((frames[2:] - frames[:-2])**2))

regimes = {
    'Ordinary': (3.8883, 0.1030),
    'Resonant': (3.8450, 0.1307),
    'STS-Chaos': (4.0000, 0.2000),
}
sigmas = [0.001, 0.01, 0.05, 0.20]   # IC dispersion (factor NOT scanned by HYP-126)
horizons = [100, 200, 400, 800]      # observation window length
L = 128; bc = 'periodic'

print("=== HYP-126 IC-dispersion x horizon stress test (L=128, periodic) ===")
print(f"{'regime':10s} {'sigma':>6s} {'T':>5s} | {'peak_f med':>10s} {'P(>0.45)':>9s} | {'D2 med':>9s} {'D2<0.006':>9s}")
rows = []
for name, (r, eps) in regimes.items():
    for sigma in sigmas:
        for T in horizons:
            pfs, d2s = [], []
            for s in range(12):
                fr = run_cml(r, eps, L, T, sigma=sigma, seed=s, bc=bc)
                pfs.append(peak_freq_metric(fr)); d2s.append(delta2_metric(fr))
            pfs = np.array(pfs); d2s = np.array(d2s)
            rec = {'regime': name, 'sigma': sigma, 'T': T,
                   'peak_f_med': float(np.median(pfs)),
                   'P_nyq': float(np.mean(pfs > 0.45)),
                   'd2_med': float(np.median(d2s)),
                   'P_d2': float(np.mean(d2s < 0.006))}
            rows.append(rec)
            print(f"{name:10s} {sigma:6.3f} {T:5d} | {rec['peak_f_med']:10.4f} {rec['P_nyq']:9.2f} | "
                  f"{rec['d2_med']:9.5f} {rec['P_d2']:9.2f}")

# Key question: does the Resonant signature survive BOTH high IC noise and short horizons?
res = [x for x in rows if x['regime'] == 'Resonant']
ord_ = [x for x in rows if x['regime'] == 'Ordinary']
print("\n=== Robustness verdict ===")
print(f"Resonant: min P(Nyquist)={min(x['P_nyq'] for x in res):.2f}, min P(d2<0.006)={min(x['P_d2'] for x in res):.2f}")
print(f"Ordinary: max P(Nyquist)={max(x['P_nyq'] for x in ord_):.2f}, max P(d2<0.006)={max(x['P_d2'] for x in ord_):.2f}")

json.dump(rows, open('cml_ic_horizon_stress.json', 'w'), indent=2)
print("\nSaved cml_ic_horizon_stress.json")
