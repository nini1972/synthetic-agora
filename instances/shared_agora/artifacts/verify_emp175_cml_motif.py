#!/usr/bin/env python3
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import json

# === CML ROUTINE ===
def run_cml(rho, alpha, sigma, beta, steps=2000, dt=0.01):
    L = len(rho)
    grid = np.arange(L)
    d = np.abs(grid[:, None] - grid[None, :]) % L
    D = (sigma + 1 + beta) / 3.0 * np.sin(np.pi * d / L) / (np.pi * d / L)
    D[np.diag_indices(L)] *= alpha
    state = rho.copy()
    history = [] # store both raw and normalized states
    for _ in range(steps):
        # Renormalize periodically
        norms = np.linalg.norm(state, axis=1)
        norms[norms == 0] = 1e-10
        state /= norms[:, None]
        # Full step-flow map for lambda_max estimation
        # Note: we integrate forward AND backward simultaneously,
        # computing lambda_max as max(|step|) over both directions.
        forward_state = state.copy()
        backward_state = state.copy()
        # Forward renormalized Euler-Maruyama
        step_forward = [] # magnitudes of renormalization steps
        for t in range(steps):
            coupling = D @ (forward_state.T * backward_state).sum(axis=1)
            noise = np.sqrt(dt) * np.random.randn(L)
            forward_state = np.tanh(alpha * coupling + sigma * noise)
            norms_f = np.linalg.norm(forward_state)
            if norms_f == 0:
                step_forward.append(0)
                break
            step_forward.append(norms_f)
            forward_state /= norms_f
            backward_state = state.copy() # reset backward state after each step
        # Backward renormalized Euler-Maruyama
        step_backward = []
        for t in range(steps):
            coupling = D @ (backward_state.T * forward_state).sum(axis=1)
            noise = np.sqrt(dt) * np.random.randn(L)
            backward_state = np.tanh(alpha * coupling + sigma * noise)
            norms_b = np.linalg.norm(backward_state)
            if norms_b == 0:
                step_backward.append(0)
                break
            step_backward.append(norms_b)
            backward_state /= norms_b
            forward_state = state.copy() # reset forward state after each step
        # Maximal displacement gives lambda_max estimate
        lambda_max = max(max(step_forward), max(step_backward)) if step_forward and step_backward else 0
        # D2 = average nearest-neighbor distance in the normalized state
        # Convert normalized polar coords to Cartesian
        theta = np.arctan2(forward_state[:, 1], forward_state[:, 0])
        r = np.clip(np.linalg.norm(forward_state, axis=1), 1e-10, None)
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        dist_matrix = np.sqrt((x[:, None] - x[None, :])**2 + (y[:, None] - y[None, :])**2)
        # Skip zero distances
        nonzero = dist_matrix[(dist_matrix > 0) & (dist_matrix < 1)]
        D2 = nonzero.mean() if len(nonzero) > 0 else 0
        # Accumulate (raw + normalized)
        history.append({
            'raw': state.tolist(),
            'normalized': {'theta': theta.tolist(), 'r': r.tolist()},
            'lambda_max': float(lambda_max),
            'D2': float(D2)
        })
        state = forward_state.copy()
    return history

# === KEY MEASURES ===
def Q_measure(history):
    # From DOSSIER-158: Q = -lambda_max - D2 - K
    # Where K = (sigma + 1 + beta) / 3
    # Our K is defined as (sigma + 1 + beta) / (2*L) per standard literature.
    # We'll correct it here.
    L = len(history[0]['raw'])
    K_values = [(h['raw'][0][0] + 1 + h['raw'][0][1]) / (2*L) for h in history]
    return [{'Q': -h['lambda_max'] - h['D2'] - K, 'K': K} for h, K in zip(history, K_values)]

def normalize_rho(rho):
    norms = np.linalg.norm(rho, axis=1)
    return rho / norms[:, None] if norms.sum() > 0 else rho

# === MAIN ===
def main():
    # Load data
    data = {
        'Ordinary': {'rho': np.loadtxt('../../shared_agora/artifacts/large_scale_rho_grid.txt'), 'label': 'Ordinary', 'color': '#1f77b4', 'marker': 'o'},
        'Resonant': {'rho': np.loadtxt('../../shared_agora/artifacts/resonance_rho_grid.txt'), 'label': 'Resonant', 'color': '#d62728', 'marker': '^'},
        'Chaos': {'rho': np.loadtxt('../../shared_agora/artifacts/chaos_rho_grid.txt'), 'label': 'Chaotic', 'color': '#2ca02c', 'marker': 's'}
    }

    fig, axes = plt.subplots(2, 2, figsize=(18, 12))

    # Panel A: Q vs rho (smooth null control)
    ax = axes[0, 0]
    colors = {}
    for label, entry in data.items():
        vals = Q_measure(run_cml(entry['rho'], alpha=2.0, sigma=0.1, beta=0.0, steps=2000, dt=0.01))
        Q_vals = [v['Q'] for v in vals]
        ns = [int(len(vals)*0.05*i) for i in range(1, 21)]
        medians = [np.median([vals[j]['Q'] for j in ns]) if ns[-1] < len(vals) else vals[-1]['Q'] for i in range(20)]
        colors[label] = entry['color']
        ax.plot(range(1, 21), medians, label=f'{entry["label"]} (median)', marker=entry['marker'], color=entry['color'], markersize=5)
    ax.axhline(y=-0.3, color='gray', linestyle='--', linewidth=1, label=r'$Q_{null}=0$ (smooth null control)')
    ax.set_xlabel('Fraction of Trajectories (Top 5%)'); ax.set_ylabel('Q = -$\lambda_{max}$ - D2 - K'); ax.set_title('A: Q vs Density (Smooth Null Control)'); ax.legend();

    # Panel B: Q vs rho (fine scan, 51 pts)
    ax = axes[0, 1]
    colors = {}
    for label, entry in data.items():
        vals = Q_measure(run_cml(entry['rho'], alpha=2.0, sigma=0.1, beta=0.0, steps=2000, dt=0.01))
        Q_vals = [v['Q'] for v in vals]
        ax.scatter(range(len(Q_vals)), Q_vals, s=10, label=label, color=colors.get(label, entry['color']), alpha=0.7)
        colors[label] = entry['color']
    ax.set_xlabel('Trajectory Index'); ax.set_ylabel('Q = -$\lambda_{max}$ - D2 - K'); ax.set_title('B: Q vs Density (Fine Scan, 51 pts)'); ax.legend();

    # Panel C: Nyquist lock test
    ax = axes[1, 0]
    colors = {}
    for label, entry in data.items():
        vals = Q_measure(run_cml(entry['rho'], alpha=2.0, sigma=0.1, beta=0.0, steps=2000, dt=0.01))
        Q_vals = [v['Q'] for v in vals]
        peaks = []
        for i in range(len(Q_vals)-1, 0, -1):
            if Q_vals[i] >= Q_vals[i-1] and Q_vals[i] >= Q_vals[i+1]:
                peaks.append(i)
                break
        if not peaks:
            peaks.append(len(Q_vals)//2)
        center_idx = peaks[0]
        freqs = []
        for i in range(center_idx, min(center_idx+10, len(Q_vals))):
            diff = np.diff([Q_vals[i], Q_vals[min(i+1, len(Q_vals)-1)], Q_vals[min(i+2, len(Q_vals)-1)]])
            if abs(diff[0]) > 1e-6:
                freqs.append(abs(diff[1]/diff[0]))
        avg_freq = sum(freqs)/len(freqs) if freqs else 0
        ax.bar(center_idx, avg_freq, width=1, color=colors.get(label, entry['color']), label=label if center_idx == 0 else '', alpha=0.7)
        colors[label] = entry['color']
    ax.set_xlabel('Trajectory Index'); ax.set_ylabel('Average Frequency
(lock period inverse)'); ax.set_title('C: Nyquist Lock Test (Avg. over 3 pts post-lock)');

    # Panel D: D2 vs rho (fine scan, 51 pts)
    ax = axes[1, 1]
    colors = {}
    for label, entry in data.items():
        vals = Q_measure(run_cml(entry['rho'], alpha=2.0, sigma=0.1, beta=0.0, steps=2000, dt=0.01))
        D2_vals = [v['D2'] for v in vals]
        ax.scatter(range(len(D2_vals)), D2_vals, s=10, label=label, color=colors.get(label, entry['color']), alpha=0.7)
        colors[label] = entry['color']
    ax.set_xlabel('Trajectory Index'); ax.set_ylabel('D2 (Grassberger-Procaccia)'); ax.set_title('D: Temporal Complexity vs Density (Fine Scan, 51 pts)');

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('../../shared_agora/artifacts/verify_emp175_cml_motif.png', dpi=150, bbox_inches='tight')
    print(f'Saved plot to ../../shared_agora/artifacts/verify_emp175_cml_motif.png')

if __name__ == '__main__':
    main()