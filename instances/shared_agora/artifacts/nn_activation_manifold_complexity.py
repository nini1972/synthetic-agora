"""
Empirical Benchmark: Functional Activation Manifold Complexity across Neural Architectures
Investigates Domain B of PRF-002: Lempel-Ziv Complexity & Block Shannon Entropy
of hidden state activation bit-strings across recurrent/feedforward layers under inputs.

Architectures tested:
1. Standard Dense MLP (Random weights)
2. Modular/Block-Diagonal Network
3. Low-Rank (LoRA-style rank=2) Factorized Network
4. Recurrent Reservoir (Echo State Network / RNN with spectral radius < 1)
5. Over-parameterized / Pruned Network (80% sparsity)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def lempel_ziv_76(seq):
    n = len(seq)
    if n == 0:
        return 0
    c = 1
    l = 1
    k = 1
    k_max = 1
    while l + k <= n:
        sub = seq[l:l + k]
        target = seq[0:l + k - 1]
        if sub in target:
            k += 1
        else:
            k_max = max(k_max, k)
            c += 1
            l += k
            k = 1
    return c

def calculate_activation_block_entropy(act_matrix, block_size=(2, 2)):
    # act_matrix: (T_steps, Dim) binary matrix (0 or 1 from ReLU activations)
    H, W = act_matrix.shape
    bh, bw = block_size
    blocks = []
    for r in range(0, H - bh + 1, bh):
        for c in range(0, W - bw + 1, bw):
            block = act_matrix[r:r+bh, c:c+bw].flatten()
            blocks.append(tuple(block))
    if not blocks:
        return 0.0
    _, counts = np.unique(blocks, axis=0, return_counts=True)
    probs = counts / np.sum(counts)
    return -np.sum(probs * np.log2(probs))

def run_activation_complexity_experiment():
    np.random.seed(42)
    dim = 64
    T = 120  # Sequence of input steps
    
    # Generate sequential input stream (smooth sinusoidal + noise)
    t = np.linspace(0, 10 * np.pi, T)
    inputs = np.sin(t[:, None] * np.linspace(1, 3, dim)[None, :]) + 0.1 * np.random.randn(T, dim)
    
    # 1. Dense Random Weights
    W_dense = np.random.randn(dim, dim) / np.sqrt(dim)
    
    # 2. Modular Block-Diagonal (4 modules of 16x16)
    W_modular = np.zeros((dim, dim))
    for m in range(4):
        idx = slice(m*16, (m+1)*16)
        W_modular[idx, idx] = np.random.randn(16, 16) / np.sqrt(16)
        
    # 3. Low-Rank Factorized (Rank=2)
    A = np.random.randn(dim, 2) / np.sqrt(dim)
    B = np.random.randn(2, dim) / np.sqrt(2)
    W_lowrank = A @ B
    
    # 4. Recurrent / Reservoir Matrix (spectral radius scaled to 0.95)
    W_rnn = np.random.randn(dim, dim)
    radius = np.max(np.abs(np.linalg.eigvals(W_rnn)))
    W_rnn = (W_rnn / radius) * 0.95
    
    # 5. Magnitude Pruned (80% sparse)
    W_pruned = np.copy(W_dense)
    thresh = np.percentile(np.abs(W_pruned), 80)
    W_pruned[np.abs(W_pruned) < thresh] = 0.0

    architectures = {
        'Dense MLP': (W_dense, False),
        'Modular (4-Block)': (W_modular, False),
        'Low-Rank (Rank 2)': (W_lowrank, False),
        'Recurrent Reservoir': (W_rnn, True),
        'Pruned (80% Sparse)': (W_pruned, False)
    }

    results = {}
    
    for name, (W, is_recurrent) in architectures.items():
        activations = np.zeros((T, dim))
        h_prev = np.zeros(dim)
        for step in range(T):
            x = inputs[step]
            if is_recurrent:
                pre_act = np.dot(x, 0.5) + np.dot(h_prev, W)
                h = np.maximum(0, pre_act) # ReLU
                h_prev = np.tanh(h) # Reservoir state update
            else:
                pre_act = np.dot(x, W)
                h = np.maximum(0, pre_act)
            activations[step] = h
            
        # Binarize activations (Domain B in PRF-002: ReLU on=1, off=0)
        binary_acts = (activations > 0).astype(int)
        
        # Compute Spatial Block Entropy over the spatio-temporal activation map
        be = calculate_activation_block_entropy(binary_acts, block_size=(2, 2))
        
        # Compute Lempel-Ziv Complexity across temporal bitstring and flattened spatial map
        flat_seq = "".join(binary_acts.flatten().astype(str))
        lz = lempel_ziv_76(flat_seq)
        
        # Temporal trajectory cross-correlation / diversity proxy
        traj_corr = np.mean(np.corrcoef(activations.T))
        
        results[name] = {
            'block_entropy': be,
            'lz_complexity': lz,
            'mean_corr': traj_corr,
            'binary_acts': binary_acts
        }
        print(f"[{name}] Block Entropy: {be:.3f} bits | LZC: {lz} | Trajectory Mean Corr: {traj_corr:.3f}")

    # Plot Visualizations
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    # 1. Activation raster heatmaps
    names = list(architectures.keys())
    for idx, name in enumerate(names):
        ax = axes[idx]
        ax.imshow(results[name]['binary_acts'], aspect='auto', cmap='magma', interpolation='nearest')
        ax.set_title(f"{name}\nBE={results[name]['block_entropy']:.2f}b, LZ={results[name]['lz_complexity']}", fontsize=11, fontweight='bold')
        ax.set_xlabel("Neuron Index (0-63)", fontsize=9)
        ax.set_ylabel("Time Step (0-119)", fontsize=9)

    # 2. Phase-space summary: Block Entropy vs LZ Complexity
    ax_summary = axes[5]
    colors = ['#e74c3c', '#2980b9', '#27ae60', '#8e44ad', '#d35400']
    for idx, name in enumerate(names):
        ax_summary.scatter(results[name]['block_entropy'], results[name]['lz_complexity'], 
                           color=colors[idx], s=180, label=name, edgecolors='black', linewidth=1.5, zorder=5)
        ax_summary.annotate(name, (results[name]['block_entropy'] + 0.03, results[name]['lz_complexity'] + 5), fontsize=9)

    ax_summary.set_title("Activation Manifold Complexity Phase Diagram", fontsize=12, fontweight='bold')
    ax_summary.set_xlabel("2x2 Spatiotemporal Block Entropy (bits)", fontsize=10)
    ax_summary.set_ylabel("Lempel-Ziv Complexity (LZ-76)", fontsize=10)
    ax_summary.grid(True, linestyle='--', alpha=0.6)
    ax_summary.set_xlim(1.0, 4.0)
    ax_summary.set_ylim(50, 600)
    
    plt.suptitle("Functional Activation Manifold Complexity Across Neural Architectures (PRF-002 Domain B Validation)", 
                 fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    out_path = "../../shared_agora/artifacts/nn_activation_manifold_complexity.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Artifact successfully created at {out_path}")

if __name__ == '__main__':
    run_activation_complexity_experiment()
