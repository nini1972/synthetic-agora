"""
EMP-043: Thomas Attractor - Edge-of-Chaos Resolution (Optimized)
Resolving DOSSIER_002 vs EMP-035/EMP-040

Key question: Where exactly does entropy/complexity peak on the Thomas attractor?
DOSSIER_002 claims b_c ≈ 0.208 with H(S) peaking there.
EMP-035/040 claim LZ peaks at LOW b (b→0), entropy at b_c ≈ 0.20.
"""
import sys, os, json
import numpy as np
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# ── Thomas attractor core ──
def thomas_rhs(state, b):
    x, y, z = state
    return np.array([np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z])

def rk4_step(state, dt, b):
    k1 = thomas_rhs(state, b)
    k2 = thomas_rhs(state + 0.5*dt*k1, b)
    k3 = thomas_rhs(state + 0.5*dt*k2, b)
    k4 = thomas_rhs(state + dt*k3, b)
    return state + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

def thomas_jacobian(state, b):
    x, y, z = state
    return np.array([[-b, np.cos(y), 0], [0, -b, np.cos(z)], [np.cos(x), 0, -b]])

def compute_lyapunov(b, dt=0.02, T_transient=150, T_measure=400, seed=42):
    """Compute full Lyapunov spectrum."""
    rng = np.random.default_rng(seed)
    state = rng.standard_normal(3) * 0.5
    Q = np.eye(3)
    renorm_every = int(0.5 / dt)
    for _ in range(int(T_transient/dt)):
        state = rk4_step(state, dt, b)
    lyap_sums = np.zeros(3)
    n_renorms = 0
    for i in range(int(T_measure/dt)):
        state = rk4_step(state, dt, b)
        J = thomas_jacobian(state, b)
        for c in range(3):
            Q[:, c] += dt * (J @ Q[:, c])
        if (i + 1) % renorm_every == 0:
            Q_r, R = np.linalg.qr(Q)
            for k in range(3):
                if abs(R[k,k]) > 0:
                    lyap_sums[k] += np.log(abs(R[k,k]))
            Q = Q_r
            n_renorms += 1
    T_total = n_renorms * renorm_every * dt
    return lyap_sums / T_total if T_total > 0 else np.zeros(3)

def symbolize(traj, n_sym=8, comp=0):
    x = traj[:, comp]
    pcts = np.linspace(0, 100, n_sym + 1)
    bins = np.percentile(x, pcts)
    bins[0], bins[-1] = -np.inf, np.inf
    return np.clip(np.digitize(x, bins) - 1, 0, n_sym - 1)

def block_entropy(symbols, block_size):
    n = len(symbols)
    if n < block_size: return 0.0
    blocks = [tuple(symbols[i:i+block_size]) for i in range(n - block_size + 1)]
    counts = Counter(blocks)
    total = len(blocks)
    return -sum((c/total)*np.log2(c/total) for c in counts.values() if c > 0)

def lz78(symbols):
    """Fast LZ78 complexity via incremental dictionary."""
    s = ''.join(str(int(c)) for c in symbols)
    n = len(s)
    i, w, comp, dictionary = 0, '', 0, set()
    while i < n:
        wc = w + s[i]
        if wc in dictionary:
            w = wc
        else:
            comp += 1
            dictionary.add(wc)
            w = s[i]
        i += 1
    return comp

def perm_entropy(symbols, order=4, delay=1):
    import math
    n = len(symbols)
    if n < order * delay: return 0.0
    patterns = []
    for i in range(n - (order - 1) * delay):
        pattern = tuple(np.argsort([symbols[i + k*delay] for k in range(order)]))
        patterns.append(pattern)
    counts = Counter(patterns)
    total = len(patterns)
    max_H = np.log2(math.factorial(order))
    H = -sum((c/total)*np.log2(c/total) for c in counts.values() if c > 0)
    return H / max_H if max_H > 0 else 0

# ── Parameters (optimized) ──
dt = 0.05
T_transient = 200
T_measure = 300  # 6000 symbolic points

# Strategic b values: dense near edge-of-chaos, sparse elsewhere
bs = np.unique(np.round(np.concatenate([
    np.linspace(0.05, 0.15, 3),       # deep chaotic
    np.linspace(0.15, 0.26, 7),       # edge-of-chaos zone (DOSSIER_002's b_c=0.208)
    np.linspace(0.26, 0.40, 4),       # stable regime
]), 3))
seeds_lyap = [42, 123]
seed_traj = 7

# ── Storage ──
res = dict(b=[], lam1=[], lam1_std=[], lam1_spec=[], H1=[], H2=[], H4=[], H6=[], H8=[],
           lz_raw=[], lz_norm=[], pe=[])

print("="*70)
print("EMP-043: Thomas Attractor - Edge-of-Chaos Resolution")
print("Adjudicating DOSSIER_002 vs EMP-035/EMP-040")
print("="*70)

for idx, b in enumerate(bs):
    print(f"  b={b:.3f} ({idx+1}/{len(bs)})")
    
    # Lyapunov spectrum (2 seeds)
    all_specs = [compute_lyapunov(b, seed=s) for s in seeds_lyap]
    lam1_vals = [sp[0] for sp in all_specs]
    mean_spec = np.mean(all_specs, axis=0)
    
    # Symbolic dynamics
    rng = np.random.default_rng(seed_traj)
    state = rng.standard_normal(3) * 0.5
    for _ in range(int(T_transient/dt)):
        state = rk4_step(state, dt, b)
    traj = np.zeros((int(T_measure/dt), 3))
    for j in range(len(traj)):
        state = rk4_step(state, dt, b)
        traj[j] = state
    sym = symbolize(traj)
    
    res['b'].append(float(b))
    res['lam1'].append(float(mean_spec[0]))
    res['lam1_std'].append(float(np.std(lam1_vals)))
    res['lam1_spec'].append(mean_spec.tolist())
    
    for bs_, key in [(1,'H1'),(2,'H2'),(4,'H4'),(6,'H6'),(8,'H8')]:
        res[key].append(block_entropy(sym, bs_))
    
    lz = lz78(sym)
    lz_n = len(sym) / np.log2(len(sym))
    res['lz_raw'].append(int(lz))
    res['lz_norm'].append(float(lz / lz_n))
    res['pe'].append(perm_entropy(sym, order=4))

print("\nComputation done!")
with open('thomas_eoc_results_v3.json', 'w') as f:
    json.dump(res, f)

# ── Analysis ──
b_arr = np.array(res['b'])
lam_arr = np.array(res['lam1'])
lz_arr = np.array(res['lz_norm'])
pe_arr = np.array(res['pe'])
H4_arr = np.array(res['H4'])

eoc_mask = np.abs(lam_arr) < 0.015
if eoc_mask.any():
    eoc_b = b_arr[eoc_mask]
    print(f"\nEdge-of-chaos region (|lambda1| < 0.015): b in [{eoc_b.min():.3f}, {eoc_b.max():.3f}]")
    print(f"  DOSSIER_002 claimed b_c = 0.208")
    print(f"  EMP-035/040 claimed b_c ≈ 0.20")

print(f"\nMetric peaks:")
print(f"  LZ complexity peak at b = {b_arr[np.argmax(lz_arr)]:.3f} (lambda1 = {lam_arr[np.argmax(lz_arr)]:.4f})")
print(f"  Permutation entropy peak at b = {b_arr[np.argmax(pe_arr)]:.3f} (lambda1 = {lam_arr[np.argmax(pe_arr)]:.4f})")
print(f"  Block entropy H(4) peak at b = {b_arr[np.argmax(H4_arr)]:.3f} (lambda1 = {lam_arr[np.argmax(H4_arr)]:.4f})")

# ── Visualization ──
fig = plt.figure(figsize=(18, 28))
gs = GridSpec(6, 1, figure=fig, hspace=0.35)
std_arr = np.array(res['lam1_std'])

ax1 = fig.add_subplot(gs[0])
ax1.fill_between(b_arr, lam_arr - std_arr, lam_arr + std_arr, alpha=0.3, color='gray')
ax1.plot(b_arr, lam_arr, 'ko-', ms=4, lw=1.5, label='lambda1 mean ± std')
ax1.axhline(0, color='red', ls='--', lw=2)
ax1.axvline(0.208, color='green', ls=':', lw=2, label='b_c=0.208 (DOSSIER_002)')
for i in range(len(b_arr)-1):
    c = 'red' if lam_arr[i] > 0.01 else ('blue' if lam_arr[i] < -0.01 else 'green')
    ax1.axvspan(b_arr[i], b_arr[i+1], alpha=0.08, color=c)
ax1.set_xlabel('b', fontsize=12)
ax1.set_ylabel('lambda_1', fontsize=12)
ax1.set_title('Panel 1: Largest Lyapunov Exponent (Ground Truth)\nRed=chaotic, Blue=stable, Green=marginal', fontsize=13)
ax1.legend(fontsize=11)

ax2 = fig.add_subplot(gs[1])
lams = np.array(res['lam1_spec'])
for k in range(3):
    ax2.plot(b_arr, lams[:, k], 'o-', ms=3, lw=1, label=f'lambda_{k+1}')
ax2.axhline(0, color='red', ls='--', alpha=0.5)
ax2.axvline(0.208, color='green', ls=':', alpha=0.5)
ax2.set_xlabel('b')
ax2.set_ylabel('Lyapunov Exponents')
ax2.set_title('Panel 2: Full Lyapunov Spectrum')
ax2.legend()

ax3 = fig.add_subplot(gs[2])
for key, lbl, col in [('H1','H(1)','#e74c3c'),('H2','H(2)','#e67e22'),
                       ('H4','H(4)','#27ae60'),('H6','H(6)','#2980b9'),('H8','H(8)','#8e44ad')]:
    ax3.plot(b_arr, np.array(res[key]), 'o-', color=col, ms=3, lw=1.5, label=lbl)
ax3.axvline(0.208, color='green', ls=':', lw=2, label='b_c=0.208')
ax3.set_xlabel('b')
ax3.set_ylabel('Block Entropy (bits)')
ax3.set_title('Panel 3: Block Entropy at Multiple Block Sizes\n(DOSSIER_002: H peaks at edge-of-chaos)')
ax3.legend(ncol=3, fontsize=9)

ax4 = fig.add_subplot(gs[3])
ax4.plot(b_arr, lz_arr, 'o-', color='#e74c3c', ms=4, lw=1.5, label='Normalized LZ78')
ax4.axvline(0.208, color='green', ls=':', lw=2, label='b_c=0.208')
ax4.set_xlabel('b')
ax4.set_ylabel('Normalized LZ Complexity')
ax4.set_title('Panel 4: Lempel-Ziv Complexity\n(EMP-035 claims LZ peaks at LOW b)')
ax4.legend()

ax5 = fig.add_subplot(gs[4])
ax5.plot(b_arr, pe_arr, 'o-', color='#8e44ad', ms=4, lw=1.5, label='Permutation Entropy')
ax5.axvline(0.208, color='green', ls=':', lw=2, label='b_c=0.208')
ax5.set_xlabel('b')
ax5.set_ylabel('Normalized Perm Entropy')
ax5.set_title('Panel 5: Permutation Entropy (order=4)')
ax5.legend()

ax6 = fig.add_subplot(gs[5])
def norm(x): return (x - x.min()) / (x.max() - x.min() + 1e-10)
ax6.plot(b_arr, norm(lam_arr), 'k-', lw=2.5, label='lambda1')
ax6.plot(b_arr, norm(lz_arr), 'r-', lw=2.5, label='LZ78')
ax6.plot(b_arr, norm(pe_arr), color='purple', lw=2.5, label='Perm Entropy')
ax6.plot(b_arr, norm(H4_arr), 'g-', lw=2.5, label='H(4)')
ax6.axvline(0.208, color='green', ls=':', lw=2, label='b_c=0.208')
ax6.axvspan(0.15, 0.25, alpha=0.1, color='green')
ax6.set_xlabel('b')
ax6.set_ylabel('Normalized Value')
ax6.set_title('Panel 6: All Metrics Normalized and Overlaid')
ax6.legend(fontsize=11)

plt.suptitle('EMP-043: Thomas Attractor Edge-of-Chaos Resolution\nResolving DOSSIER_002 vs EMP-035/EMP-040', fontsize=16, y=0.98)
plt.savefig('thomas_eoc_resolution_v3.png', dpi=150, bbox_inches='tight')
print("\nSaved: thomas_eoc_resolution_v3.png")
plt.close()
