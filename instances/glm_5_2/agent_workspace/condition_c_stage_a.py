"""STAGE A: analyze completed rr_sweep_rows.json.
1) per-band ENT(RR) curves  2) band-pair ENT crossings  3) noise floor:
rho(freq,ENT) vs RR drift  4) iid Bernoulli null entropy (analytic + MC)."""
import json
import numpy as np
from scipy.stats import spearmanr

rows = json.load(open("rr_sweep_rows.json"))
FREQ = {"delta": 2.0, "theta": 5.5, "alpha": 10.0, "beta": 21.0, "gamma": 37.5}

curves = {}
for band in FREQ:
    for conv in ("full", "sub"):
        sel = sorted([r for r in rows if r["band"] == band and r["conv"] == conv
                      and r["RR"] > 0], key=lambda r: r["RR"])
        curves[(band, conv)] = (np.array([r["RR"] for r in sel]),
                                np.array([r["ENT"] for r in sel]),
                                np.array([r["DET"] for r in sel]))

print("=== A1: per-band ENT(RR) curves (full conv) ===")
for band in FREQ:
    rr, ent, _ = curves[(band, "full")]
    print(f"{band:6s} " + " ".join(f"({r:.3f},{e:.2f})" for r, e in zip(rr, ent)))

print("=== A2: band-pair ENT crossings (full conv, log-RR interp) ===")
for a, b in [("delta", "gamma"), ("delta", "alpha"), ("alpha", "gamma"),
             ("delta", "theta"), ("theta", "gamma")]:
    rra, enta, _ = curves[(a, "full")]
    rrb, entb, _ = curves[(b, "full")]
    lo, hi = max(rra.min(), rrb.min()), min(rra.max(), rrb.max())
    if lo >= hi:
        print(f"  {a}-{b}: no RR overlap"); continue
    grid = np.exp(np.linspace(np.log(lo), np.log(hi), 800))
    d = (np.interp(np.log(grid), np.log(rra), enta)
         - np.interp(np.log(grid), np.log(rrb), entb))
    sgn = np.sign(d)
    flips = np.flatnonzero(np.diff(sgn) != 0)
    if flips.size:
        for k in flips[:5]:
            print(f"  {a}-{b}: ENT diff flips sign at RR~{grid[k]:.3f} "
                  f"(d={d[k]:+.2f} -> {d[k+1]:+.2f})")
    else:
        print(f"  {a}-{b}: no crossing in [{lo:.3f},{hi:.3f}] "
              f"(d range {d.min():+.2f}..{d.max():+.2f})")

print("=== A3: noise floor — rho(freq,ENT) vs RR multiplier (full conv) ===")
mults = sorted({r["mult"] for r in rows})
print("mult | mean_RR | rho(freq,ENT) | per-band RR")
for m in mults:
    g = sorted([r for r in rows if r["conv"] == "full"
                and abs(r["mult"] - m) < 1e-9], key=lambda r: r["freq"])
    rr = [r["RR"] for r in g]; ent = [r["ENT"] for r in g]
    rho = float(spearmanr([FREQ[r["band"]] for r in g], ent)[0])
    print(f"{m:4.2f} | {np.mean(rr):.3f} | {rho:+.3f} | "
          + " ".join(f"{b}:{x:.3f}" for b, x in
                     zip([r["band"] for r in g], rr)))

print("=== A4: iid Bernoulli null at RR=p ===")
def h_geo(p):
    return -np.log2(1 - p) - (p / (1 - p)) * np.log2(p)
for p in (0.02, 0.05, 0.107, 0.32, 0.43, 0.6, 0.84):
    print(f"  p={p:.3f}  H_iid={h_geo(p):.3f} bits")
# MC check at p=0.05, N=2000 diagonals
rng = np.random.default_rng(11)
N = 2000
ents = []
for rep in range(20):
    Rb = (rng.random((N, N)) < 0.05).astype(np.uint8)
    lens = []
    for k in range(1, N):
        d = Rb.diagonal(k)
        dp = np.empty(len(d) + 2, dtype=np.int8)
        dp[0] = 0; dp[-1] = 0; dp[1:-1] = d
        df = np.diff(dp)
        s = np.flatnonzero(df == 1)
        if s.size == 0:
            continue
        e = np.flatnonzero(df == -1)
        ln = e - s
        ln = ln[ln >= 2]
        if ln.size:
            lens.append(ln)
    lens = np.concatenate(lens)
    h = np.bincount(lens); pr = h[h > 0] / h.sum()
    ents.append(float(-(pr * np.log2(pr)).sum()))
print(f"  MC iid p=0.05: ENT mean={np.mean(ents):.3f} "
      f"(analytic {h_geo(0.05):.3f}; measured EEG bands 2.56-4.04)")
print("STAGE A DONE")
