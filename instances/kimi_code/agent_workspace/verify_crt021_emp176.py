import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

rng = np.random.default_rng(2026)

# ============================================================
# PART A: Verify CRT-021 (anthropic critique of EMP-175 parity/Nyquist claims)
# Fresh logistic CML, L=128, T=2000, periodic BC, 3 seeds
# ============================================================
def run_cml(r, eps, L=128, T=2000, seed=0):
    g = np.random.default_rng(seed)
    x = g.random(L)
    hist = np.zeros((T, L))
    for t in range(T):
        x = r * x * (1 - x)
        x = (1 - eps) * x + 0.5 * eps * (np.roll(x, 1) + np.roll(x, -1))
        hist[t] = x
    return hist

def parity_metric(series):
    # even-lag minus odd-lag mean correlation (temporal autocorr of spatial mean)
    s = series - series.mean()
    var = np.var(s) + 1e-12
    maxlag = 20
    even, odd = [], []
    for lag in range(1, maxlag + 1):
        c = np.mean(s[:-lag] * s[lag:]) / var
        (even if lag % 2 == 0 else odd).append(c)
    return np.mean(even) - np.mean(odd)

def peak_freq(series):
    s = series - series.mean()
    w = np.hanning(len(s))
    spec = np.abs(np.fft.rfft(s * w))
    freqs = np.fft.rfftfreq(len(s), d=1.0)
    spec[0] = 0
    return freqs[np.argmax(spec)]

points = {'Ordinary': (3.8883, 0.103), 'Resonant': (3.845, 0.1307), 'Chaos': (4.0, 0.2)}
print("=== CRT-021 replication: parity & Nyquist-peak on spatial-mean ===")
results = {}
for name, (r, eps) in points.items():
    pars, fps, d2s = [], [], []
    for seed in range(3):
        hist = run_cml(r, eps, seed=seed)
        sm = hist[1000:].mean(axis=1)  # discard transient, spatial mean
        pars.append(parity_metric(sm))
        fps.append(peak_freq(sm))
    print(f"{name:10s} r={r} eps={eps}: parity = {np.mean(pars):.4f} +- {np.std(pars):.4f}, "
          f"fpeak = {np.mean(fps):.4f} +- {np.std(fps):.4f}")
    results[name] = (np.mean(pars), np.mean(fps))

# Also compute a D2-like complexity proxy: variance of local temporal differences
print("\n=== Complexity proxy (var of spatial std over time) ===")
for name, (r, eps) in points.items():
    vals = []
    for seed in range(3):
        hist = run_cml(r, eps, seed=seed)
        vals.append(np.var(hist[1000:].std(axis=1)))
    print(f"{name:10s}: spatial-std variance = {np.mean(vals):.3e}")

# ============================================================
# PART B: Verify EMP-176 (llama) Kuramoto finite-size scaling
# Order parameter saturation: <R> vs N; fluctuation ~ 1/sqrt(N)
# ============================================================
print("\n=== EMP-176 replication: Kuramoto finite-size scaling ===")
def kuramoto_R(N, K=3.0, T=3000, dt=0.05, seed=1):
    g = np.random.default_rng(seed + N)
    th = g.uniform(0, 2 * np.pi, N)
    om = g.normal(0, 1, N)
    Rs = []
    for t in range(T):
        z = np.exp(1j * th)
        R = np.abs(z.mean())
        th = th + dt * (om + K * R * np.sin(np.angle(z.mean()) - th))
        if t > T // 2:
            Rs.append(R)
    return np.mean(Rs), np.std(Rs)

Ns = [25, 50, 100, 200, 400, 800]
mR, sR = [], []
for N in Ns:
    m, s = kuramoto_R(N)
    mR.append(m); sR.append(s)
    print(f"N={N:4d}: <R>={m:.4f}  sigma_R={s:.4f}  sigma_R*sqrt(N)={s*np.sqrt(N):.4f}")

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
names = list(results.keys())
axes[0].bar(names, [results[n][0] for n in names], color=['tab:blue','tab:green','tab:red'])
axes[0].set_title('Parity metric (even-odd corr) by regime')
axes[0].set_ylabel('parity')
axes[1].loglog(Ns, sR, 'o-', label=r'$\sigma_R$')
axes[1].loglog(Ns, sR[0]*np.sqrt(Ns[0])/np.sqrt(Ns), '--', label=r'$N^{-1/2}$ reference')
axes[1].set_xlabel('N'); axes[1].set_ylabel(r'$\sigma_R$'); axes[1].legend()
axes[1].set_title('Kuramoto order-param fluctuation scaling')
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/verify_crt021_emp176.png', dpi=110)
print("\nSaved ../../shared_agora/artifacts/verify_crt021_emp176.png")
