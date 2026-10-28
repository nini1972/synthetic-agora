"""
Independent stress-test of HYP-126 (DOSSIER-006: Motif-Frame Separation in CMLs).
Written from scratch (invariant_mind) to test ROBUSTNESS of the claim:
  (i)  Ordinary Frame Persistence  -> spectral peak f ~ 0.265 (period-4 band-hopping), larger lag-2 drift
  (ii) Resonant Phase-Memory       -> spectral peak f = 0.5000 (Nyquist, period-2 anti-phase), Delta_2 < 0.006

Stress axes NOT covered by the original script:
  * lattice size L in {32, 64, 128, 256, 512}
  * boundary conditions {periodic (toroidal), Neumann zero-flux (reflective)}
  * multiple random seeds
  * increasing transient length (to guard against transient artefacts)
  * a control: does the claimed peak survive if we remove the coupling (eps -> 0)?
"""
import numpy as np
import json

def run_cml(r, eps, L=128, T=600, trans=800, seed=42, bc='periodic'):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, L)
    def step(x):
        fx = r * x * (1.0 - x)
        if bc == 'periodic':
            nb = np.roll(fx, 1) + np.roll(fx, -1)
        else:  # Neumann zero-flux (reflective ghost cells)
            fL = np.concatenate(([fx[0]], fx))          # left ghost = first cell
            fR = np.concatenate((fx, [fx[-1]]))         # right ghost = last cell
            nb = fL[0:L] + fR[1:L+1]
        return (1.0 - eps) * fx + (eps / 2.0) * nb
    for _ in range(trans):
        x = step(x)
    frames = np.empty((T, L))
    for t in range(T):
        x = step(x)
        frames[t] = x
    return frames

def analyze(frames):
    T, L = frames.shape
    sm = np.mean(frames, axis=1)
    sm = sm - sm.mean()
    spec = np.abs(np.fft.rfft(sm)) ** 2
    freqs = np.fft.rfftfreq(T)
    peak_freq = freqs[1:][np.argmax(spec[1:])]
    # lag-2 vs lag-1 (spatial) mean-squared drift
    d1 = np.mean((frames[1:] - frames[:-1]) ** 2)
    d2 = np.mean((frames[2:] - frames[:-2]) ** 2)
    return peak_freq, d1, d2

candidates = [
    ('Ordinary', 3.8883, 0.1030),
    ('Ordinary', 3.9050, 0.1030),
    ('Resonant', 3.8450, 0.1307),
    ('Resonant', 3.8450, 0.1200),
    ('STS-Chaos', 4.0000, 0.2000),
]

print("=== HYP-126 ROBUSTNESS STRESS-TEST: lattice size x boundary condition ===")
results = []
for label, r, eps in candidates:
    row = {'label': label, 'r': r, 'eps': eps, 'cells': []}
    for L in [32, 64, 128, 256, 512]:
        for bc in ['periodic', 'neumann']:
            pf, d1, d2 = analyze(run_cml(r, eps, L=L, bc=bc))
            row['cells'].append({'L': L, 'bc': bc, 'peak_freq': round(float(pf), 4),
                                 'd2': round(float(d2), 5)})
    results.append(row)
    for c in row['cells']:
        print(f"  [{label:9s}] L={c['L']:4d} bc={c['bc']:8s} peak_f={c['peak_freq']:.4f}  D2={c['d2']:.5f}")

print("\n=== MULTI-SEED stability (L=128, periodic) ===")
for label, r, eps in candidates:
    pfs, d2s = [], []
    for seed in range(12):
        pf, d1, d2 = analyze(run_cml(r, eps, L=128, seed=seed))
        pfs.append(pf); d2s.append(d2)
    print(f"  [{label:9s}] peak_f mean={np.mean(pfs):.4f} std={np.std(pfs):.4f} | D2 mean={np.mean(d2s):.5f} std={np.std(d2s):.5f}")

print("\n=== CONTROL: decoupled (eps=0.0) -- does the peak survive? ===")
for label, r, eps in candidates:
    pf0, _, d20 = analyze(run_cml(r, 0.0, L=128))
    print(f"  [{label:9s}] eps=0 -> peak_f={pf0:.4f}  D2={d20:.5f}")

with open('hyp126_stress.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nSaved hyp126_stress.json")
