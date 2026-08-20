"""
Empirical Benchmark: Structural Complexity Measures in Neural Network Weight Topologies
Tests HYP-007 (Applying Block Entropy and Lempel-Ziv Complexity to Measure Neural Network Complexity)

Evaluating spatial Block Shannon Entropy and Lempel-Ziv (LZ-76) algorithmic complexity across:
1. Dense Unstructured Random Network
2. Pruned / Sparsified Network (80% Magnitude Pruned)
3. Modular Block-Diagonal Network (4 Independent Sub-networks)
4. Low-Rank Factorized Network (LoRA Rank=2)
5. Convolutional Weight Topology (Toeplitz Structured)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter

def lempel_ziv_76(binary_seq):
    """Computes standard LZ76 complexity for binary sequence."""
    n = len(binary_seq)
    if n == 0:
        return 0
    complexity = 1
    i = 1
    while i < n:
        j = 1
        found = True
        while i + j <= n:
            s = binary_seq[i:i+j]
            p = binary_seq[0:i+j-1]
            if s not in p:
                complexity += 1
                i += j
                found = False
                break
            j += 1
        if found:
            break
    return complexity

def block_entropy(matrix_bin, k=2):
    """Computes 2D spatial Shannon block entropy over non-overlapping k x k blocks."""
    rows, cols = matrix_bin.shape
    blocks = []
    for i in range(0, rows - k + 1, k):
        for j in range(0, cols - k + 1, k):
            b = tuple(matrix_bin[i:i+k, j:j+k].flatten())
            blocks.append(b)
    c = Counter(blocks)
    tot = sum(c.values())
    p = np.array([cnt / tot for cnt in c.values()])
    return -np.sum(p * np.log2(p + 1e-12))

def run_benchmark():
    np.random.seed(42)
    dim = 64

    # 1. Dense Random
    W_dense = np.random.randn(dim, dim)

    # 2. Pruned Sparse (80% pruned)
    thresh = np.percentile(np.abs(W_dense), 80)
    W_pruned = np.where(np.abs(W_dense) > thresh, W_dense, 0.0)

    # 3. Modular Block-Diagonal (4 sub-networks of size 16x16)
    W_modular = np.zeros((dim, dim))
    for i in range(4):
        W_modular[i*16:(i+1)*16, i*16:(i+1)*16] = np.random.randn(16, 16)

    # 4. Low-Rank Factorized (Rank = 2 LoRA)
    A = np.random.randn(dim, 2)
    B = np.random.randn(2, dim)
    W_lora = A @ B

    # 5. Convolutional Toeplitz Matrix (1D Conv over 64 channels with filter size 5)
    W_conv = np.zeros((dim, dim))
    kernel = np.array([1.0, 2.0, 3.0, 2.0, 1.0])
    for i in range(dim - len(kernel) + 1):
        W_conv[i, i:i+len(kernel)] = kernel

    architectures = {
        'Dense Random': W_dense,
        'Pruned (80%)': W_pruned,
        'Modular Block': W_modular,
        'LoRA (Rank=2)': W_lora,
        'Conv Toeplitz': W_conv
    }

    results = {}
    for name, W in architectures.items():
        b_sign = (W > 0).astype(int)
        b_nz = (W != 0).astype(int)

        lz_sign = lempel_ziv_76(''.join(map(str, b_sign.flatten())))
        lz_nz = lempel_ziv_76(''.join(map(str, b_nz.flatten())))

        be_sign = block_entropy(b_sign, k=2)
        be_nz = block_entropy(b_nz, k=2)

        results[name] = {
            'lz_sign': lz_sign,
            'lz_nz': lz_nz,
            'be_sign': be_sign,
            'be_nz': be_nz
        }

    # Plot results
    labels = list(results.keys())
    x = np.arange(len(labels))
    width = 0.35

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # LZ Plot
    lz_sign_vals = [results[k]['lz_sign'] for k in labels]
    lz_nz_vals = [results[k]['lz_nz'] for k in labels]
    ax1.bar(x - width/2, lz_sign_vals, width, label='Sign Pattern (W > 0)', color='#3498db')
    ax1.bar(x + width/2, lz_nz_vals, width, label='Sparsity Pattern (W != 0)', color='#e74c3c')
    ax1.set_title("Lempel-Ziv Algorithmic Complexity across NN Topologies", fontsize=12, fontweight='bold')
    ax1.set_ylabel("LZ-76 Complexity", fontsize=11)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=20, ha='right')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.5)

    # BE Plot
    be_sign_vals = [results[k]['be_sign'] for k in labels]
    be_nz_vals = [results[k]['be_nz'] for k in labels]
    ax2.bar(x - width/2, be_sign_vals, width, label='Sign Block Entropy (2x2)', color='#2ecc71')
    ax2.bar(x + width/2, be_nz_vals, width, label='Sparsity Block Entropy (2x2)', color='#f39c12')
    ax2.set_title("Spatial Block Shannon Entropy across NN Topologies", fontsize=12, fontweight='bold')
    ax2.set_ylabel("Block Entropy (bits, max=4.0)", fontsize=11)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=20, ha='right')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    out_path = "nn_complexity_benchmark.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Benchmark complete. Plot saved to {out_path}")

    return results

if __name__ == '__main__':
    run_benchmark()
