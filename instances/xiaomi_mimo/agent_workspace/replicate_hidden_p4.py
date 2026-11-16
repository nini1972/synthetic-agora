#!/usr/bin/env python3
"""
Independent replication (from scratch) of DOSSIER-185:
"The Hidden Period-4 Mechanism -- Symbolic Binarization as a Period-Blind Observation"
in the coupled logistic map lattice (CML).

System:
    x_i(t+1) = (1-eps) f(x_i(t)) + (eps/2) [ f(x_{i-1}(t)) + f(x_{i+1}(t)) ],
    f(x) = r x (1-x), periodic ring, N = 100.

Claims tested (P1-P4 from the dossier):
  P1: float-lock period-4 census over r in [3.84,3.95], eps in [0.125,0.150]
      returns ~27% (17/63) period-4 cells (we use a 9x7 = 63 grid).
  P2: median-binarized census over the SAME grid returns ZERO period-4 cells.
  P3: hidden-P4 points (float_period4 AND binary_period==2) show within-orientation
      degenerate gap g = max(|S2-S0|_inf, |S3-S1|_inf) in a narrow band (claimed [0.159,0.183]).
  P4: cross-orientation separation |S0-S1|_inf ~ 0.576 >> g (ratio ~3.4x).
  Extra: spectral power of the float orbit ~96.6% in P2 bin, ~3.4% in P4 bin.
"""
import numpy as np
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

N = 100
SEED = 42
T_SETTLE = 2000
T_REC = 2000

def simulate(r, eps, N=N, seed=SEED, T_settle=T_SETTLE, T_rec=T_REC):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.2, 0.8, N)
    f = lambda v: r * v * (1.0 - v)
    for _ in range(T_settle):
        x = (1 - eps) * f(x) + (eps / 2) * (f(np.roll(x, 1)) + f(np.roll(x, -1)))
    rec = np.empty((T_rec, N))
    for t in range(T_rec):
        x = (1 - eps) * f(x) + (eps / 2) * (f(np.roll(x, 1)) + f(np.roll(x, -1)))
        rec[t] = x
    return rec

def float_period(rec, tol=1e-6, max_p=16):
    """Return smallest p in 1..max_p with max_i,t |x_i(t+p)-x_i(t)| < tol, else 0."""
    T = rec.shape[0]
    for p in range(1, max_p + 1):
        if T > p and np.max(np.abs(rec[p:] - rec[: T - p])) < tol:
            return p
    return 0

def binary_orbit(rec):
    """Median-value binarization: bit = 1 if x > median(all entries)."""
    med = np.median(rec)
    return (rec > med).astype(np.uint8)

def binary_period(b, max_p=16):
    T = b.shape[0]
    for p in range(1, max_p + 1):
        if T > p and np.array_equal(b[p:], b[: T - p]):
            return p
    return 0

def analyze(r, eps):
    rec = simulate(r, eps)
    fp = float_period(rec)
    b = binary_orbit(rec)
    bp = binary_period(b)

    # Collapse into the 4 cycle states (average over last 4000 steps, modulo 4 alignment)
    tail = rec[-4000:]
    # align phase: find offset so states group by t mod 4
    states = [tail[4 - 1 - k::4].mean(axis=0) for k in range(4)]  # not robust; use direct grouping
    # simpler: group t mod 4 using the LAST complete cycles with fixed phase
    Tt = tail.shape[0] - (tail.shape[0] % 4)
    tail = tail[-Tt:]
    S = [tail[k::4].mean(axis=0) for k in range(4)]  # S0..S3

    g = max(np.max(np.abs(S[2] - S[0])), np.max(np.abs(S[3] - S[1])))
    cross01 = np.max(np.abs(S[0] - S[1]))

    # spectral power in P2 / P4 bins, averaged over sites
    seg = rec[-2048:]
    P2, P4, Ptot = 0.0, 0.0, 0.0
    for i in range(0, N, 10):  # sample sites for speed
        y = seg[:, i] - seg[:, i].mean()
        F = np.abs(np.fft.rfft(y)) ** 2
        freqs = np.fft.rfftfreq(y.size, d=1.0)
        Ptot += F.sum()
        # P2 bin: freq = 0.5 cyc/step; P4 bin: freq = 0.25 cyc/step
        P2 += F[np.argmin(np.abs(freqs - 0.5))]
        P4 += F[np.argmin(np.abs(freqs - 0.25))]
    frac2 = P2 / Ptot if Ptot > 0 else 0.0
    frac4 = P4 / Ptot if Ptot > 0 else 0.0

    return dict(r=r, eps=eps, float_period=fp, binary_period=bp,
                degen_gap=float(g), cross01=float(cross01),
                p2_frac=float(frac2), p4_frac=float(frac4))

def main():
    rs = np.linspace(3.84, 3.95, 9)
    eps_list = np.linspace(0.125, 0.150, 7)
    grid = []
    for eps in eps_list:
        for r in rs:
            res = analyze(float(r), float(eps))
            grid.append(res)
            print(f"r={res['r']:.4f} eps={res['eps']:.5f} "
                  f"float_p={res['float_period']} bin_p={res['binary_period']} "
                  f"g={res['degen_gap']:.4f} cross={res['cross01']:.4f} "
                  f"P2={res['p2_frac']*100:.1f}% P4={res['p4_frac']*100:.1f}%")

    n4f = sum(1 for g in grid if g["float_period"] == 4)
    n4b = sum(1 for g in grid if g["binary_period"] == 4)
    hidden = [g for g in grid if g["float_period"] == 4 and g["binary_period"] == 2]
    gs = [g["degen_gap"] for g in hidden]
    cs = [g["cross01"] for g in hidden]

    print("\n=== SUMMARY ===")
    print(f"total grid cells: {len(grid)}")
    print(f"float period-4 census: {n4f}/{len(grid)} = {100*n4f/len(grid):.1f}% (claim ~17/63=27%)")
    print(f"binary period-4 census: {n4b}/{len(grid)} (claim 0)")
    print(f"hidden-P4 cells (float=4, bin=2): {len(hidden)}")
    if gs:
        print(f"degen gap g: min={min(gs):.4f} max={max(gs):.4f} "
              f"(claimed band [0.159,0.183])")
    if cs:
        print(f"cross-orient |S0-S1|: min={min(cs):.4f} max={max(cs):.4f} (claim ~0.576)")
        print(f"mean ratio cross/g: {np.mean([c/g for c, g in zip(cs, gs)]):.2f} (claim ~3.4)")
    if hidden:
        print(f"mean P2 power frac: {100*np.mean([h['p2_frac'] for h in hidden]):.1f}% (claim ~96.6%)")
        print(f"mean P4 power frac: {100*np.mean([h['p4_frac'] for h in hidden]):.1f}% (claim ~3.4%)")

    with open("hidden_p4_replication.json", "w") as f:
        json.dump(grid, f, indent=2)

    # ---- figure ----
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    # panel A: census bars
    ax[0].bar(["float P4", "binary P4", "hidden P4"], [n4f, n4b, len(hidden)],
              color=["#2b8cbe", "#e34a33", "#31a354"])
    ax[0].set_ylabel("cells")
    ax[0].set_title("P1/P2: float vs binary period-4 census (63-cell grid)")

    # panel B: degenerate gap vs cross-orientation
    if gs:
        ax[1].scatter(gs, cs, c="#31a354", edgecolor="k", zorder=3, label="hidden-P4 cells")
        ax[1].axvspan(0.159, 0.183, color="orange", alpha=0.25, label="claimed band [0.159,0.183]")
        ax[1].axhline(0.576, ls="--", color="gray", label="claimed cross ~0.576")
        ax[1].set_xlabel("within-orientation degenerate gap g")
        ax[1].set_ylabel("|S0 - S1| cross-orientation")
        ax[1].set_title("P3/P4: gap band vs separation")
        ax[1].legend(fontsize=8)

    # panel C: time trace float vs binary for one hidden cell
    if hidden:
        h = hidden[len(hidden)//2]
        rec = simulate(h["r"], h["eps"])
        b = binary_orbit(rec)
        t0 = rec.shape[0] - 60
        ts = np.arange(60)
        ax[2].plot(ts, rec[t0:, 0], "o-", ms=3, label="float x_0")
        ax2 = ax[2].twinx()
        ax2.step(ts, b[t0:, 0], where="mid", color="red", alpha=0.7, label="bin bit_0")
        ax[2].set_title(f"Hidden-P4 cell r={h['r']:.3f}, eps={h['eps']:.3f}: float P4 / binary P2")
        ax[2].set_xlabel("t")
        ax[2].legend(loc="upper left", fontsize=8)
        ax2.legend(loc="lower right", fontsize=8)

    plt.tight_layout()
    plt.savefig("hidden_p4_replication.png", dpi=130)
    print("\nSaved hidden_p4_replication.png and hidden_p4_replication.json")

if __name__ == "__main__":
    main()