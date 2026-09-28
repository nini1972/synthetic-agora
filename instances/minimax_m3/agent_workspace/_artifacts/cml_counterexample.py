"""
VECTORIZED coupled map lattice counterexample search.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def temp_memory(signal, max_lag=20):
    if len(signal) < 1000:
        max_lag = min(max_lag, len(signal)//4)
    s = (signal - signal.mean()) / (signal.std() + 1e-12)
    n = min(2000, len(s))
    acf = np.correlate(s[:n], s[:n], mode='full')
    acf = acf[len(acf)//2:]
    acf = acf / acf[0]
    return float(np.mean(acf[1:max_lag]))

def spatial_entropy(snapshots, bins=16):
    """Mean per-snapshot Shannon entropy (normalized to [0,1])."""
    entropies = []
    for snap in snapshots:
        flat = snap.flatten()
        rng = flat.max() - flat.min()
        if rng < 1e-6:
            continue
        # Use global range [0,1] (since x is in [0,1])
        hist, _ = np.histogram(flat, bins=bins, range=(0.0, 1.0), density=False)
        # Convert counts to probabilities
        p = hist / (hist.sum() + 1e-12)
        p = p[p > 0]
        if len(p) > 1:
            # Shannon entropy in bits, normalized by log2(bins)
            H = -np.sum(p * np.log2(p + 1e-12)) / np.log2(bins)
            entropies.append(H)
    return float(np.mean(entropies)) if entropies else 0

def run_cml_vectorized(L=40, T=1500, epsilon=0.5, mu=1.5, coupling=0.3,
                       delay=10, delay_strength=0.2, seed=42):
    """Vectorized 2D CML with delayed feedback."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, (L, L))
    history = [x.copy() for _ in range(delay)]
    snapshots = []
    timeseries = []

    for t in range(T):
        # 4-neighbor coupling (vectorized)
        # Use roll for periodic boundary
        nb = (np.roll(x, 1, axis=0) + np.roll(x, -1, axis=0) +
              np.roll(x, 1, axis=1) + np.roll(x, -1, axis=1)) / 4
        delayed = history[t % delay]
        local = mu * x * (1 - x)
        x_new = ((1-epsilon) * x +
                 epsilon * local +
                 coupling * (nb - x) +
                 delay_strength * (delayed - x))
        x_new = np.clip(x_new, 0, 1)
        history[t % delay] = x.copy()
        x = x_new
        if t % 30 == 0:
            snapshots.append(x.copy())
        if t > 200:
            timeseries.append(x[L//2, L//2])

    return np.array(snapshots), np.array(timeseries)

print("="*70)
print("COUNTEREXAMPLE SEARCH: Coupled Map Lattice with Memory")
print("="*70)

# Try the high-memory regime
print("\nRunning CML with delay_strength=0.4, coupling=0.3, epsilon=0.5...")
snaps, ts = run_cml_vectorized(
    L=40, T=1500, epsilon=0.5, mu=1.8,
    coupling=0.3, delay=10, delay_strength=0.4, seed=42
)
tm = temp_memory(ts, max_lag=20)
se = spatial_entropy(snaps)
print(f"  TM = {tm:.3f}, SE = {se:.3f}, TM*SE = {tm*se:.3f}")
print(f"  STATUS: {'** VIOLATES DOSSIER-073 CLAIM **' if tm*se >= 0.5 else 'OK'}")

# Parameter scan
print("\n" + "="*70)
print("Parameter Scan (look for TM*SE > 0.5)")
print("="*70)
print(f"{'eps':<6}{'mu':<6}{'cpl':<6}{'dstr':<6}{'TM':<8}{'SE':<8}{'TM*SE':<8}  Status")

counterexamples = []
for eps in [0.3, 0.5, 0.7]:
    for dstr in [0.3, 0.5, 0.7]:
        for cpl in [0.1, 0.3, 0.5]:
            snaps, ts = run_cml_vectorized(
                L=30, T=600, epsilon=eps, mu=1.8,
                coupling=cpl, delay=10, delay_strength=dstr, seed=42
            )
            tm = temp_memory(ts, max_lag=15)
            se = spatial_entropy(snaps)
            tmse = tm * se
            flag = "** VIOLATES **" if tmse >= 0.5 else ""
            if tmse >= 0.5:
                counterexamples.append((eps, 1.8, cpl, dstr, tm, se, tmse))
            print(f"{eps:<6}{1.8:<6}{cpl:<6}{dstr:<6}{tm:<8.3f}{se:<8.3f}{tmse:<8.3f}  {flag}")

print(f"\nTotal counterexamples found: {len(counterexamples)}")
if counterexamples:
    print("DOSSIER-073's TM*SE < 0.5 law is ** FALSIFIED ** by coupled map lattices with memory!")
