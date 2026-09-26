"""Verify Dossier-076: IC complexity underestimation in elementary CA.

Does random initialization reveal significantly more temporal complexity
than single-point initialization for the same CA rules?

Metrics: 2x2 Block Shannon Entropy (spatial), Temporal Lempel-Ziv Complexity
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def apply_ca(rule, state):
    """Apply elementary CA rule to state."""
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
    """Run CA and return trajectory."""
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

def shannon_entropy(data):
    """Shannon entropy of a distribution."""
    if len(data) == 0 or np.sum(data) == 0:
        return 0.0
    p = data / np.sum(data)
    p = p[p > 0]
    return -np.sum(p * np.log2(p))

def block_entropy_2x2(trajectory, N):
    """2x2 block Shannon entropy of trajectory (averaged over rows)."""
    T = len(trajectory)
    counts = np.zeros(16, dtype=int)
    for t in range(T):
        row = trajectory[t]
        for i in range(N):
            c00 = row[i]
            c10 = row[(i+1) % N]
            c01 = trajectory[(t+1) % T][i]
            c11 = trajectory[(t+1) % T][(i+1) % N]
            idx = c00 + 2*c10 + 4*c01 + 8*c11
            counts[idx] += 1
    return shannon_entropy(counts.astype(float))

def lempel_ziv_complexity(binary_string):
    """Lempel-Ziv complexity (number of distinct substrings)."""
    s = ''.join(map(str, binary_string))
    n = len(s)
    if n == 0:
        return 0
    complexity = 1
    i = 0
    l = 1
    while i + l <= n:
        substr = s[i:i+l]
        # Check if substr appears in s[0:i+l-1]
        found = False
        for j in range(max(0, i - l + 1), i):
            if s[j:j+l] == substr:
                found = True
                break
        if found:
            l += 1
            if i + l > n:
                break
        else:
            i += l
            l = 1
            complexity += 1
    return complexity

def temporal_lz(trajectory):
    """Temporal Lempel-Ziv: treat column dynamics as binary string."""
    T, N = trajectory.shape
    # Concatenate first 10 columns
    cols = min(10, N)
    binary_seq = []
    for c in range(cols):
        binary_seq.extend(trajectory[:, c].tolist())
    return lempel_ziv_complexity(binary_seq)

np.random.seed(42)

# Rules to test
rules = [18, 22, 26, 30, 54, 62, 90, 94, 102, 110, 126, 150, 158, 182, 190]
N = 100
T = 100

results = {}
for rule in rules:
    lz_single = []
    lz_random = []
    be_single = []
    be_random = []
    
    for trial in range(3):
        traj_s = simulate_ca(rule, N, T, 'single')
        traj_r = simulate_ca(rule, N, T, 'random')
        
        lz_single.append(temporal_lz(traj_s))
        lz_random.append(temporal_lz(traj_r))
        be_single.append(block_entropy_2x2(traj_s, N))
        be_random.append(block_entropy_2x2(traj_r, N))
    
    results[rule] = {
        'lz_single': np.mean(lz_single),
        'lz_random': np.mean(lz_random),
        'be_single': np.mean(be_single),
        'be_random': np.mean(be_random),
        'lz_ratio': np.mean(lz_random) / max(np.mean(lz_single), 1)
    }
    print(f"R{rule:3d}: LZ_single={results[rule]['lz_single']:.1f}, LZ_random={results[rule]['lz_random']:.1f}, "
          f"ratio={results[rule]['lz_ratio']:.2f}x | "
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