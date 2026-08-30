"""Probe IV (tencent_hy3): Cauchy-frequency test of Kuramoto Keff=K0*R^2 bistability.

Directly mirrors Dossier #001 / EMP-004's stated setup: alpha=2, Cauchy
(Lorentzian) natural frequencies with scale gamma=0.02, N=200. Tests whether the
subcritical bistable hysteresis loop found with NORMAL frequencies (Probe III) is
robust to the exact frequency distribution the dossier used.

 (A) FORWARD random-init sweep UP  -> tests nucleability from incoherence.
 (B) BACKWARD locked-init (th=0) sweep DOWN -> tests survivability of locked branch.
 (C) BISTABILITY PROBE: lock at K0=6, jump to fixed K0, long relax (T_long=400),
     measure steady R for BOTH locked-init and random-init to expose co-existing
     attractors and the true nucleation/collapse points.

Truncations: Cauchy tail capped at |x|<3 (=> |omega|<0.06) so that "fully locked"
persistence is bounded by K0>max|omega| (as in the normal case) and the comparison
is fair. The dossier never specified a tail cutoff, so this mirrors common practice.
"""
import numpy as np
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

N = 200
DT = 0.05
T_TRANS = 25.0
T_MEAS = 12.0
ALPHA = 2.0
GAMMA = 0.02

def steady_R(om, K0, th, ntrans, nmeas):
    ntrans = int(ntrans / DT); nmeas = int(nmeas / DT)
    acc = 0.0; cnt = 0
    for step in range(ntrans + nmeas):
        z = np.mean(np.exp(1j * th)); R = abs(z); psi = np.angle(z)
        Keff = K0 * (R ** ALPHA)
        k1 = om + Keff * R * np.sin(psi - th)
        t2 = th + 0.5 * DT * k1
        z2 = np.mean(np.exp(1j * t2)); R2 = abs(z2); p2 = np.angle(z2)
        k2 = om + (K0 * (R2 ** ALPHA)) * R2 * np.sin(p2 - t2)
        t3 = th + 0.5 * DT * k2
        z3 = np.mean(np.exp(1j * t3)); R3 = abs(z3); p3 = np.angle(z3)
        k3 = om + (K0 * (R3 ** ALPHA)) * R3 * np.sin(p3 - t3)
        t4 = th + DT * k3
        z4 = np.mean(np.exp(1j * t4)); R4 = abs(z4); p4 = np.angle(z4)
        k4 = om + (K0 * (R4 ** ALPHA)) * R4 * np.sin(p4 - t4)
        th = th + (DT / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        if step >= ntrans:
            acc += abs(np.mean(np.exp(1j * th))); cnt += 1
    return acc / cnt, th

def main():
    t0 = time.time()
    rng = np.random.default_rng(7)
    om = []
    while len(om) < N:
        x = rng.standard_cauchy()
        if abs(x) < 3.0:
            om.append(x)
    om = np.array(om) * GAMMA
    print("max|omega| =", round(float(om.max()), 4), " min|omega| =", round(float(-om.min()), 4))

    grid = np.round(np.arange(0.0, 6.01, 0.3), 3)

    # (A) FORWARD random-init sweep UP
    th = rng.uniform(0, 2 * np.pi, N)
    Kf = []; Rf = []
    for K0 in grid:
        r, th = steady_R(om, K0, th, T_TRANS, T_MEAS)
        Kf.append(K0); Rf.append(r)

    # (B) BACKWARD locked-init (th=0) sweep DOWN
    th = np.zeros(N)
    Kb = []; Rb = []
    for K0 in grid[::-1]:
        r, th = steady_R(om, K0, th, T_TRANS, T_MEAS)
        Kb.append(K0); Rb.append(r)

    Kf = np.array(Kf); Rf = np.array(Rf)
    Kb = np.array(Kb); Rb = np.array(Rb)

    # (C) BISTABILITY PROBE
    th0 = np.zeros(N)
    _, th_lock = steady_R(om, 6.0, th0, 80.0, 5.0)
    probe_K = np.array([3.0, 2.0, 1.5, 1.0, 0.7, 0.5, 0.3, 0.2, 0.1])
    Pk = []; Prl = []; Prr = []
    for K0 in probe_K:
        tl = th_lock.copy()
        rl, _ = steady_R(om, K0, tl, 400.0, 20.0)
        tr = rng.uniform(0, 2 * np.pi, N)
        rr, _ = steady_R(om, K0, tr, 400.0, 20.0)
        Pk.append(K0); Prl.append(rl); Prr.append(rr)
    Pk = np.array(Pk); Prl = np.array(Prl); Prr = np.array(Prr)

    # summaries
    print("=== FORWARD (random-init) Cauchy ===")
    for k, r in zip(Kf, Rf):
        print(f"  K0={k:5.2f}  R={r:.3f}")
    print("=== BACKWARD (locked-init) Cauchy ===")
    for k, r in zip(Kb, Rb):
        print(f"  K0={k:5.2f}  R={r:.3f}")
    print("=== BISTABILITY PROBE (Cauchy) locked vs random, T_long=400 ===")
    for k, rl, rr in zip(Pk, Prl, Prr):
        print(f"  K0={k:5.2f}  R_locked={rl:.3f}  R_random={rr:.3f}  gap={rl-rr:+.3f}")

    bsort = sorted(zip(Kb, Rb))
    Kb_s = np.array([x[0] for x in bsort]); Rb_s = np.array([x[1] for x in bsort])
    coll = Kb_s[Rb_s > 0.5]
    Kc_back = coll.min() if len(coll) > 0 else None
    fwd_nuc = Kf[Rf > 0.5].min() if np.any(Rf > 0.5) else None
    lock_coll = Pk[Prl > 0.5].min() if np.any(Prl > 0.5) else None
    print("--- SUMMARY (Cauchy) ---")
    print("Forward random-init nucleation K0 (R>0.5):", fwd_nuc)
    print("Backward sweep collapse K0 (R>0.5):", Kc_back)
    print("Bistab-probe locked-init collapse K0 (R>0.5):", lock_coll)
    print("Elapsed (s):", round(time.time() - t0, 1))

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    ax = axes[0]
    ax.plot(Kf, Rf, 'o-', color='tab:blue', label='Forward (random init)')
    ax.plot(Kb_s, Rb_s, 's-', color='tab:red', label='Backward (locked init, sweep)')
    ax.plot(Pk, Prl, '^--', color='tab:green', label='Locked-init, T_long=400')
    ax.plot(Pk, Prr, 'v--', color='tab:gray', label='Random-init, T_long=400')
    ax.axhline(0.5, ls=':', color='k', alpha=0.5)
    ax.set_xlabel('K0'); ax.set_ylabel('Order parameter R'); ax.set_ylim(-0.05, 1.05)
    ax.set_title('Cauchy Kuramoto Keff=K0*R^2 : Forward vs Backward (tencent_hy3 Probe IV)')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax2 = axes[1]
    ax2.plot(Kb_s, Rb_s, 's-', color='tab:red', label='Backward sweep R')
    ax2.plot(Pk, Prl, '^--', color='tab:green', label='Locked-init long relax R')
    ax2.set_xlabel('K0'); ax2.set_ylabel('R')
    ax2.set_title('Backward / locked-branch detail (Cauchy)'); ax2.legend(fontsize=8); ax2.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('kuramoto_cauchy.png', dpi=110)
    print("SAVED kuramoto_cauchy.png")

if __name__ == '__main__':
    main()
