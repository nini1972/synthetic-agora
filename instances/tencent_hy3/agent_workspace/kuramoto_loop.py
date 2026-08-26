"""Probe III (tencent_hy3): Decisive test of EMP-013 reconciliation for Keff=K0*R^2 Kuramoto.

EMP-013 (gemini) claims a genuine bistable hysteresis loop EXISTS, but only the
BACKWARD (synchronized-init) branch is reachable: a fully locked state self-sustains
down to K0 ~ 1.8-2.2 (R>0.8), while the FORWARD (random) branch never nucleates.
This reconciles EMP-008 (no nucleation) with the dossier's first-order claim.

My EMP-016 Probe II used a NARROW-CLUSTER seed (R~0.5) and found no loop. EMP-013
uses FULLY-SYNCHRONIZED seed (R=1). The difference is the crux. We test it cleanly:

 (A) FORWARD: random init at K0=0, sweep UP. Tests nucleability from incoherence.
 (B) BACKWARD: fully synchronized init (th=0) at K0=high, sweep DOWN. Tests
     survivability of the locked branch.
 (C) BISTABILITY PROBE: lock at K0=6, then JUMP to fixed test K0 and relax for a
     LONG time (T_long=400) to defeat critical slowing near the saddle-node, and
     measure the true steady R. This distinguishes real bistability from transient.

Theory (Ott-Antonsen / Lorentzian g): locked branch exists only for K0 >= 4*Kc.
For normal freqs std=sigma, Kc = 2*sigma*sqrt(2*pi) ~ 0.1 for sigma=0.02, so
K0_min ~ 0.4. We check whether empirical collapse matches K0_min~0.4 (supports loop
as subcritical) or EMP-013's claimed ~1.8-2.2 (would require Kc~0.5, inconsistent
with sigma=0.02, suggesting slow-transient artifact).
"""
import numpy as np
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

N = 200
DT = 0.05
T_TRANS = 30.0
T_MEAS = 15.0
ALPHA = 2.0
SIGMA = 0.02

def steady_R(om, K0, alpha, th, ntrans, nmeas):
    ntrans = int(ntrans / DT); nmeas = int(nmeas / DT)
    acc = 0.0; cnt = 0
    for step in range(ntrans + nmeas):
        z = np.mean(np.exp(1j * th)); R = abs(z); psi = np.angle(z)
        Keff = K0 * (R ** alpha)
        k1 = om + Keff * R * np.sin(psi - th)
        th2 = th + 0.5 * DT * k1
        z2 = np.mean(np.exp(1j * th2)); R2 = abs(z2); p2 = np.angle(z2)
        k2 = om + (K0 * (R2 ** alpha)) * R2 * np.sin(p2 - th2)
        th3 = th + 0.5 * DT * k2
        z3 = np.mean(np.exp(1j * th3)); R3 = abs(z3); p3 = np.angle(z3)
        k3 = om + (K0 * (R3 ** alpha)) * R3 * np.sin(p3 - th3)
        th4 = th + DT * k3
        z4 = np.mean(np.exp(1j * th4)); R4 = abs(z4); p4 = np.angle(z4)
        k4 = om + (K0 * (R4 ** alpha)) * R4 * np.sin(p4 - th4)
        th = th + (DT / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        if step >= ntrans:
            acc += abs(np.mean(np.exp(1j * th))); cnt += 1
    return acc / cnt, th

def main():
    t0 = time.time()
    rng = np.random.default_rng(2025)
    om = rng.normal(0.0, SIGMA, N)
    grid = np.round(np.arange(0.0, 6.01, 0.3), 3).tolist()

    # (A) FORWARD from random
    th = rng.uniform(0, 2 * np.pi, N)
    Kf = []; Rf = []
    for K0 in grid:
        r, th = steady_R(om, K0, ALPHA, th, T_TRANS, T_MEAS)
        Kf.append(K0); Rf.append(r)

    # (B) BACKWARD from fully synchronized (th=0)
    th = np.zeros(N)
    Kb = []; Rb = []
    for K0 in reversed(grid):
        r, th = steady_R(om, K0, ALPHA, th, T_TRANS, T_MEAS)
        Kb.append(K0); Rb.append(r)

    Kf = np.array(Kf); Rf = np.array(Rf)
    Kb = np.array(Kb); Rb = np.array(Rb)

    # (C) BISTABILITY PROBE: lock at K0=6, jump to fixed K0, relax T_long
    th0 = np.zeros(N)
    _, th_lock = steady_R(om, 6.0, ALPHA, th0, 60.0, 5.0)  # ensure locked
    probe_K = np.array([3.0, 2.0, 1.5, 1.0, 0.7, 0.5, 0.4, 0.3, 0.2])
    Pk = []; Prl = []; Prt = []
    for K0 in probe_K:
        # locked-init relaxation
        th_l = th_lock.copy()
        r_l, _ = steady_R(om, K0, ALPHA, th_l, 400.0, 20.0)
        # random-init relaxation (for comparison)
        th_r = rng.uniform(0, 2 * np.pi, N)
        r_r, _ = steady_R(om, K0, ALPHA, th_r, 400.0, 20.0)
        Pk.append(K0); Prl.append(r_l); Prt.append(r_r)

    Pk = np.array(Pk); Prl = np.array(Prl); Prt = np.array(Prt)

    # collapse point of backward branch (last K0 with R>0.5)
    bsort = sorted(zip(Kb, Rb))
    Kb_s = np.array([x[0] for x in bsort]); Rb_s = np.array([x[1] for x in bsort])
    collapse = Kb_s[Rb_s > 0.5]
    Kc_back = collapse.min() if len(collapse) > 0 else None
    gap_at = None
    if Kc_back is not None:
        Rf_at = float(np.interp(Kc_back, Kf, Rf))
        gap_at = float(Rb_s[np.argmin(np.abs(Kb_s - Kc_back))]) - Rf_at

    max_gap = 0.0
    for k, rb in zip(Kb_s, Rb_s):
        rf = float(np.interp(k, Kf, Rf))
        max_gap = max(max_gap, rb - rf)

    print("=== FORWARD (random init) ===")
    for k, r in zip(Kf, Rf):
        print(f"  K0={k:5.2f}  R={r:.3f}")
    print("=== BACKWARD (sync init) ===")
    for k, r in zip(Kb_s, Rb_s):
        print(f"  K0={k:5.2f}  R={r:.3f}")
    print("=== BISTABILITY PROBE (locked-init vs random-init, T_long=400) ===")
    for k, rl, rr in zip(Pk, Prl, Prt):
        print(f"  K0={k:5.2f}  R_locked={rl:.3f}  R_random={rr:.3f}  gap={rl-rr:+.3f}")
    print("--- SUMMARY ---")
    print("FORWARD final R at K0=6:", round(float(Rf[-1]), 3))
    print("BACKWARD collapse K0 (R>0.5):", Kc_back)
    print("Hysteresis gap at collapse (R_back - R_fwd):", round(gap_at, 3) if gap_at else None)
    print("BACKWARD max R (peak of sustained branch):", round(float(Rb_s.max()), 3))
    print("Max forward/backward gap overall:", round(max_gap, 3))
    # where does locked-init collapse in bistability probe?
    lock_collapse = Pk[Prl > 0.5].min() if np.any(Prl > 0.5) else None
    print("Bistab-probe locked-init collapse K0 (R>0.5):", lock_collapse)
    print("Elapsed (s):", round(time.time() - t0, 1))

    # plot
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    ax = axes[0]
    ax.plot(Kf, Rf, 'o-', color='tab:blue', label='Forward (random init)')
    ax.plot(Kb_s, Rb_s, 's-', color='tab:red', label='Backward (sync init, sweep)')
    ax.plot(Pk, Prl, '^--', color='tab:green', label='Locked-init, T_long=400')
    ax.plot(Pk, Prt, 'v--', color='tab:gray', label='Random-init, T_long=400')
    ax.axhline(0.5, ls=':', color='k', alpha=0.5)
    if Kc_back is not None:
        ax.axvline(Kc_back, ls='--', color='red', alpha=0.6,
                   label=f'backward collapse K0={Kc_back:.2f}')
    ax.set_xlabel('K0'); ax.set_ylabel('Order parameter R'); ax.set_ylim(-0.05, 1.05)
    ax.set_title('Kuramoto Keff=K0*R^2 : Forward vs Backward (tencent_hy3 Probe III)')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax2 = axes[1]
    ax2.plot(Kb_s, Rb_s, 's-', color='tab:red', label='Backward sweep R')
    ax2.plot(Pk, Prl, '^--', color='tab:green', label='Locked-init long relax R')
    ax2.set_xlabel('K0'); ax2.set_ylabel('R')
    ax2.set_title('Backward / locked-branch detail'); ax2.legend(fontsize=8); ax2.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('kuramoto_loop.png', dpi=110)
    print("SAVED kuramoto_loop.png")

if __name__ == '__main__':
    main()
