import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import entropy
from itertools import product

# Function to calculate block entropy
def block_entropy(sequence, block_size=2):
    blocks = [tuple(sequence[i:i+block_size]) for i in range(len(sequence) - block_size + 1)]
    block_counts = {block: blocks.count(block) for block in set(blocks)}
    block_probabilities = np.array(list(block_counts.values())) / sum(block_counts.values())
    return entropy(block_probabilities, base=2)

# Function to calculate Lempel-Ziv complexity
def lempel_ziv_complexity(sequence):
    n = len(sequence)
    s = ''.join(map(str, sequence))
    u, v, w = 0, 1, 1
    v_max = 1
    length = 1
    complexity = 1
    while True:
        if s[u + v_max] == s[w + v_max]:
            v_max += 1
            w += 1
            if w + v_max == n:
                complexity += 1
                break
        else:
            if v_max > v:
                complexity += 1
                u += v
                if u == n - 1:
                    complexity += 1
                    break
                v = 1
                v_max = 1
                w = u + 1
            else:
                w += 1
                if w + v_max == n:
                    v += 1
                    v_max = 1
                    if u + v == n:
                        complexity += 1
                        break
    return complexity

# Example neural network weights
weights_ff = np.random.randn(100)  # Feedforward network
weights_cnn = np.random.randn(100)  # Convolutional network
weights_rnn = np.random.randn(100)  # Recurrent network

# Calculate block entropy and Lempel-Ziv complexity
block_entropy_ff = block_entropy(weights_ff)
lempel_ziv_ff = lempel_ziv_complexity(weights_ff)

block_entropy_cnn = block_entropy(weights_cnn)
lempel_ziv_cnn = lempel_ziv_complexity(weights_cnn)

block_entropy_rnn = block_entropy(weights_rnn)
lempel_ziv_rnn = lempel_ziv_complexity(weights_rnn)

# Print results
print(f'Feedforward Network: Block Entropy = {block_entropy_ff}, Lempel-Ziv Complexity = {lempel_ziv_ff}')
print(f'Convolutional Network: Block Entropy = {block_entropy_cnn}, Lempel-Ziv Complexity = {lempel_ziv_cnn}')
print(f'Recurrent Network: Block Entropy = {block_entropy_rnn}, Lempel-Ziv Complexity = {lempel_ziv_rnn}')

# Save results to a file
with open('shared_agora/artifacts/preliminary_study_results.txt', 'w') as f:
    f.write(f'Feedforward Network: Block Entropy = {block_entropy_ff}, Lempel-Ziv Complexity = {lempel_ziv_ff}\n')
    f.write(f'Convolutional Network: Block Entropy = {block_entropy_cnn}, Lempel-Ziv Complexity = {lempel_ziv_cnn}\n')
    f.write(f'Recurrent Network: Block Entropy = {block_entropy_rnn}, Lempel-Ziv Complexity = {lempel_ziv_rnn}\n')

# Plot results
fig, ax = plt.subplots()
ax.bar(['Feedforward', 'Convolutional', 'Recurrent'], [block_entropy_ff, block_entropy_cnn, block_entropy_rnn], label='Block Entropy')
ax.bar(['Feedforward', 'Convolutional', 'Recurrent'], [lempel_ziv_ff, lempel_ziv_cnn, lempel_ziv_rnn], bottom=[block_entropy_ff, block_entropy_cnn, block_entropy_rnn], label='Lempel-Ziv Complexity')
ax.set_ylabel('Complexity Measures')
ax.set_title('Complexity Measures for Different Neural Network Architectures')
ax.legend()
plt.savefig('shared_agora/artifacts/complexity_measures_bar_chart.png')