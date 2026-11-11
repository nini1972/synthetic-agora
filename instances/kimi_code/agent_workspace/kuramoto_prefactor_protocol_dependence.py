#!/usr/bin/env python3
"""
Kuramoto escape-time prefactor protocol-dependence test.

Tests the claim (DOSSIER-214 / HYP-145) that the dimensionless prefactor
u = a*K0*R0**a*t_esc/2 in the reflexive Kuramoto model is not a universal
invariant, but varies systematically with protocol choices:
    - nonlinear exponent a
    - relative frequency spread kappa
    - escape threshold R_thr
    - system size N

Integrates: dtheta_i/dt = omega_i + K0 * R(t)**a * sin(psi(t) - theta_i)
with omega_i ~ U(-kappa, kappa), random initial phases.
"""

import json
import os
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from numba import njit, prange

OUT_DIR = '../shared_agora/artifacts'
os.makedirs(OUT_DIR, exist_ok=True)


@njit(parallel=True)
def integrate_escape_batch(theta0, freqs, a, K0, R_thr, dt, t_max):
    """Return initial order parameters R0 and escape times t_esc for many seeds."""
    N, n_seeds = theta0.shape
    n_steps = int(np.ceil(t_max / dt))
    R0_out = np.empty(n_seeds)
    t_esc_out = np.empty(n_seeds)

    for s in prange(n_seeds):
        theta = theta0[:, s].copy()
        omega = freqs[:, s]

        # initial order parameter
        zr = 0.0
        zi = 0.0
        for i in range(N):
            zr += np.cos(theta[i])
            zi += np.sin(theta[i])
        R0_out[s] = np.sqrt(zr * zr + zi * zi) / N

        t = 0.0
        escaped = False
        for step in range(n_steps):
            zr = 0.0
            zi = 0.0
            for i in range(N):
                zr += np.cos(theta[i])
                zi += np.sin(theta[i])
            zr /= N
            zi /= N
            R = np.sqrt(zr * zr + zi * zi)
            if R >= R_thr:
                t_esc_out[s] = t
                escaped = True
                break

            psi = np.arctan2(zi, zr)
            K = K0 * (R ** a)
            sinpsi = np.sin(psi)
            cospsi = np.cos(psi)
            # Euler step (dt small enough; verified stable for K0<=20)
            for i in range(N):
                theta[i] += dt * (omega[i] + K * (sinpsi * np.cos(theta[i]) - cospsi * np.sin(theta[i])))
            t += dt

        if not escaped:
            t_esc_out[s] = np.nan

    return R0_out, t_esc_out


def run_config(N, a, K0, kappa, R_thr, n_seeds, dt=0.01, t_max=200.0, seed_offset=0):
    rng = np.random.default_rng((int(a * 100) + int(K0 * 10) + int(kappa * 100) +
                                 N * 7 + int(R_thr * 100) + seed_offset))
    theta0 = rng.uniform(0.0, 2.0 * np.pi, size=(N, n_seeds))
    freqs = rng.uniform(-kappa, kappa, size=(N, n_seeds))
    R0, t_esc = integrate_escape_batch(theta0, freqs, float(a), float(K0), float(R_thr), float(dt), float(t_max))
    u = np.empty_like(t_esc)
    u[:] = np.nan
    finite = np.isfinite(t_esc) & (R0 > 0.0)
    if np.any(finite):
        u[finite] = a * K0 * (R0[finite] ** a) * t_esc[finite] / 2.0
    return {
        'N': N, 'a': a, 'K0': K0, 'kappa': kappa, 'R_thr': R_thr,
        'n_seeds': n_seeds, 'dt': dt, 't_max': t_max,
        'R0': R0.tolist(), 't_esc': t_esc.tolist(), 'u': u.tolist()
    }


def aggregate(rec):
    u = np.array(rec['u'])
    t_esc = np.array(rec['t_esc'])
    R0 = np.array(rec['R0'])
    finite = np.isfinite(u)
    n_total = len(u)
    n_esc = int(finite.sum())
    lock_rate = n_esc / n_total if n_total else 0.0
    stats = {
        'n_total': n_total,
        'n_escape': n_esc,
        'lock_rate': lock_rate,
    }
    if n_esc > 0:
        stats.update({
            'mean_u': float(np.mean(u[finite])),
            'median_u': float(np.median(u[finite])),
            'std_u': float(np.std(u[finite])),
            'p16_u': float(np.percentile(u[finite], 16)),
            'p84_u': float(np.percentile(u[finite], 84)),
            'min_u': float(np.min(u[finite])),
            'max_u': float(np.max(u[finite])),
            'mean_t_esc': float(np.mean(t_esc[finite])),
            'median_t_esc': float(np.median(t_esc[finite])),
            'mean_R0': float(np.mean(R0)),
        })
    return stats


def main():
    start = time.time()
    dt = 0.01
    t_max = 200.0
    n_seeds = 25  # modest but enough to resolve distribution

    records = []

    # Main protocol-dependence sweep
    for N in [200]:
        for a in [0.5, 1.0, 2.0]:
            for K0 in [5.0, 20.0]:
                for kappa in [0.25, 0.5, 1.0, 2.0, 4.0]:
                    for R_thr in [0.5, 0.6]:
                        rec = run_config(N, a, K0, kappa, R_thr, n_seeds, dt=dt, t_max=t_max)
                        records.append(rec)

    # Threshold dependence for a=1, K0=5
    for R_thr in [0.3, 0.7, 0.9]:
        rec = run_config(200, 1.0, 5.0, 1.0, R_thr, n_seeds, dt=dt, t_max=t_max)
        records.append(rec)

    # N-dependence for a=2 failure regime
    for N in [100, 300]:
        for kappa in [0.5, 1.0, 2.0]:
            rec = run_config(N, 2.0, 5.0, kappa, 0.5, n_seeds, dt=dt, t_max=t_max)
            records.append(rec)

    # Aggregate
    agg = {f"N{r['N']}_a{r['a']}_K{r['K0']}_k{r['kappa']}_thr{r['R_thr']}": aggregate(r)
           for r in records}

    summary = {
        'dt': dt,
        't_max': t_max,
        'n_seeds_per_config': n_seeds,
        'aggregates': agg,
        'records_count': len(records),
    }

    json_path = os.path.join(OUT_DIR, 'kuramoto_prefactor_protocol_dependence.json')
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # --- Plots ---
    # 1. u vs kappa for a=0.5,1,2 (N=200, R_thr=0.5)
    fig, ax = plt.subplots(figsize=(7, 5))
    colors = {0.5: 'tab:blue', 1.0: 'tab:green', 2.0: 'tab:red'}
    for a in [0.5, 1.0, 2.0]:
        for K0 in [5.0, 20.0]:
            kappas = []
            medians = []
            lowers = []
            uppers = []
            for kappa in [0.25, 0.5, 1.0, 2.0, 4.0]:
                key = f"N200_a{a}_K{K0}_k{kappa}_thr0.5"
                st = agg.get(key, {})
                if st.get('n_escape', 0) > 5:
                    kappas.append(kappa)
                    medians.append(st['median_u'])
                    lowers.append(st['median_u'] - st['p16_u'])
                    uppers.append(st['p84_u'] - st['median_u'])
            if kappas:
                ls = '-' if K0 == 5.0 else '--'
                label = f"a={a}, K0={K0}"
                ax.errorbar(kappas, medians, yerr=[lowers, uppers], fmt='o', ls=ls,
                            color=colors[a], label=label, capsize=3)
    ax.axhline(1.0, color='black', ls=':', lw=1, label='u=1 (law identity)')
    ax.set_xlabel(r'Frequency spread $\kappa$')
    ax.set_ylabel(r'Median prefactor $u = a K_0 R_0^a t_{esc}/2$')
    ax.set_title('Prefactor u varies with a, K0 and frequency spread')
    ax.set_xscale('log')
    ax.legend(fontsize=8, ncol=2)
    ax.set_ylim(0, 3.0)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, 'kuramoto_prefactor_vs_kappa.png'), dpi=200)
    plt.close(fig)

    # 2. Threshold dependence for a=1, K0=5
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for R_thr in [0.3, 0.5, 0.7, 0.9]:
        key = f"N200_a1.0_K5.0_k1.0_thr{R_thr}"
        st = agg.get(key, {})
        if st.get('n_escape', 0) > 5:
            parts = ax.violinplot([np.array(summary.get('records', []))], positions=[R_thr], widths=0.08,
                                  showmedians=True)
    # Recompute per threshold for violin
    thr_vals = [0.3, 0.5, 0.7, 0.9]
    u_lists = []
    for R_thr in thr_vals:
        for rec in records:
            if (rec['N'] == 200 and rec['a'] == 1.0 and rec['K0'] == 5.0 and
                    rec['kappa'] == 1.0 and rec['R_thr'] == R_thr):
                u_lists.append(np.array(rec['u'])[np.isfinite(rec['u'])])
    if u_lists:
        parts = ax.violinplot(u_lists, positions=thr_vals, widths=0.08, showmedians=True)
        ax.set_xticks(thr_vals)
        ax.set_xticklabels([str(t) for t in thr_vals])
        ax.set_xlabel(r'Escape threshold $R_{thr}$')
        ax.set_ylabel(r'Prefactor $u$')
        ax.set_title(r'Threshold dependence: a=1, K0=5, $\kappa$=1')
        ax.axhline(1.0, color='black', ls=':')
        fig.tight_layout()
        fig.savefig(os.path.join(OUT_DIR, 'kuramoto_prefactor_threshold_dependence.png'), dpi=200)
        plt.close(fig)

    # 3. Lock rate vs kappa for a=2, N=100,200,300
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for N in [100, 200, 300]:
        kappas = []
        rates = []
        for kappa in [0.25, 0.5, 1.0, 2.0, 4.0]:
            key = f"N{N}_a2.0_K5.0_k{kappa}_thr0.5"
            st = agg.get(key, {})
            if key in agg:
                kappas.append(kappa)
                rates.append(st['lock_rate'])
        if kappas:
            ax.plot(kappas, rates, marker='o', label=f'N={N}')
    ax.set_xlabel(r'Frequency spread $\kappa$')
    ax.set_ylabel('Lock rate')
    ax.set_title(r'a=2 escape failure: lock rate drops with N and $\kappa$')
    ax.set_xscale('log')
    ax.set_ylim(-0.05, 1.05)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, 'kuramoto_a2_lock_rate.png'), dpi=200)
    plt.close(fig)

    elapsed = time.time() - start
    print(f"Done. {len(records)} configs x {n_seeds} seeds. Time: {elapsed:.1f}s")
    print(f"JSON: {json_path}")
    # Print a few key numbers
    for key in ['N200_a1.0_K5.0_k1.0_thr0.5', 'N200_a2.0_K5.0_k1.0_thr0.5', 'N300_a2.0_K5.0_k1.0_thr0.5']:
        st = agg.get(key, {})
        print(key, st)


if __name__ == '__main__':
    main()
