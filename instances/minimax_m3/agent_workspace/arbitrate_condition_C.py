"""
Arbitration of EMP-207 (claude_sonnet: per-channel sign reversal in Condition C)
                vs.
                EMP-191 (xiaomi_mimo: ρ(freq, ENT)=-0.90 robust, 14/14 sign test)

Diagnostic: RR-feasibility floor.  Low-frequency bands (Delta, Theta) have high
autocorrelation in their Takens embedding, so the distance distribution has
heavy mass near zero.  When the matched-RR protocol forces the 5%-quantile
epsilon, low-frequency bands end up with RR >> 5% (saturation) while
high-frequency bands land near 5%.

If this floor effect is channel-dependent (some channels have cleaner
low-frequency dynamics than others), then:
   - On channels where floor binds → ENT collapses (low complexity, all recurrences)
   - On channels where floor doesn't bind → ENT follows EMP-191 (monotone decrease)

This predicts CLAUDE's per-channel sign reversal as a genuine regime-mixing
artifact, not as a refutation of EMP-191.

Protocol: colony_lib neural_eeg (fs=128 Hz, 14 channels), Butterworth band-pass,
Takens m=3 tau=2, z-scored.  Two arms:
   ARM-1: matched-RR via colony_lib target_rr=0.05 (EMP-191 protocol)
   ARM-2: matched-RR via Kimi-style 1500-sample subsampled 5% quantile
   DIAGNOSTIC: report actual RR achieved in each band; classify "floor-bound" if RR > 0.10

Then:
   - Compute ρ(freq, ENT) across 14 channels for both arms
   - Report per-channel sign of ρ
   - Test claude_sonnet's EMP-207 hypothesis: per-channel sign should flip ~50/50
   - Test xiaomi_mimo's EMP-191 hypothesis: per-channel sign should be ≲ 0 in (near-)all channels
   - Test the floor hypothesis: sign reversal clusters on channels where floor binds
"""

import numpy as np
from scipy.signal import butter, filtfilt
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr, binomtest
import sys, os, json

# Make colony_lib importable from world_c/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../world_c'))
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

# ---- Constants ----
FS = 128
BANDS = [
    ("Delta", 1.0, 3.0),
    ("Theta", 4.0, 7.0),
    ("Alpha", 8.0, 12.0),
    ("Beta",  13.0, 30.0),
    ("Gamma", 31.0, 44.0),
]
BAND_FREQ = np.array([2.0, 5.5, 10.0, 21.5, 37.5])  # band centers
EMBED_M = 3
EMBED_TAU = 2
TARGET_RR = 0.05
FLOOR_THRESHOLD = 0.10  # > 10% = "floor-bound"
N_EMBED = 2000  # subsample length for distance matrix

def butter_bandpass(x, lo, hi, fs, order=4):
    nyq = fs / 2.0
    b, a = butter(order, [lo/nyq, hi/nyq], btype='band')
    return filtfilt(b, a, x)

def matched_rr_epsilon_full(x_embedded, target_rr):
    """EMP-191 / colony_lib native: epsilon = quantile(all pairwise distances, target_rr)"""
    dists = squareform(pdist(x_embedded, metric='euclidean'))
    iu = np.triu_indices(len(dists), k=1)
    return float(np.quantile(dists[iu], target_rr)), dists

def matched_rr_epsilon_subsample(x_embedded, target_rr, n_sample=1500, seed=0):
    """Kimi-style: subsample 1500 points, take 5% quantile"""
    rng = np.random.default_rng(seed)
    if len(x_embedded) > n_sample:
        idx = rng.choice(len(x_embedded), n_sample, replace=False)
        sub = x_embedded[idx]
    else:
        sub = x_embedded
    dists = squareform(pdist(sub, metric='euclidean'))
    iu = np.triu_indices(len(dists), k=1)
    return float(np.quantile(dists[iu], target_rr)), dists

def per_band_per_channel(channels_data, channel_names, bands, arm='full'):
    """Returns: dict[(band, channel)] = {RR, DET, LAM, ENT, eps}"""
    results = {}
    for band_name, lo, hi in bands:
        for ch_name, x in zip(channel_names, channels_data):
            x = np.asarray(x, dtype=float)
            x = x - np.mean(x)
            rms = np.sqrt(np.mean(x**2)) + 1e-12
            x = x / rms  # z-score / unit-RMS

            x_filt = butter_bandpass(x, lo, hi, FS, order=4)
            x_filt = (x_filt - np.mean(x_filt)) / (np.std(x_filt) + 1e-12)

            emb = takens_embedding(x_filt, m=EMBED_M, tau=EMBED_TAU)
            # Subsample to keep distance matrix tractable
            if len(emb) > N_EMBED:
                stride = len(emb) // N_EMBED
                emb_use = emb[::stride][:N_EMBED]
            else:
                emb_use = emb

            if arm == 'full':
                eps, dists = matched_rr_epsilon_full(emb_use, TARGET_RR)
            else:
                eps, dists = matched_rr_epsilon_subsample(emb_use, TARGET_RR)

            R = (dists <= eps).astype(np.uint8)
            metrics = compute_rqa_metrics(R)
            metrics['eps'] = eps
            results[(band_name, ch_name)] = metrics
    return results

def main():
    print("Loading neural_eeg dataset...")
    ds = load_dataset("neural_eeg")
    print(f"  type: {type(ds).__name__}")

    # Inspect dataset structure
    if isinstance(ds, dict):
        keys = list(ds.keys())
        print(f"  keys: {keys}")
        # Try common keys
        for k in ['data', 'X', 'signals', 'EEG', 'eeg']:
            if k in ds:
                arr = np.asarray(ds[k])
                print(f"  ds[{k!r}].shape = {arr.shape}")
                break
        # Channel names?
        for k in ['channels', 'channel_names', 'ch_names']:
            if k in ds:
                channel_names = list(ds[k])
                print(f"  channels = {channel_names}")
                break
        else:
            channel_names = None
    else:
        arr = np.asarray(ds)
        print(f"  ds.shape = {arr.shape}")
        channel_names = None

    # Handle the common case: ds is a structured record with .data and .channels
    if hasattr(ds, 'data'):
        data = np.asarray(ds.data)
        if hasattr(ds, 'channels'):
            channel_names = list(ds.channels)
        elif hasattr(ds, 'channel_names'):
            channel_names = list(ds.channel_names)
    elif isinstance(ds, dict) and 'data' in ds:
        data = np.asarray(ds['data'])
        channel_names = ds.get('channels', channel_names)
    else:
        data = arr

    print(f"  data.shape = {data.shape}")

    if channel_names is None:
        # Try to infer from shape
        if data.ndim == 2:
            n_ch = data.shape[0] if data.shape[0] < data.shape[1] else data.shape[1]
            channel_names = [f"Ch{i+1}" for i in range(n_ch)]
        else:
            channel_names = [f"Ch{i+1}" for i in range(14)]

    # Ensure data is (n_channels, n_samples)
    if data.ndim == 2 and data.shape[1] > data.shape[0] and data.shape[0] <= 32:
        # Already (channels, samples)
        pass
    elif data.ndim == 2 and data.shape[0] > data.shape[1]:
        data = data.T
    elif data.ndim == 3:
        # (trials, channels, samples) - take first trial
        data = data[0]

    print(f"  using data.shape = {data.shape}, channels = {channel_names[:5]}... (n={len(channel_names)})")

    # Truncate to first 4096 samples for fair comparison with prior replications
    if data.shape[1] > 4096:
        data = data[:, :4096]

    channels_data = [data[i] for i in range(len(channel_names))]

    # ---- Run both arms ----
    print("\n=== ARM 1: colony_lib native target_rr=0.05 (full pairwise) ===")
    res_full = per_band_per_channel(channels_data, channel_names, BANDS, arm='full')

    print("\n=== ARM 2: Kimi-style subsampled target_rr=0.05 (1500 samples) ===")
    res_sub = per_band_per_channel(channels_data, channel_names, BANDS, arm='sub')

    # ---- Aggregate per-band ----
    def aggregate(results):
        per_band = {}
        for band_name, _, _ in BANDS:
            rrs = []; dets=[]; lams=[]; ents=[]; epss=[]
            for ch in channel_names:
                m = results[(band_name, ch)]
                rrs.append(m['RR']); dets.append(m['DET']); lams.append(m['LAM']); ents.append(m['ENT']); epss.append(m['eps'])
            per_band[band_name] = {
                'RR_mean': float(np.mean(rrs)), 'RR_std': float(np.std(rrs)),
                'DET_mean': float(np.mean(dets)), 'DET_std': float(np.std(dets)),
                'LAM_mean': float(np.mean(lams)), 'LAM_std': float(np.std(lams)),
                'ENT_mean': float(np.mean(ents)), 'ENT_std': float(np.std(ents)),
                'eps_mean': float(np.mean(epss)),
                'floor_bound_pct': float(np.mean(np.array(rrs) > FLOOR_THRESHOLD) * 100),
            }
        return per_band

    agg_full = aggregate(res_full)
    agg_sub = aggregate(res_sub)

    print("\n=========== ARM 1 (full): per-band aggregate ===========")
    for b in BANDS:
        bn = b[0]
        d = agg_full[bn]
        print(f"  {bn:6s}  RR={d['RR_mean']:.4f}±{d['RR_std']:.4f}  DET={d['DET_mean']:.3f}  LAM={d['LAM_mean']:.3f}  ENT={d['ENT_mean']:.3f}±{d['ENT_std']:.3f}  eps={d['eps_mean']:.4f}  floor%={d['floor_bound_pct']:.0f}")

    print("\n=========== ARM 2 (subsampled): per-band aggregate ===========")
    for b in BANDS:
        bn = b[0]
        d = agg_sub[bn]
        print(f"  {bn:6s}  RR={d['RR_mean']:.4f}±{d['RR_std']:.4f}  DET={d['DET_mean']:.3f}  LAM={d['LAM_mean']:.3f}  ENT={d['ENT_mean']:.3f}±{d['ENT_std']:.3f}  eps={d['eps_mean']:.4f}  floor%={d['floor_bound_pct']:.0f}")

    # ---- Spearman across bands (over channel mean) ----
    def spear(agg):
        ents = [agg[b[0]]['ENT_mean'] for b in BANDS]
        rho, p = spearmanr(BAND_FREQ, ents)
        return rho, p, ents

    rho_f, p_f, ents_f = spear(agg_full)
    rho_s, p_s, ents_s = spear(agg_sub)
    print(f"\n=========== Spearman(freq, ENT_mean) ===========")
    print(f"  ARM 1 (full):       ρ = {rho_f:+.4f}, p = {p_f:.4f}")
    print(f"  ARM 2 (subsampled): ρ = {rho_s:+.4f}, p = {p_s:.4f}")

    # ---- Per-channel sign test ----
    def per_channel_sign(results):
        """For each channel, compute Spearman(freq, ENT) over the 5 bands."""
        per_ch = {}
        for ch in channel_names:
            ents = [results[(b[0], ch)]['ENT'] for b in BANDS]
            rrs = [results[(b[0], ch)]['RR'] for b in BANDS]
            rho, p = spearmanr(BAND_FREQ, ents)
            per_ch[ch] = {'rho': float(rho), 'p': float(p), 'ENT': ents, 'RR': rrs}
        return per_ch

    pc_full = per_channel_sign(res_full)
    pc_sub = per_channel_sign(res_sub)

    n_neg_f = sum(1 for v in pc_full.values() if v['rho'] < 0)
    n_neg_s = sum(1 for v in pc_sub.values() if v['rho'] < 0)
    print(f"\n=========== Per-channel sign test (Xiaomi claim: 14/14 negative) ===========")
    print(f"  ARM 1 (full):       {n_neg_f}/{len(channel_names)} channels have ρ < 0")
    print(f"  ARM 2 (subsampled): {n_neg_s}/{len(channel_names)} channels have ρ < 0")

    # ---- Binomial test (sign reversal test) ----
    # H0: 50/50 sign split (Claude's EMP-207 claim)
    # H1: ≲ all-negative (Xiaomi's EMP-191 claim)
    n_total = len(channel_names)
    n_pos_f = n_total - n_neg_f
    n_pos_s = n_total - n_neg_s
    binom_f = binomtest(n_pos_f, n_total, p=0.5, alternative='less') if n_pos_f < n_total/2 else binomtest(n_pos_f, n_total, p=0.5, alternative='two-sided')
    binom_s = binomtest(n_pos_s, n_total, p=0.5, alternative='less') if n_pos_s < n_total/2 else binomtest(n_pos_s, n_total, p=0.5, alternative='two-sided')
    print(f"\n=========== Binomial test: 'all-negative' (Xiaomi) vs '50/50' (Claude) ===========")
    print(f"  ARM 1: n_pos={n_pos_f}/{n_total}, p(50/50) = {binom_f.pvalue:.2e}")
    print(f"  ARM 2: n_pos={n_pos_s}/{n_total}, p(50/50) = {binom_s.pvalue:.2e}")

    # ---- Floor-bound diagnostic ----
    # For each channel, classify bands as floor-bound (RR > 0.10) and check whether
    # the floor-bound bands are low-frequency.
    print(f"\n=========== Floor-bound diagnostic ===========")
    floor_summary = []
    for ch in channel_names:
        fb_bands = [BANDS[i][0] for i in range(len(BANDS)) if pc_full[ch]['RR'][i] > FLOOR_THRESHOLD]
        floor_summary.append({'channel': ch, 'floor_bound_bands': fb_bands, 'rho': pc_full[ch]['rho']})

    n_with_floor = sum(1 for fs in floor_summary if fs['floor_bound_bands'])
    print(f"  channels with at least one floor-bound band: {n_with_floor}/{n_total}")

    # Of channels with floor-bound low-freq bands, do they show sign reversal?
    n_flip_with_floor = 0
    n_flip_without_floor = 0
    for fs in floor_summary:
        lo_fb = any(b in ['Delta', 'Theta'] for b in fs['floor_bound_bands'])
        sign_flip = fs['rho'] > 0
        if lo_fb:
            n_flip_with_floor += int(sign_flip)
        else:
            n_flip_without_floor += int(sign_flip)
    print(f"  channels with low-freq floor-binding:  sign-flip ρ>0 in {n_flip_with_floor} cases")
    print(f"  channels WITHOUT low-freq floor:        sign-flip ρ>0 in {n_flip_without_floor} cases")

    # ---- Save artifacts ----
    out = {
        'protocol': {
            'fs': FS,
            'bands': [(b[0], b[1], b[2]) for b in BANDS],
            'band_freq_hz': BAND_FREQ.tolist(),
            'embed_m': EMBED_M, 'embed_tau': EMBED_TAU,
            'target_rr': TARGET_RR, 'floor_threshold': FLOOR_THRESHOLD,
            'n_embed_subsample': N_EMBED,
            'data_truncated_samples': 4096,
        },
        'data_shape': list(data.shape),
        'channels': channel_names,
        'agg_full': agg_full,
        'agg_sub': agg_sub,
        'spearman_full': {'rho': rho_f, 'p': p_f, 'ENT_per_band': ents_f},
        'spearman_sub': {'rho': rho_s, 'p': p_s, 'ENT_per_band': ents_s},
        'per_channel_full': pc_full,
        'per_channel_sub': pc_sub,
        'sign_test_full': {'n_neg': n_neg_f, 'n_total': n_total, 'binom_pvalue_50_50': binom_f.pvalue},
        'sign_test_sub': {'n_neg': n_neg_s, 'n_total': n_total, 'binom_pvalue_50_50': binom_s.pvalue},
        'floor_diagnostic': {
            'n_with_floor_bound_band': n_with_floor,
            'sign_flip_with_lowfreq_floor': n_flip_with_floor,
            'sign_flip_without_lowfreq_floor': n_flip_without_floor,
            'per_channel': floor_summary,
        },
        'hypotheses_tested': {
            'H_xiaomi_EMP191': 'ρ(freq, ENT) < 0 in (near-)all 14 channels',
            'H_claude_EMP207': 'ρ(freq, ENT) flips ~50/50 across channels',
            'H_floor': 'sign reversal clusters on channels where low-freq bands hit RR floor',
        },
    }

    out_path = os.path.join(os.path.dirname(__file__), 'arbitration_results.json')
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")

    # ---- Verdict ----
    print(f"\n{'='*60}")
    print("VERDICT")
    print(f"{'='*60}")
    if rho_f < 0 and n_neg_f >= 13:
        print("EMP-191 (Xiaomi): CONFIRMED in aggregate + per-channel sign test")
    elif rho_f > 0:
        print("EMP-207 (Claude): CONFIRMED in aggregate")
    else:
        print(f"MIXED: aggregate ρ={rho_f:.3f}, {n_neg_f}/{n_total} channels negative")

    if n_flip_with_floor > 2 * max(1, n_flip_without_floor):
        print("Floor hypothesis: CONFIRMED (sign flips cluster on floor-bound channels)")
    else:
        print(f"Floor hypothesis: NOT CONFIRMED ({n_flip_with_floor} with floor vs {n_flip_without_floor} without)")

if __name__ == '__main__':
    main()
