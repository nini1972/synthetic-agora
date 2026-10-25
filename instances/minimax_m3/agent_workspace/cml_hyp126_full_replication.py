"""
HYP-126 INDEPENDENT REPLICATION -- DOSSIER-006 / CML motif-frame separation
==========================================================================
Three layers of analysis:
  A) Like-for-like replication of the 5 GEMINI test candidates, with
     MULTIPLE SEEDS (10 each) -- the original artifact used 1 seed.
  B) Bifurcation boundary map: sweep r in [3.83, 3.88], eps in [0.10, 0.15]
     to localize the period-2 lock window claimed by HYP-126.
  C) Adversarial diagnostics:
     (C1) Spatial FFT peak at k=N/2 (Nyquist wavenumber) -- the *actual*
          signature of anti-phase locking between adjacent sites.
     (C2) Spectral concentration ratio: power at f=0.5 / total power.
          A single delta at 0.5 has ratio->1; broadband chaos -> small.
     (C3) Size scaling: do the locked points stay locked at L=32, 64, 256?

CML convention: x^{n+1}_i = (1-eps) * f(x^n_i) + 0.5*eps*(f(x^n_{i-1}) + f(x^n_{i+1}))
                f(x) = r*x*(1-x),  periodic BC
"""
import numpy as np
import json, os, time
from numba import njit, prange


@njit(cache=True)
def cml_run(r, eps, L, T_trans, T_save, seed):
    np.random.seed(seed)
    x = np.empty(L)
    for i in range(L):
        x[i] = 0.1 + 0.8 * (np.random.random() % 1.0)
    # transient
    for _ in range(T_trans):
        fx = np.empty(L)
        for i in range(L):
            fx[i] = r * x[i] * (1.0 - x[i])
        for i in range(L):
            x[i] = (1.0 - eps) * fx[i] + 0.5 * eps * (
                fx[(i - 1) % L] + fx[(i + 1) % L])
    # save
    frames = np.empty((T_save, L))
    for t in range(T_save):
        fx = np.empty(L)
        for i in range(L):
            fx[i] = r * x[i] * (1.0 - x[i])
        for i in range(L):
            x[i] = (1.0 - eps) * fx[i] + 0.5 * eps * (
                fx[(i - 1) % L] + fx[(i + 1) % L])
        for i in range(L):
            frames[t, i] = x[i]
    return frames


def analyze(frames):
    T, L = frames.shape
    # ---- Temporal mean over space
    smean = frames.mean(axis=1)
    smean -= smean.mean()
    spec_t = np.abs(np.fft.rfft(smean))**2
    freqs = np.fft.rfftfreq(T)
    if spec_t[1:].max() > 0:
        peak_f_t = float(freqs[1 + np.argmax(spec_t[1:])])
    else:
        peak_f_t = 0.0
    # fractional power at f=0.5 (or its closest bin)
    target_idx = -1
    if T % 2 == 0:
        target_idx = T // 2  # Nyquist bin exactly
        frac_t_at_half = float(spec_t[target_idx] / spec_t.sum())
    else:
        idx = np.argmin(np.abs(freqs - 0.5))
        total = spec_t[1:].sum() + 1e-12
        frac_t_at_half = float(spec_t[idx] / total)
    # ---- Spatial FFT (mean over time, looking at k=N/2)
    sx = frames.mean(axis=0)
    sx -= sx.mean()
    spec_s = np.abs(np.fft.rfft(sx))**2
    if L % 2 == 0:
        spatial_anti = float(spec_s[L // 2] / spec_s.sum())
    else:
        spatial_anti = float('nan')
    # ---- Delta_2 (mean over n, i of |x^{n+2}_i - x^n_i|)
    d2 = float(np.mean(np.abs(frames[2:] - frames[:-2])))
    # ---- Parity (Gemini protocol, lags 1..16)
    sims = []
    for lag in range(1, 17):
        f0 = frames[:-lag]
        f1 = frames[lag:]
        f0c = f0 - f0.mean(axis=1, keepdims=True)
        f1c = f1 - f1.mean(axis=1, keepdims=True)
        num = (f0c * f1c).sum(axis=1)
        den = np.sqrt((f0c**2).sum(axis=1) * (f1c**2).sum(axis=1) + 1e-12)
        sims.append(float(np.mean(num / den)))
    m_even = float(np.mean([sims[l - 1] for l in range(2, 17, 2)]))
    m_odd = float(np.mean([sims[l - 1] for l in range(1, 17, 2)]))
    parity = max(0.0, m_even - m_odd)
    return dict(
        peak_f_t=peak_f_t, frac_t_half=frac_t_at_half,
        spatial_anti=spatial_anti, d2=d2,
        m_even=m_even, m_odd=m_odd, parity=parity,
    )


# ============================================================
# (A) Like-for-like, 10 seeds
# ============================================================
CANDIDATES = [
    ('ordinary', 3.8883, 0.1030),
    ('ordinary', 3.9050, 0.1030),
    ('ordinary', 3.9050, 0.1083),
    ('ordinary', 3.8717, 0.1030),
    ('resonant', 3.8450, 0.1307),
    ('resonant', 3.8450, 0.1200),
    ('chaos',    4.0000, 0.2000),
]


def replicate_candidate(label, r, eps, L=128, T_save=600, T_trans=1500, n_seeds=10):
    rows = []
    for s in range(n_seeds):
        frames = cml_run(r, eps, L, T_trans, T_save, seed=1000 + 17 * s)
        rows.append(analyze(frames))
    keys = rows[0].keys()
    mean = {k: float(np.mean([r[k] for r in rows])) for k in keys}
    std  = {k: float(np.std([r[k] for r in rows]))  for k in keys}
    return mean, std


if __name__ == '__main__':
    t0 = time.time()
    # Warm up jit
    print("[jit warm-up] ...")
    _ = cml_run(3.85, 0.12, 32, 100, 50, 0)
    print(f"[jit warm-up done, {time.time()-t0:.1f}s]")

    print("\n" + "=" * 96)
    print("(A) LIKE-FOR-LIKE REPLICATION -- 10 seeds, L=128, T_save=600, T_trans=1500")
    print("=" * 96)
    A_results = []
    print(f"{'label':>10} {'r':>7} {'eps':>6}  "
          f"{'peak_f_t':>10} {'frac@.5':>9} {'sp_anti':>9} "
          f"{'d2':>9} {'M_even':>8} {'M_odd':>8} {'Parity':>8}")
    print("-" * 96)
    for label, r, eps in CANDIDATES:
        m, s = replicate_candidate(label, r, eps)
        A_results.append(dict(label=label, r=r, eps=eps, mean=m, std=s))
        print(f"{label:>10} {r:>7.4f} {eps:>6.4f}  "
              f"{m['peak_f_t']:>10.4f} {m['frac_t_half']:>9.4f} "
              f"{m['spatial_anti']:>9.4f} {m['d2']:>9.5f} "
              f"{m['m_even']:>8.4f} {m['m_odd']:>8.4f} {m['parity']:>8.4f}")

    # ============================================================
    # (B) Bifurcation boundary map -- the *narrow* window claimed
    # ============================================================
    print("\n" + "=" * 96)
    print("(B) BIFURCATION BOUNDARY MAP -- r in [3.83, 3.88], eps in [0.10, 0.15]")
    print("=" * 96)
    rs = np.round(np.arange(3.83, 3.8801, 0.005), 4)
    eps_set = [0.10, 0.11, 0.12, 0.13, 0.14, 0.15]
    B_results = []
    header = "       "
    for e in eps_set:
        header += f"eps={e:.2f} "
    print(header)
    grid_d2 = np.full((len(rs), len(eps_set)), np.nan)
    grid_pf = np.full((len(rs), len(eps_set)), np.nan)
    grid_par = np.full((len(rs), len(eps_set)), np.nan)
    grid_f05 = np.full((len(rs), len(eps_set)), np.nan)
    grid_spa = np.full((len(rs), len(eps_set)), np.nan)
    for i, r in enumerate(rs):
        for j, e in enumerate(eps_set):
            m_list = []
            for s in range(3):
                frames = cml_run(float(r), float(e), 128, 1500, 600, seed=2000 + 31 * s)
                m_list.append(analyze(frames))
            m = {k: float(np.mean([x[k] for x in m_list])) for k in m_list[0]}
            grid_d2[i, j] = m['d2']
            grid_pf[i, j] = m['peak_f_t']
            grid_par[i, j] = m['parity']
            grid_f05[i, j] = m['frac_t_half']
            grid_spa[i, j] = m['spatial_anti']
        row = f"r={rs[i]:.4f} "
        for j in range(len(eps_set)):
            v = grid_pf[i, j]
            row += f"{v:>7.3f} "
        print(row)

    # Mark period-2 lock region (PeakFreq > 0.49 AND d2 < 0.01)
    lock_mask = (grid_pf > 0.49) & (grid_d2 < 0.01)
    n_lock = int(lock_mask.sum())
    print(f"\n>>> Period-2 lock cells (peak_f>0.49 AND d2<0.01): {n_lock} / {lock_mask.size}")
    if n_lock > 0:
        idx = np.argwhere(lock_mask)
        for i, j in idx:
            print(f"    r={rs[i]:.4f}, eps={eps_set[j]:.2f}: "
                  f"pf={grid_pf[i,j]:.4f}, d2={grid_d2[i,j]:.5f}, "
                  f"frac@.5={grid_f05[i,j]:.4f}, sp_anti={grid_spa[i,j]:.4f}, "
                  f"par={grid_par[i,j]:.4f}")

    # ============================================================
    # (C) Size scaling at locked (3.845, 0.12) vs ordinary (3.905, 0.103)
    # ============================================================
    print("\n" + "=" * 96)
    print("(C) SIZE SCALING -- L in {32, 64, 128, 256}")
    print("=" * 96)
    print(f"{'r':>7} {'eps':>6} {'L':>4}  "
          f"{'peak_f':>9} {'frac@.5':>9} {'sp_anti':>9} {'d2':>9} {'parity':>8}")
    print("-" * 96)
    for label, r, eps in [('resonant', 3.8450, 0.1200),
                          ('ordinary', 3.9050, 0.1030),
                          ('chaos',    4.0000, 0.2000)]:
        for L in [32, 64, 128, 256]:
            m_list = []
            for s in range(5):
                frames = cml_run(r, eps, L, 2000, 800, seed=3000 + s)
                m_list.append(analyze(frames))
            m = {k: float(np.mean([x[k] for x in m_list])) for k in m_list[0]}
            print(f"{r:>7.4f} {eps:>6.4f} {L:>4}  "
                  f"{m['peak_f_t']:>9.4f} {m['frac_t_half']:>9.4f} "
                  f"{m['spatial_anti']:>9.4f} {m['d2']:>9.5f} {m['parity']:>8.4f}")

    elapsed = time.time() - t0
    print(f"\n[Total elapsed: {elapsed:.1f}s]")

    # Save full grid
    out = dict(
        A=A_results,
        B=dict(rs=rs.tolist(), eps=eps_set,
               d2=grid_d2.tolist(), peak_f=grid_pf.tolist(),
               parity=grid_par.tolist(), frac_at_half=grid_f05.tolist(),
               spatial_anti=grid_spa.tolist()),
    )
    os.makedirs('world_c_results', exist_ok=True)
    with open('world_c_results/hyp126_full_replication.json', 'w') as fh:
        json.dump(out, fh, indent=2)
    print("Saved -> world_c_results/hyp126_full_replication.json")
