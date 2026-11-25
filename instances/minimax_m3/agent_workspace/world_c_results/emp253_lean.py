"""
EMP-253/EMP-238 Lean Synthetic Ground-Truth Stress Test (minimax_m3)
Goal: Run within CI reconciliation window (~400s).

3 systems with KNOWN complexity structure x 5 bands x 2 protocols = 30 RQA runs.
Each system has independent ground truth:
  - Lorenz63 (chaotic, deterministic strange attractor, broadband)
  - AR(1) linear (linear stochastic, low complexity)
  - White Gaussian noise (null)

For each (system, band) pair, generate a 4096-pt signal, apply butterworth bandpass,
then run RQA under TWO protocols:
  - FIXED: epsilon = 0.3 of normalized signal std (EMP-253 style saturation protocol)
  - MATCHED: epsilon = percentile such that RR ~ 0.05 (EMP-191 sparse-protocol)

Output: rho(ENT, freq) under each protocol, FT-surrogate gap (EMP-254), and
sign-flip determination per system.

Key predictions:
  - Lorenz (real chaos): MATCHED rho should be strongly negative (real structure);
    FIXED rho can flip sign at dense bands due to saturation. FT gap > 0 (real).
  - AR(1) (linear): MATCHED rho ~ 0; FIXED rho ~ 0; FT gap ~ 0.
  - White noise (null): MATCHED rho ~ 0; FIXED rho ~ 0; FT gap ~ 0.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics
from colony_lib.persistence import StageTracker

np.random.seed(42)
FS = 128.0  # Match neural_eeg sampling rate
T = 4096    # Smaller than 10k for speed but enough for stable RQA
BANDS = {
    'Delta': (0.5, 4.0),
    'Theta': (4.0, 8.0),
    'Alpha': (8.0, 13.0),
    'Beta':  (13.0, 30.0),
    'Gamma': (30.0, 50.0),
}

def lorenz63(N, dt=0.01, s=10.0, r=28.0, b=2.667):
    x = np.empty(N); y = np.empty(N); z = np.empty(N)
    x[0]=1.0; y[0]=1.0; z[0]=1.0
    for i in range(1, N):
        x[i]=x[i-1]+dt*s*(y[i-1]-x[i-1])
        y[i]=y[i-1]+dt*(x[i-1]*(r-z[i-1])-y[i-1])
        z[i]=z[i-1]+dt*(x[i-1]*y[i-1]-b*z[i-1])
    # resample to FS via linear interp on time index
    t_old = np.arange(N)*dt
    t_new = np.linspace(0, t_old[-1], int(T))
    from scipy.interpolate import interp1d
    f = interp1d(t_old, x, kind='cubic')
    return f(t_new)

def ar1(N, phi=0.7):
    x = np.zeros(N)
    e = np.random.randn(N)
    for i in range(1, N):
        x[i] = phi*x[i-1] + e[i]
    return x

def white(N):
    return np.random.randn(N)

def bandpass(x, lo, hi, fs, order=4):
    if lo <= 0: lo = 0.5
    nyq = fs/2
    if hi >= nyq: hi = nyq - 1
    b, a = butter(order, [lo/nyq, hi/nyq], btype='band')
    return filtfilt(b, a, x)

def surrogate_ft(x, n_iter=50):
    """Fourier transform surrogate (Theiler et al. 1992)."""
    from numpy.fft import fft, ifft
    X = fft(x)
    phases = np.angle(X)
    amps = np.abs(X)
    # Randomize phases
    new_phases = np.random.permutation(phases[1:len(x)//2])
    new_phases = np.concatenate([[0], new_phases, [0], -new_phases[::-1]])
    return np.real(ifft(amps * np.exp(1j*new_phases)))

def run_rqa(signal, protocol='fixed', target_rr=0.05, m=3, tau=2):
    x = (signal - signal.mean()) / (signal.std() + 1e-12)
    emb = takens_embedding(x, m=m, tau=tau)
    if protocol == 'fixed':
        # FIXED EPSILON: 0.3 * std of embedded points (EMP-253 saturation protocol)
        eps = 0.3 * np.std(emb)
    else:
        # MATCHED-RR: pick percentile for target RR
        from scipy.spatial.distance import pdist
        D = pdist(emb[:500, :])  # subsample for speed
        eps = np.percentile(D, target_rr*100)
    R = recurrence_matrix(emb, epsilon=eps)
    return compute_rqa_metrics(R)

# === MAIN ===
tracker = StageTracker('emp253_lean_synthetic')
results = {}

systems = {
    'Lorenz63_chaotic': lorenz63(int(T/dt_l := 50000) if False else 50000),  # generate long
    'AR1_linear': ar1(50000),
    'White_noise': white(50000),
}
# Actually let's generate exactly 50000 then resample to T at FS
def make_signal(name):
    if name == 'Lorenz63_chaotic':
        # use 200000 step integration, then resample
        s = lorenz63(200000)
    elif name == 'AR1_linear':
        s = ar1(200000)
    else:
        s = white(200000)
    # Resample to T points at FS
    from scipy.interpolate import interp1d
    f = interp1d(np.arange(len(s))/200000.0*len(s)/FS, s, kind='linear')
    t_new = np.linspace(0, len(s)/FS, T)
    return f(t_new)

systems = {name: make_signal(name) for name in ['Lorenz63_chaotic', 'AR1_linear', 'White_noise']}

rows = []
for sys_name, sig in systems.items():
    band_results = {'fixed': {}, 'matched': {}}
    for band_name, (lo, hi) in BANDS.items():
        try:
            bp = bandpass(sig, lo, hi, FS)
        except Exception as e:
            print(f"Bandpass failed {sys_name}/{band_name}: {e}")
            continue
        if bp.std() < 1e-6:
            continue
        # FIXED protocol
        m_fixed = run_rqa(bp, 'fixed')
        # MATCHED protocol
        m_match = run_rqa(bp, 'matched', target_rr=0.05)
        # FT surrogate gap (EMP-254)
        surr = surrogate_ft(bp, n_iter=30)
        m_surr = run_rqa(surr, 'matched', target_rr=0.05)
        gap = m_match['ENT'] - m_surr['ENT']
        band_results['fixed'][band_name] = m_fixed
        band_results['matched'][band_name] = m_match
        rows.append({
            'system': sys_name,
            'band': band_name,
            'center_freq': (lo+hi)/2,
            'fixed_ENT': m_fixed['ENT'],
            'fixed_RR': m_fixed['RR'],
            'matched_ENT': m_match['ENT'],
            'matched_RR': m_match['RR'],
            'surrogate_ENT': m_surr['ENT'],
            'ft_gap': gap,
        })
    results[sys_name] = band_results

# === ANALYSIS ===
from scipy.stats import spearmanr
analysis = {}
for sys_name in systems:
    rows_s = [r for r in rows if r['system'] == sys_name]
    freqs = [r['center_freq'] for r in rows_s]
    fENT = [r['fixed_ENT'] for r in rows_s]
    mENT = [r['matched_ENT'] for r in rows_s]
    gaps = [r['ft_gap'] for r in rows_s]
    rho_f, p_f = spearmanr(freqs, fENT)
    rho_m, p_m = spearmanr(freqs, mENT)
    rho_g, p_g = spearmanr(freqs, gaps)
    analysis[sys_name] = {
        'rho_fixed_ENT_freq': rho_f, 'p_fixed': p_f,
        'rho_matched_ENT_freq': rho_m, 'p_matched': p_m,
        'rho_gap_freq': rho_g, 'p_gap': p_g,
        'mean_ft_gap': float(np.mean(gaps)),
        'sign_flip': bool(rho_f * rho_m < 0),
    }

# === SAVE ARTIFACTS ===
import json
with open('emp253_lean_results.json', 'w') as f:
    json.dump({
        'rows': rows,
        'analysis': analysis,
        'config': {'T': T, 'FS': FS, 'bands': BANDS, 'protocols': ['fixed_eps_0.3', 'matched_rr_0.05']},
    }, f, indent=2)

tracker.save_stage('final', {'rows': rows, 'analysis': analysis})

# === FIGURE ===
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
sys_names = list(systems.keys())
colors = {'Lorenz63_chaotic': 'C0', 'AR1_linear': 'C1', 'White_noise': 'C2'}
markers = {'fixed': 'o', 'matched': 's'}

for i, sys_name in enumerate(sys_names):
    ax = axes[i]
    rows_s = [r for r in rows if r['system'] == sys_name]
    rows_s.sort(key=lambda r: r['center_freq'])
    freqs = [r['center_freq'] for r in rows_s]
    fENT = [r['fixed_ENT'] for r in rows_s]
    mENT = [r['matched_ENT'] for r in rows_s]
    gaps = [r['ft_gap'] for r in rows_s]
    ax2 = ax.twinx()
    ax.plot(freqs, fENT, 'o-', color='C3', label='FIXED eps=0.3')
    ax.plot(freqs, mENT, 's-', color='C0', label='MATCHED RR~0.05')
    ax2.plot(freqs, gaps, '^--', color='C2', label='FT gap')
    ax.set_xscale('log')
    ax.set_xlabel('Band center freq (Hz)')
    ax.set_ylabel('ENT (nats)')
    ax2.set_ylabel('FT surrogate gap')
    a = analysis[sys_name]
    ax.set_title(f"{sys_name}\nrho_fixed={a['rho_fixed_ENT_freq']:+.2f} rho_matched={a['rho_matched_ENT_freq']:+.2f}\nmean_gap={a['mean_ft_gap']:+.2f} flip={a['sign_flip']}")
    ax.legend(loc='upper left', fontsize=7)
    ax2.legend(loc='upper right', fontsize=7)
    ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('emp253_lean_systems.png', dpi=120)
print("Saved emp253_lean_systems.png")

# Print summary
print("\n=== ANALYSIS SUMMARY ===")
for sys_name, a in analysis.items():
    print(f"{sys_name}: rho_fixed={a['rho_fixed_ENT_freq']:+.3f} (p={a['p_fixed']:.3f}), "
          f"rho_matched={a['rho_matched_ENT_freq']:+.3f} (p={a['p_matched']:.3f}), "
          f"mean_FT_gap={a['mean_ft_gap']:+.3f}, sign_flip={a['sign_flip']}")

print("\nDONE")
