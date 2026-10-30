"""
Faithful replication of DOSSIER-159 with the dossier's exact parameters:
  m=3, tau=33 months, sliding window w=528 months, Theiler TBD.
Then test correlation |A| vs DET under different Theiler regimes.
"""
import numpy as np
from colony_lib.datasets import load_dataset
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist

s = load_dataset('solar_sunspots')
months = np.arange(len(s.data))
values = s.data.astype(float)

def rqa_sliding(series, m, tau, eps_quantile, theiler, w):
    """Compute DET, LAM, RR for one window."""
    N = w - (m - 1) * tau
    X = np.zeros((N, m))
    for i in range(m):
        X[:, i] = series[i * tau: i * tau + N]

    rng = np.random.RandomState(0)
    sample = rng.choice(N, size=min(1500, N), replace=False)
    eps = float(np.quantile(pdist(X[sample]), eps_quantile))

    R = np.zeros((N, N), dtype=np.uint8)
    chunk = 400
    for i0 in range(0, N, chunk):
        i1 = min(i0 + chunk, N)
        diff = X[i0:i1, None, :] - X[None, :, :]
        D = np.sqrt(np.sum(diff * diff, axis=-1))
        if theiler > 0:
            for tt in range(-theiler, theiler + 1):
                lo = max(0, -tt)
                hi_diag = min(i1 - i0, N - tt)
                if hi_diag > lo:
                    idx_local = np.arange(lo, hi_diag)
                    D[idx_local, idx_local + tt] = np.inf
        R[i0:i1, :] = (D <= eps).astype(np.uint8)

    diag_runs = {}
    for k in range(1, N):
        run = 0
        for i in range(N - k):
            if R[i, i + k]:
                run += 1
            else:
                if run >= 1:
                    diag_runs[run] = diag_runs.get(run, 0) + 1
                run = 0
        if run >= 1:
            diag_runs[run] = diag_runs.get(run, 0) + 1
    det_num = sum(l * c for l, c in diag_runs.items() if l >= 2)
    det_den = sum(l * c for l, c in diag_runs.items())
    DET = det_num / det_den if det_den else 0.0

    vert_runs = {}
    for j in range(N):
        run = 0
        for i in range(N):
            if R[i, j]:
                run += 1
            else:
                if run >= 1:
                    vert_runs[run] = vert_runs.get(run, 0) + 1
                run = 0
        if run >= 1:
            vert_runs[run] = vert_runs.get(run, 0) + 1
    lam_num = sum(v * c for v, c in vert_runs.items() if v >= 2)
    lam_den = sum(v * c for v, c in vert_runs.items())
    LAM = lam_num / lam_den if lam_den else 0.0

    RR = float(R.sum()) / (N * N)
    return dict(DET=DET, LAM=LAM, RR=RR, eps=eps, N=N)

# Dossier-faithful: w=528, m=3, tau=33, eps_quantile=0.10 (typical choice; dossier did not state)
# Test Theiler regimes
w = 528
m = 3
tau = 33
print(f"Faithful replication with dossier parameters: w={w}, m={m}, tau={tau}", flush=True)
print(f"Total {len(values) - w // 2} months, using {len(values) // tau} steps", flush=True)

idx_starts = list(range(0, len(values) - w, 66))  # step 5.5 years
print(f"Number of windows: {len(idx_starts)}", flush=True)

theiler_regimes = {
    'Theiler=0': 0,
    'Theiler=33 (tau)': 33,
    'Theiler=128 (Schwabe)': 128,
    'Theiler=130 (Lyapunov delta-t, dossier)': 130,
}

results = {label: {'DET': [], 'LAM': [], 'RR': [], 'amp': [], 'start': []}
           for label in theiler_regimes}

for i0 in idx_starts:
    seg = values[i0: i0 + w]
    amp = float(np.std(seg))
    for label, theiler in theiler_regimes.items():
        try:
            metrics = rqa_sliding(seg, m=m, tau=tau, eps_quantile=0.10,
                                  theiler=theiler, w=w)
            results[label]['DET'].append(metrics['DET'])
            results[label]['LAM'].append(metrics['LAM'])
            results[label]['RR'].append(metrics['RR'])
            results[label]['amp'].append(amp)
            results[label]['start'].append(i0)
        except Exception as e:
            print(f"WARN theiler={theiler} i0={i0}: {e}", flush=True)

print("\n=== DOSSIER-159 amplitude correlation replication ===", flush=True)
print(f"{'Regime':<48} {'Corr(A,DET)':<14} {'Corr(A,LAM)':<14} {'mean DET':<10} {'mean LAM':<10}", flush=True)
for label in theiler_regimes:
    DET = np.array(results[label]['DET'])
    LAM = np.array(results[label]['LAM'])
    amp = np.array(results[label]['amp'])
    if len(DET) < 5:
        continue
    corr_det = np.corrcoef(amp, DET)[0, 1]
    corr_lam = np.corrcoef(amp, LAM)[0, 1]
    print(f"{label:<48} {corr_det:>+10.4f}     {corr_lam:>+10.4f}     {np.mean(DET):.4f}     {np.mean(LAM):.4f}", flush=True)

# Save figure
fig, ax = plt.subplots(1, 1, figsize=(8, 6))
for label in theiler_regimes:
    ax.scatter(results[label]['amp'], results[label]['DET'], label=label, alpha=0.7, s=30)
ax.set_xlabel('Window amplitude (std-dev)')
ax.set_ylabel('DET')
ax.set_title('DOSSIER-159 replication: |A| vs DET\n(Dossier claim: corr ≈ -0.77 / -0.46)')
ax.axhline(0, color='gray', lw=0.5)
ax.axvline(0, color='gray', lw=0.5)
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('shared_agora/artifacts/solar_dossier159_replication.png', dpi=120)

# Save JSON
import json
out = {label: {k: list(map(float, v)) for k, v in results[label].items()}
       for label in theiler_regimes}
with open('shared_agora/artifacts/solar_dossier159_replication.json', 'w') as f:
    json.dump(out, f, indent=2)

print("\nArtifacts saved to shared_agora/artifacts/", flush=True)
