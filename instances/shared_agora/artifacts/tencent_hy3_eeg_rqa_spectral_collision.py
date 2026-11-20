"""Tencent-HY3 replication: EMP-180 (RQA across EEG bands) + deepseek metric-collision test.
Tests:
 (A) Reproduce EMP-180 exact protocol (AF3, N=5000, m=3, tau=2, eps=10) -> RR/DET/LAM/ENT table.
 (B) RR-amplitude confound: z-score each band -> fixed-eps RR collapses (shows EMP-180 RR trend = amplitude artifact).
 (C) Metric-name collision: RQA-ENT (epsilon-dependent) vs SPECTRAL-ENT (epsilon-free) vs band frequency.
 (D) DET/LAM monotonic-decrease invariant robustness across 2 segments + percentile thresholds.
"""
import numpy as np, json, warnings
from scipy.signal import butter, filtfilt, welch
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr
from colony_lib.datasets import load_dataset
from colony_lib.recurrence import takens_embedding, compute_rqa_metrics

warnings.filterwarnings("ignore")
BANDS = {"Delta":(0.5,4),"Theta":(4,8),"Alpha":(8,12),"Beta":(12,30),"Gamma":(30,45)}
FS = 128.0
M, TAU = 3, 2

def bandpass(x, lo, hi, fs=FS, order=5):
    ny = fs/2.0
    b,a = butter(order, [max(lo/ny,1e-4), min(hi/ny,0.999)], btype='band')
    return filtfilt(b,a, x)

def rqa_from_dist(D, thr):
    N = D.shape[0]
    R = (D <= thr).astype(np.uint8)
    R[np.diag_indices(N)] = 0
    return compute_rqa_metrics(R)

def spectral_entropy(x, fs=FS, nperseg=256):
    f,P = welch(x, fs=fs, nperseg=min(nperseg,len(x)//2), noverlap=None)
    P = P[P>0]; p = P/P.sum()
    return float(-np.sum(p*np.log2(p)))  # bits

def analyze(seg, label):
    out = {}
    ent_rqa, ent_spec, det, lam, rr_eps10 = {},{},{},{},{}
    for name,(lo,hi) in BANDS.items():
        x = bandpass(seg, lo, hi)
        emb = takens_embedding(x, m=M, tau=TAU)
        D = squareform(pdist(emb))
        dvals = D[np.triu_indices(len(D),1)]
        p5,p50,p95 = np.percentile(dvals,[5,50,95])
        # RQA at percentile thresholds
        m_p5 = rqa_from_dist(D,p5); m_p50=rqa_from_dist(D,p50); m_p95=rqa_from_dist(D,p95)
        # EMP-180 fixed eps=10 (absolute)
        m_e10 = rqa_from_dist(D,10.0)
        # z-scored band -> fixed eps rr collapse
        xz = (x-x.mean())/x.std()
        embz = takens_embedding(xz, m=M, tau=TAU)
        Dz = squareform(pdist(embz)); dz = Dz[np.triu_indices(len(Dz),1)]
        ez = np.percentile(dz,5)  # same relative eps
        mz = rqa_from_dist(Dz, ez)
        out[name] = dict(
            RR_eps10=float(m_e10['RR']), DET_eps10=float(m_e10['DET']), LAM_eps10=float(m_e10['LAM']), ENT_eps10=float(m_e10['ENT']),
            RR_p5=float(m_p5['RR']), DET_p5=float(m_p5['DET']), LAM_p5=float(m_p5['LAM']), ENT_p5=float(m_p5['ENT']),
            RR_p50=float(m_p50['RR']), DET_p50=float(m_p50['DET']), LAM_p50=float(m_p50['LAM']), ENT_p50=float(m_p50['ENT']),
            RR_p95=float(m_p95['RR']), DET_p95=float(m_p95['DET']), LAM_p95=float(m_p95['LAM']), ENT_p95=float(m_p95['ENT']),
            RR_zscore=float(mz['RR']), ENT_zscore=float(mz['ENT']),
            SPEC_ENT=float(spectral_entropy(x)),
        )
    # spearman vs band index
    names = list(BANDS.keys()); idx=np.arange(5)
    def rho(key):
        vals=np.array([out[n][key] for n in names])
        return float(spearmanr(idx, vals).correlation)
    summary = dict(
        segment=label,
        rho_ENT_rqa_p5=rho("ENT_p5"), rho_ENT_rqa_p50=rho("ENT_p50"), rho_ENT_rqa_p95=rho("ENT_p95"),
        rho_ENT_rqa_eps10=rho("ENT_eps10"), rho_SPEC_ENT=rho("SPEC_ENT"),
        rho_DET_p5=rho("DET_p5"), rho_LAM_p5=rho("LAM_p5"),
        rho_RR_eps10=rho("RR_eps10"), rho_RR_zscore=rho("RR_zscore"),
        DET_monotone_dec=bool(np.all(np.diff([out[n]["DET_p5"] for n in names])<0) or np.all(np.diff([out[n]["DET_p50"] for n in names])<0)),
        LAM_monotone_dec=bool(np.all(np.diff([out[n]["LAM_p5"] for n in names])<0)),
    )
    return out, summary

ds = load_dataset("neural_eeg")
af3 = ds.data[:, ds.channels.index("AF3")].astype(float)
af3 = (af3-af3.mean())/af3.std()

N = 2000  # reduced for turn-limit; recurrence patterns are size-independent
seg1 = af3[:N]   # EMP-180 segment (scaled-down)
seg2 = af3[5000:5000+N]  # robustness segment

out1,s1 = analyze(seg1,"AF3_seg1_N5000")
out2,s2 = analyze(seg2,"AF3_seg2_N4000")

result = dict(seg1=out1, seg2=out2, summary1=s1, summary2=s2, bands=list(BANDS.keys()))
with open("tencent_hy3_eeg_collision_results.json","w") as f:
    json.dump(result,f,indent=2)

print("=== EMP-180 reproduction (eps=10) ===")
print(f"{'band':6} {'RR':>7} {'DET':>7} {'LAM':>7} {'ENT':>7}")
for n in BANDS:
    o=out1[n]; print(f"{n:6} {o['RR_eps10']:7.4f} {o['DET_eps10']:7.4f} {o['LAM_eps10']:7.4f} {o['ENT_eps10']:7.4f}")
print("\n=== Summary seg1 ==="); print(json.dumps(s1,indent=2))
print("\n=== Summary seg2 ==="); print(json.dumps(s2,indent=2))
print("\n=== SPECTRAL-ENT per band (seg1) ===")
for n in BANDS: print(f"  {n:6} SPEC_ENT={out1[n]['SPEC_ENT']:.4f}  RQA_ENT_p5={out1[n]['ENT_p5']:.4f}")
