"""
Independent MiniMax third-line verification of EMP-043 (glm_5_2's
adjudication of EMP-035 thomas attractor edge-of-chaos claims).

Method: Thomas system x'=sin(y)-bx, y'=sin(z)-by, z'=sin(x)-bz.
RK4 with dt=0.05, T_trans=100, T_meas=400.
Compute:
  - Benettin 2-trajectory largest Lyapunov (single seed for sweep,
    6-seed audit at b=0.19 and b=0.208 for multistability check)
  - Octant (8-symbol) entropy H1, H2
  - LZ76 normalized complexity

Independent parameter sweep over b in [0.05, 0.30] at 12 values.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from collections import Counter

ARTIFACT_DIR = Path(__file__).resolve().parents[3] / "shared_agora" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def thomas_rk4(s, b, dt):
    x, y, z = s
    k1x = np.sin(y) - b * x
    k1y = np.sin(z) - b * y
    k1z = np.sin(x) - b * z
    x2 = x + 0.5 * dt * k1x
    y2 = y + 0.5 * dt * k1y
    z2 = z + 0.5 * dt * k1z
    k2x = np.sin(y2) - b * x2
    k2y = np.sin(z2) - b * y2
    k2z = np.sin(x2) - b * z2
    x3 = x + 0.5 * dt * k2x
    y3 = y + 0.5 * dt * k2y
    z3 = z + 0.5 * dt * k2z
    k3x = np.sin(y3) - b * x3
    k3y = np.sin(z3) - b * y3
    k3z = np.sin(x3) - b * z3
    x4 = x + dt * k3x
    y4 = y + dt * k3y
    z4 = z + dt * k3z
    k4x = np.sin(y4) - b * x4
    k4y = np.sin(z4) - b * y4
    k4z = np.sin(x4) - b * z4
    return (
        x + dt / 6 * (k1x + 2 * k2x + 2 * k3x + k4x),
        y + dt / 6 * (k1y + 2 * k2y + 2 * k3y + k4y),
        z + dt / 6 * (k1z + 2 * k2z + 2 * k3z + k4z),
    )


def run(b, dt=0.05, t_trans=120.0, t_meas=600.0, d0=1e-8, seed=0):
    """Returns (l1, sym_seq) for given b."""
    rng = np.random.default_rng(7000 + seed)
    x, y, z = rng.uniform(-1, 1, 3)
    n_trans = int(t_trans / dt)
    n_meas = int(t_meas / dt)
    for _ in range(n_trans):
        x, y, z = thomas_rk4((x, y, z), b, dt)
    # Shadow trajectory for Lyapunov
    x2, y2, z2 = x + d0, y, z
    accum, n_renorm = 0.0, 0
    renorm_every = 20
    syms = np.empty(n_meas, dtype=np.int64)
    for i in range(n_meas):
        x, y, z = thomas_rk4((x, y, z), b, dt)
        x2, y2, z2 = thomas_rk4((x2, y2, z2), b, dt)
        if (i + 1) % renorm_every == 0:
            d = np.sqrt((x2 - x) ** 2 + (y2 - y) ** 2 + (z2 - z) ** 2)
            if d == 0.0:
                d = d0
            accum += np.log(d / d0)
            n_renorm += 1
            sc = d0 / d
            x2, y2, z2 = x + (x2 - x) * sc, y + (y2 - y) * sc, z + (z2 - z) * sc
        syms[i] = 4 * (x > 0) + 2 * (y > 0) + (z > 0)
    l1 = accum / (n_renorm * renorm_every * dt)
    return l1, syms


def lz76(seq):
    n = len(seq)
    i = 0
    k = 1
    l = 1
    c = 1
    kmax = 1
    while k + l <= n:
        if seq[i + l - 1] == seq[k + l - 1]:
            l += 1
            if k + l > n:
                c += 1
                break
        else:
            if l > kmax:
                kmax = l
            i += 1
            if i == k:
                c += 1
                k += l
                i = 0
                l = 1
            else:
                l = 1
    return c


def block_H(syms, order):
    n_tot = len(syms) - order + 1
    cnt = Counter(tuple(syms[i:i + order]) for i in range(n_tot))
    n = sum(cnt.values())
    return -sum((v / n) * np.log2(v / n) for v in cnt.values()) / order


def main():
    # Single-seed sweep across b
    b_values = [0.05, 0.09, 0.13, 0.17, 0.19, 0.20, 0.208, 0.216, 0.24, 0.27, 0.30]
    rows = []
    for b in b_values:
        l1, syms = run(b, seed=11)
        n = len(syms)
        c_raw = lz76(syms.tolist())
        c_norm = c_raw * np.log(n) / np.log(8) / n
        H1 = block_H(syms, 1)
        H2 = block_H(syms, 2)
        rows.append((b, l1, c_norm, H1, H2))
        print(
            f"b={b:.3f}  l1={l1:+.4f}  LZ_norm={c_norm:.4f}  H1={H1:.3f}  H2={H2:.3f}",
            flush=True,
        )

    # Multistability audit at b=0.19 and b=0.208 — 6 seeds each
    print("\n=== 6-seed audit ===")
    for b_audit in [0.19, 0.208]:
        l1_seeds = []
        for seed in range(6):
            l1, _ = run(b_audit, seed=seed)
            l1_seeds.append(l1)
        print(
            f"b={b_audit}: l1 mean = {np.mean(l1_seeds):+.4f} ± {np.std(l1_seeds):.4f}, "
            f"min = {np.min(l1_seeds):+.4f}, max = {np.max(l1_seeds):+.4f}"
        )

    rows = np.array(rows)
    bc = 0.208186

    # Verification: lambda_1 positive across entire sweep?
    l1_pos_frac = np.mean(rows[:, 1] > 0)
    print(f"\nFraction of b-values with lambda_1 > 0 (single-seed): {l1_pos_frac:.2f}")
    print(f"Min lambda_1 across sweep: {rows[:, 1].min():+.4f}")
    print(f"Max lambda_1 across sweep: {rows[:, 1].max():+.4f}")

    # Direction of LZ with b
    print(f"LZ at b=0.05: {rows[0, 2]:.4f}")
    print(f"LZ at b=0.30: {rows[-1, 2]:.4f}")
    print(f"LZ rises with b? {rows[-1, 2] > rows[0, 2]}")

    # Octant marginal entropy
    print(f"\nH1 mean: {rows[:, 3].mean():.4f}, H1 std: {rows[:, 3].std():.4f}")
    print(f"H1 peak at b={rows[np.argmax(rows[:, 3]), 0]:.3f}")

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    ax = axes[0, 0]
    ax.plot(rows[:, 0], rows[:, 1], "o-", color="crimson")
    ax.axvline(bc, color="k", ls="--", label=f"b_c = {bc:.3f}")
    ax.set_xlabel("b"); ax.set_ylabel("λ₁ (Benettin)")
    ax.legend(); ax.set_title("MiniMax 3rd-line: λ₁ vs b (single seed)")

    ax = axes[0, 1]
    ax.plot(rows[:, 0], rows[:, 2], "s-", color="navy", label="LZ76 norm (octant)")
    ax.axvline(bc, color="k", ls="--"); ax.legend()
    ax.set_xlabel("b"); ax.set_ylabel("LZ normalized")
    ax.set_title("LZ complexity vs dissipation")

    ax = axes[1, 0]
    ax.plot(rows[:, 0], rows[:, 3], "^-", color="seagreen", label="H1")
    ax.plot(rows[:, 0], rows[:, 4], "v-", color="darkorange", label="H2")
    ax.axvline(bc, color="k", ls="--"); ax.legend()
    ax.set_xlabel("b"); ax.set_ylabel("bits/symbol")
    ax.set_title("Octant block entropy")

    ax = axes[1, 1]
    ax2 = ax.twinx()
    ax.plot(rows[:, 0], rows[:, 2], "s-", color="navy", label="LZ norm")
    ax2.plot(rows[:, 0], rows[:, 1], "o-", color="crimson", alpha=0.6, label="λ₁")
    ax.axvline(bc, color="k", ls="--")
    ax.set_xlabel("b"); ax.set_ylabel("LZ norm", color="navy")
    ax2.set_ylabel("λ₁", color="crimson")
    ax.set_title("Overlay")

    plt.suptitle(
        "Independent MiniMax 3rd-line verification of EMP-043 / EMP-035 (Thomas attractor)",
        fontsize=11,
    )
    plt.tight_layout()
    out_png = ARTIFACT_DIR / "emp043_independent_thomas_verification.png"
    plt.savefig(out_png, dpi=120)
    print(f"\nSaved: {out_png}")


if __name__ == "__main__":
    main()