"""
STRESS-TEST: Find a CML regime where TM > 0.5 AND SE > 0.5 simultaneously.
Need to defeat the temporal-spatial complementarity claim.
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
        hist, _ = np.histogram(snap.flatten(), bins=bins, range=(0.0, 1.0), density=False)
        p = hist / (hist.sum() + 1e-12)
        p = p[p > 0]
        if len(p) > 1:
            H = -np.sum(p * np.log2(p + 1e-12)) / np.log2(bins)
            entropies.append(H)
    return float(np.mean(entropies)) if entropies else 0

def run_cml_vectorized(L=40, T=1500, epsilon=0.5, mu=1.5, coupling=0.3,
                       delay=10, delay_strength=0.2, seed=42,
                       use_spatial_dynamics=True, mu_inhomogeneity=0.0):
    """Vectorized 2D CML with delayed feedback."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, (L, L))
    if mu_inhomogeneity > 0:
        # Spatial variation in mu to encourage spatial structure
        mu_field = mu + mu_inhomogeneity * rng.standard_normal((L, L))
    else:
        mu_field = mu * np.ones((L, L))
    history = [x.copy() for _ in range(delay)]
    snapshots = []
    timeseries = []

    for t in range(T):
        nb = (np.roll(x, 1, axis=0) + np.roll(x, -1, axis=0) +
              np.roll(x, 1, axis=1) + np.roll(x, -1, axis=1)) / 4
        delayed = history[t % delay]
        local = mu_field * x * (1 - x)
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

# Strategy: Use INHOMOGENEOUS mu to break translation symmetry, so each site
# can have independent dynamics with high temporal memory while the spatial
# pattern is rich (high spatial entropy).

print("="*70)
print("STRATEGY: Use INHOMOGENEOUS mu_field to break translation symmetry.")
print("Each site becomes an independent oscillator with memory,")
print("but spatial structure is preserved.")
print("="*70)

print(f"\n{'eps':<6}{'mu':<6}{'cpl':<6}{'dstr':<6}{'mu_inh':<8}{'TM':<8}{'SE':<8}{'TM*SE':<8}  Status")
print("-" * 80)

counterexamples = []
for eps in [0.2, 0.5, 0.8]:
    for dstr in [0.1, 0.3, 0.5, 0.7]:
        for mu_inh in [0.3, 0.6, 1.0]:
            for cpl in [0.05, 0.15, 0.3]:
                snaps, ts = run_cml_vectorized(
                    L=30, T=600, epsilon=eps, mu=1.5,
                    coupling=cpl, delay=10, delay_strength=dstr, seed=42,
                    use_spatial_dynamics=True, mu_inhomogeneity=mu_inh
                )
                tm = temp_memory(ts, max_lag=15)
                se = spatial_entropy(snaps)
                tmse = tm * se
                flag = ""
                if tm > 0 and se > 0 and tmse > 0.5:
                    flag = "** COUNTEREXAMPLE **"
                    counterexamples.append((eps, 1.5, cpl, dstr, mu_inh, tm, se, tmse))
                if flag:
                    print(f"{eps:<6}{1.5:<6}{cpl:<6}{dstr:<6}{mu_inh:<8}{tm:<8.3f}{se:<8.3f}{tmse:<8.3f}  {flag}")

print(f"\n*** COUNTEREXAMPLES FOUND (inhomogeneous mu): {len(counterexamples)} ***")
if counterexamples:
    for c in counterexamples[:5]:
        print(f"  eps={c[0]}, cpl={c[2]}, dstr={c[3]}, mu_inh={c[4]}, TM={c[5]:.3f}, SE={c[6]:.3f}, TM*SE={c[7]:.3f}")
    print("\n*** DOSSIER-073's TM*SE < 0.5 law FALSIFIED ***")
else:
    print("No counterexample in this regime.")