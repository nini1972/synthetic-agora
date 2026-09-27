"""Verify Dossier-076: IC complexity underestimation in elementary CA.
Corrected Lempel-Ziv implementation.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def apply_ca(rule, state):
    N = len(state)
    new = np.zeros(N, dtype=int)
    for i in range(N):
        left = state[(i-1) % N]
        center = state[i]
        right = state[(i+1) % N]
        pattern = (left << 2) | (center << 1) | right
        new[i] = (rule >> pattern) & 1
    return new

def simulate_ca(rule, N, T, ic_type='single'):
    if ic_type == 'single':
        state = np.zeros(N, dtype=int)
        state[N // 2] = 1
    elif ic_type == 'random':
        state = (np.random.random(N) < 0.5).astype(int)
    
    trajectory = np.zeros((T, N), dtype=int)
    trajectory[0] = state
    for t in range(1, T):
        state = apply_ca(rule, state)
        trajectory[t] = state
    return trajectory

def lz76_complexity(s):
    """LZ76 complexity: count distinct substrings using dictionary.
    Standard Lempel-Ziv 1976 parsing."""
    n = len(s)
    if n == 0:
        return 0
    i = 0
    c = 1  # at least one word
    while i < n:
        l = 1  # start with length 1
        # Find longest match in dictionary (positions 0..i-1)
        while i + l <= n:
            w = s[i:i+l]
            found = False
            # Search for w in s[0:i]
            for j in range(0, i):
                if j + l <= i and s[j:j+l] == w:
                    found = True
                    break
            if found and i + l <= n:
                l += 1
            else:
                break
        # The word s[i:i+l] is new
        i += l
        c += 1
    return c

def block_entropy_2x2(trajectory, N):
    """2x2 block Shannon entropy."""
    T = len(trajectory)
    counts = np.zeros(16, dtype=int)
    for t in range(T - 1):
        row = trajectory[t]
        row_next = trajectory[t + 1]
        for i in range(N):
            c00 = row[i]
            c10 = row[(i+1) % N]
            c01 = row_next[i]
            c11 = row_next[(i+1) % N]
            idx = c00 + 2*c10 + 4*c01 + 8*c11
            counts[idx] += 1
    total = np.sum(counts)
    p = counts[counts > 0].astype(float) / total
    return -np.sum(p * np.log2(p))

def temporal_lz(trajectory, n_cols=1):
    """Temporal LZ: concatenate first n_cols time-series columns."""
    T, N = trajectory.shape
    binary_seq = []
    for c in range(min(n_cols, N)):
        binary_seq.extend(trajectory[:, c].tolist())
    s = ''.join(map(str, binary_seq))
    return lz76_complexity(s)

np.random.seed(42)

rules = [18, 22, 26, 30, 54, 62, 90, 94, 102, 110, 126, 150, 158, 182, 190]
N = 100
T = 100
n_trials = 3

results = {}
for rule in rules:
    lz_single = []
    lz_random = []
    be_single = []
    be_random = []
    
    for trial in range(n_trials):
        traj_s = simulate_ca(rule, N, T, 'single')
        traj_r = simulate_ca(rule, N, T, 'random')
        
        lz_single.append(temporal_lz(traj_s, n_cols=3))
        lz_random.append(temporal_lz(traj_r, n_cols=3))
        be_single.append(block_entropy_2x2(traj_s, N))
        be_random.append(block_entropy_2x2(traj_r, N))
    
    lz_s = np.mean(lz_single)
    lz_r = np.mean(lz_random)
    ratio = lz_r / max(lz_s, 1)
    results[rule] = {
        'lz_single': lz_s,
        'lz_random': lz_r,
        'be_single': np.mean(be_single),
        'be_random': np.mean(be_random),
        'lz_ratio': ratio
    }
    print(f"R{rule:3d}: LZ_single={lz_s:.1f}, LZ_random={lz_r:.1f}, ratio={ratio:.2f}x | "
          f"BE_single={results[rule]['be_single']:.2f}, BE_random={results[rule]['be_random']:.2f}")

ratios = [results[r]['lz_ratio'] for r in rules]
print(f"\nMean complexity ratio: {np.mean(ratios):.2f}x (dossier claims 5.34x)")
print(f"Median: {np.median(ratios):.2f}x")
print(f"Range: [{np.min(ratios):.2f}x, {np.max(ratios):.2f}x]")

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
x = np.arange(len(rules))
width = 0.35

ax1.bar(x - width/2, [results[r]['lz_single'] for r in rules], width, label='Single-point IC', alpha=0.7)
ax1.bar(x + width/2, [results[r]['lz_random'] for r in rules], width, label='Random IC (50%)', alpha=0.7)
ax1.set_xticks(x)
ax1.set_xticklabels([f'R{r}' for r in rules], rotation=45, fontsize=8)
ax1.set_ylabel('Temporal LZ Complexity')
ax1.set_title('LZ Complexity: Single-Point vs Random IC')
ax1.legend()
ax1.grid(True, alpha=0.3, axis='y')

ax2.bar(x, ratios, width, color='crimson', alpha=0.7)
ax2.set_xticks(x)
ax2.set_xticklabels([f'R{r}' for r in rules], rotation=45, fontsize=8)
ax2.set_ylabel('Complexity Ratio (Random/Single)')
ax2.set_title(f'IC Complexity Underestimation\nMean ratio: {np.mean(ratios):.2f}x')
ax2.axhline(y=1.0, color='black', linestyle='--', alpha=0.5)
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('shared_agora/artifacts/ca_ic_complexity.png', dpi=150)
print("\nPlot saved.")