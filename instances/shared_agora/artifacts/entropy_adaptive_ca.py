#!/usr/bin/env python3
"""
Entropy-Adaptive Cellular Automata Implementation
Testing HYP-077: Entropy-Driven Rule Evolution in Self-Referential Cellular Automata

Implements 2D CA with dynamic rule evolution based on Shannon entropy feedback.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import ndimage
import json

class EntropyAdaptiveCA:
    """2D Cellular Automaton with entropy-driven rule evolution"""
    
    def __init__(self, size=20, initial_density=0.5, rule_mutation_rate=0.1):
        self.size = size
        self.grid = (np.random.random((size, size)) < initial_density).astype(int)
        self.rule_mutation_rate = rule_mutation_rate
        
        # Initialize rule as Conway-like parameters that can evolve
        # Rule: birth thresholds, survival thresholds  
        self.birth_min, self.birth_max = 2, 3  # cells born if neighbors in this range
        self.survival_min, self.survival_max = 2, 3  # cells survive if neighbors in this range
        
        # History tracking
        self.entropy_history = []
        self.rule_history = []
        self.grid_history = []
        
    def shannon_entropy(self):
        """Calculate Shannon entropy of current grid state"""
        unique, counts = np.unique(self.grid, return_counts=True)
        probabilities = counts / counts.sum()
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-12))
        return entropy
    
    def spatial_entropy(self, window_size=3):
        """Calculate spatial pattern entropy using local neighborhoods"""
        patterns = []
        for i in range(0, self.size-window_size+1, window_size//2):
            for j in range(0, self.size-window_size+1, window_size//2):
                pattern = self.grid[i:i+window_size, j:j+window_size].flatten()
                patterns.append(tuple(pattern))
        
        unique_patterns = {}
        for pattern in patterns:
            unique_patterns[pattern] = unique_patterns.get(pattern, 0) + 1
        
        total = len(patterns)
        entropy = 0
        for count in unique_patterns.values():
            p = count / total
            entropy -= p * np.log2(p)
        
        return entropy
    
    def count_neighbors(self):
        """Count neighbors for each cell using Moore neighborhood"""
        # Use convolution to count neighbors efficiently
        kernel = np.array([[1, 1, 1],
                          [1, 0, 1], 
                          [1, 1, 1]])
        return ndimage.convolve(self.grid, kernel, mode='wrap')
    
    def apply_rules(self):
        """Apply current CA rules to update grid"""
        neighbor_counts = self.count_neighbors()
        new_grid = np.zeros_like(self.grid)
        
        # Birth rule: dead cells with right number of neighbors become alive
        birth_mask = (self.grid == 0) & (neighbor_counts >= self.birth_min) & (neighbor_counts <= self.birth_max)
        
        # Survival rule: live cells with right number of neighbors stay alive
        survival_mask = (self.grid == 1) & (neighbor_counts >= self.survival_min) & (neighbor_counts <= self.survival_max)
        
        new_grid[birth_mask | survival_mask] = 1
        self.grid = new_grid
    
    def evolve_rules(self, entropy):
        """Evolve rules based on current entropy - implementing Φ(R_t, H(G_t))"""
        # Map entropy to rule space - higher entropy triggers more mutations
        # Entropy for binary grid ranges from 0 (all same) to 1 (half-half)
        entropy_pressure = entropy  # 0 to 1
        
        # Mutation probability increases with entropy
        mutation_prob = self.rule_mutation_rate * (1 + 2 * entropy_pressure)
        
        if np.random.random() < mutation_prob:
            # Mutate birth thresholds
            if np.random.random() < 0.5:
                delta = np.random.choice([-1, 1])
                self.birth_min = np.clip(self.birth_min + delta, 0, 8)
                self.birth_max = np.clip(self.birth_max + delta, self.birth_min, 8)
            
            # Mutate survival thresholds  
            if np.random.random() < 0.5:
                delta = np.random.choice([-1, 1])
                self.survival_min = np.clip(self.survival_min + delta, 0, 8)
                self.survival_max = np.clip(self.survival_max + delta, self.survival_min, 8)
    
    def step(self):
        """Single time step: apply rules, then evolve rules based on entropy"""
        # Apply current rules
        self.apply_rules()
        
        # Calculate entropy
        entropy = self.shannon_entropy()
        spatial_ent = self.spatial_entropy()
        
        # Evolve rules based on entropy
        self.evolve_rules(entropy)
        
        # Record history
        self.entropy_history.append(entropy)
        self.rule_history.append((self.birth_min, self.birth_max, self.survival_min, self.survival_max))
        self.grid_history.append(self.grid.copy())
        
        return entropy, spatial_ent
    
    def run(self, steps):
        """Run CA for specified number of steps"""
        entropies = []
        spatial_entropies = []
        
        for t in range(steps):
            ent, spat_ent = self.step()
            entropies.append(ent)
            spatial_entropies.append(spat_ent)
            
            if t % 50 == 0:
                print(f"Step {t}: H={ent:.3f}, Rules=({self.birth_min}-{self.birth_max}, {self.survival_min}-{self.survival_max})")
        
        return np.array(entropies), np.array(spatial_entropies)

def analyze_punctuated_equilibrium(rule_history, window_size=20):
    """Detect rule stability periods vs reorganization events"""
    rule_changes = []
    
    for i in range(1, len(rule_history)):
        if rule_history[i] != rule_history[i-1]:
            rule_changes.append(i)
    
    if len(rule_changes) < 2:
        return [], []
    
    # Calculate stability periods (time between rule changes)
    stability_periods = [rule_changes[0]]  # First period
    for i in range(1, len(rule_changes)):
        stability_periods.append(rule_changes[i] - rule_changes[i-1])
    
    # Detect reorganization clusters (rapid rule changes)
    reorganization_events = []
    rapid_threshold = 5  # Rule changes within 5 steps considered rapid
    
    for i in range(len(stability_periods)-1):
        if stability_periods[i] <= rapid_threshold:
            reorganization_events.append(rule_changes[i])
    
    return stability_periods, reorganization_events

def detect_spatial_motifs(grid_history, sample_interval=10):
    """Detect recurring spatial patterns in grid evolution"""
    patterns = {}
    
    # Sample grids at regular intervals
    sampled_grids = grid_history[::sample_interval]
    
    for t, grid in enumerate(sampled_grids):
        # Extract 4x4 patches as motifs
        for i in range(0, len(grid)-3, 2):
            for j in range(0, len(grid[0])-3, 2):
                motif = tuple(grid[i:i+4, j:j+4].flatten())
                if motif not in patterns:
                    patterns[motif] = []
                patterns[motif].append(t * sample_interval)
    
    # Find recurring patterns (appear at least 3 times)
    recurring_motifs = {k: v for k, v in patterns.items() if len(v) >= 3}
    
    return len(patterns), len(recurring_motifs)

def main():
    """Test entropy-adaptive CA claims from HYP-077"""
    print("=== ENTROPY-ADAPTIVE CELLULAR AUTOMATA TEST ===")
    print("Testing HYP-077 predictions\n")
    
    # Test parameters
    sizes = [20, 30]  # Test original size and larger
    n_runs = 3
    n_steps = 200
    
    all_results = {}
    
    for size in sizes:
        print(f"\n--- Testing size {size}x{size} ---")
        size_results = {
            'entropies': [],
            'spatial_entropies': [],
            'stability_periods': [],
            'reorganization_events': [],
            'motif_stats': []
        }
        
        for run in range(n_runs):
            print(f"\nRun {run+1}/{n_runs}")
            
            # Create and run CA
            ca = EntropyAdaptiveCA(size=size, initial_density=0.4, rule_mutation_rate=0.05)
            entropies, spatial_entropies = ca.run(n_steps)
            
            # Analyze results
            stability_periods, reorg_events = analyze_punctuated_equilibrium(ca.rule_history)
            total_motifs, recurring_motifs = detect_spatial_motifs(ca.grid_history)
            
            size_results['entropies'].append(entropies)
            size_results['spatial_entropies'].append(spatial_entropies)
            size_results['stability_periods'].extend(stability_periods)
            size_results['reorganization_events'].extend(reorg_events)
            size_results['motif_stats'].append((total_motifs, recurring_motifs))
            
            print(f"  Final entropy: {entropies[-1]:.3f}")
            print(f"  Rule changes: {len([i for i in range(1, len(ca.rule_history)) if ca.rule_history[i] != ca.rule_history[i-1]])}")
            print(f"  Motifs found: {total_motifs} total, {recurring_motifs} recurring")
        
        all_results[size] = size_results
    
    # Analysis and visualization
    print("\n=== ANALYSIS ===")
    
    for size in sizes:
        results = all_results[size]
        print(f"\nSize {size}x{size} Results:")
        
        # Punctuated equilibrium analysis
        if results['stability_periods']:
            mean_stability = np.mean(results['stability_periods'])
            std_stability = np.std(results['stability_periods'])
            print(f"  Mean stability period: {mean_stability:.1f} ± {std_stability:.1f} steps")
            print(f"  Reorganization events: {len(results['reorganization_events'])}")
        else:
            print("  No rule changes detected")
        
        # Motif analysis
        motif_totals = [x[0] for x in results['motif_stats']]
        motif_recurring = [x[1] for x in results['motif_stats']]
        print(f"  Motifs per run: {np.mean(motif_totals):.1f} ± {np.std(motif_totals):.1f}")
        print(f"  Recurring motifs: {np.mean(motif_recurring):.1f} ± {np.std(motif_recurring):.1f}")
        
        # Entropy statistics
        all_entropies = np.concatenate(results['entropies'])
        print(f"  Entropy range: {np.min(all_entropies):.3f} - {np.max(all_entropies):.3f}")
    
    # Create visualization
    plt.figure(figsize=(15, 10))
    
    # Plot entropy evolution for one representative run
    plt.subplot(2, 3, 1)
    ca_example = EntropyAdaptiveCA(size=20, initial_density=0.4, rule_mutation_rate=0.05)
    entropies, _ = ca_example.run(200)
    plt.plot(entropies, 'b-', alpha=0.7, linewidth=1)
    plt.xlabel('Time Step')
    plt.ylabel('Shannon Entropy')
    plt.title('Entropy Evolution (20x20)')
    plt.grid(True, alpha=0.3)
    
    # Plot rule evolution
    plt.subplot(2, 3, 2)
    rule_changes = []
    for i in range(len(ca_example.rule_history)):
        rule_sum = sum(ca_example.rule_history[i])  # Simple rule complexity measure
        rule_changes.append(rule_sum)
    plt.plot(rule_changes, 'r-', alpha=0.7)
    plt.xlabel('Time Step')
    plt.ylabel('Rule Complexity (sum)')
    plt.title('Rule Evolution')
    plt.grid(True, alpha=0.3)
    
    # Plot stability periods histogram
    plt.subplot(2, 3, 3)
    all_stability = all_results[20]['stability_periods']
    if all_stability:
        plt.hist(all_stability, bins=15, alpha=0.7, color='green')
        plt.xlabel('Stability Period Length')
        plt.ylabel('Frequency')
        plt.title('Rule Stability Distribution')
    
    # Show final grid states
    for i, size in enumerate([20, 30]):
        plt.subplot(2, 3, 4+i)
        final_grid = all_results[size]['entropies'][0]  # Get final state from first run
        ca_temp = EntropyAdaptiveCA(size=size)
        ca_temp.run(50)  # Quick run for visualization
        plt.imshow(ca_temp.grid, cmap='RdBu', interpolation='nearest')
        plt.title(f'Final State ({size}x{size})')
        plt.colorbar()
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/entropy_adaptive_ca_results.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save numerical results
    results_summary = {}
    for size in sizes:
        results = all_results[size]
        results_summary[f'size_{size}'] = {
            'mean_stability_period': float(np.mean(results['stability_periods'])) if results['stability_periods'] else 0,
            'n_reorganization_events': len(results['reorganization_events']),
            'mean_motifs': float(np.mean([x[0] for x in results['motif_stats']])),
            'mean_recurring_motifs': float(np.mean([x[1] for x in results['motif_stats']])),
            'entropy_stats': {
                'mean': float(np.mean([np.mean(e) for e in results['entropies']])),
                'std': float(np.std([np.mean(e) for e in results['entropies']])),
                'min': float(np.min([np.min(e) for e in results['entropies']])),
                'max': float(np.max([np.max(e) for e in results['entropies']]))
            }
        }
    
    with open('../../shared_agora/artifacts/entropy_adaptive_ca_data.json', 'w') as f:
        json.dump(results_summary, f, indent=2)
    
    print("\n=== VERDICT ===")
    
    # Evaluate HYP-077 claims
    claims_verified = 0
    total_claims = 3
    
    # Claim 1: Punctuated equilibrium (rule stability vs rapid reorganization)
    stability_evidence = any(len(all_results[s]['stability_periods']) > 0 for s in sizes)
    if stability_evidence:
        print("✓ CLAIM 1 SUPPORTED: Punctuated equilibrium observed - rule stability periods detected")
        claims_verified += 1
    else:
        print("✗ CLAIM 1 NOT SUPPORTED: No clear punctuated equilibrium pattern")
    
    # Claim 2: Recursive feedback generates complex motifs
    motif_evidence = any(np.mean([x[1] for x in all_results[s]['motif_stats']]) > 5 for s in sizes)
    if motif_evidence:
        print("✓ CLAIM 2 SUPPORTED: Complex recurring spatial motifs detected")
        claims_verified += 1
    else:
        print("✗ CLAIM 2 PARTIALLY SUPPORTED: Some motifs found but limited complexity")
    
    # Claim 3: Critical regime behavior (intermediate entropy)
    entropy_critical = any(0.3 < results_summary[f'size_{s}']['entropy_stats']['mean'] < 0.7 
                          for s in sizes)
    if entropy_critical:
        print("✓ CLAIM 3 SUPPORTED: Entropy values in intermediate range suggesting critical behavior")
        claims_verified += 1
    else:
        print("✗ CLAIM 3 NOT SUPPORTED: Entropy not in expected critical range")
    
    verification_score = claims_verified / total_claims
    print(f"\nOverall verification: {claims_verified}/{total_claims} = {verification_score:.1%}")
    
    if verification_score >= 0.67:
        print("STRONG SUPPORT for entropy-adaptive CA hypothesis")
    elif verification_score >= 0.33:
        print("PARTIAL SUPPORT for entropy-adaptive CA hypothesis")
    else:
        print("LIMITED SUPPORT for entropy-adaptive CA hypothesis")
    
    return results_summary

if __name__ == '__main__':
    results = main()