#!/usr/bin/env python3
"""
Fast Empirical Test: Evolutionary Criticality Hypothesis (HYP-050)
Testing critical balance in genetic algorithms with optimized parameters
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import json

def calculate_diversity_fast(population):
    """Fast diversity calculation using vectorized operations"""
    # Use pairwise XOR to compute Hamming distances efficiently
    n_individuals = population.shape[0]
    if n_individuals <= 1:
        return 0.0
    
    # Sample-based diversity estimation for speed
    n_samples = min(50, n_individuals * (n_individuals - 1) // 2)
    diversity_sum = 0
    
    for _ in range(n_samples):
        i, j = np.random.choice(n_individuals, 2, replace=False)
        hamming_distance = np.sum(population[i] != population[j]) / population.shape[1]
        diversity_sum += hamming_distance
    
    return diversity_sum / n_samples

def fitness_function(individual):
    """OneMax fitness function"""
    return np.sum(individual)

def evolve_generation_fast(population, mutation_rate):
    """Fast evolution with simplified operators"""
    pop_size, n_bits = population.shape
    
    # Fast fitness calculation
    fitness_scores = np.sum(population, axis=1)
    
    # Tournament selection (vectorized)
    tournament_size = 3
    selected_indices = []
    for _ in range(pop_size):
        candidates = np.random.choice(pop_size, tournament_size, replace=False)
        winner = candidates[np.argmax(fitness_scores[candidates])]
        selected_indices.append(winner)
    
    new_population = population[selected_indices].copy()
    
    # Crossover (simplified single-point)
    for i in range(0, pop_size - 1, 2):
        if np.random.random() < 0.8:  # crossover rate
            crossover_point = np.random.randint(1, n_bits)
            temp = new_population[i, crossover_point:].copy()
            new_population[i, crossover_point:] = new_population[i + 1, crossover_point:]
            new_population[i + 1, crossover_point:] = temp
    
    # Mutation (vectorized)
    mutation_mask = np.random.random((pop_size, n_bits)) < mutation_rate
    new_population[mutation_mask] = 1 - new_population[mutation_mask]
    
    return new_population

def exponential_decay_model(t, D0, lambda_val, D_min):
    """Model: D(t) = D0 * exp(-lambda * t) + D_min"""
    return D0 * np.exp(-lambda_val * t) + D_min

def test_evolutionary_criticality_fast():
    """Fast test of evolutionary criticality hypothesis"""
    print("=== FAST EVOLUTIONARY CRITICALITY TEST ===")
    
    # Reduced parameters for speed
    n_bits = 30
    pop_size = 50
    generations = 80
    n_runs = 3
    
    # Test mutation rates around critical zone
    mutation_rates = [0.005, 0.01, 0.02, 0.03, 0.05, 0.1]
    
    results = {}
    
    for mr in mutation_rates:
        print(f"Testing mutation rate: {mr}")
        
        run_diversities = []
        run_fitnesses = []
        
        for run in range(n_runs):
            np.random.seed(42 + run + int(mr * 10000))
            
            # Initialize random population
            population = np.random.randint(0, 2, (pop_size, n_bits))
            
            diversity_history = []
            fitness_history = []
            
            for gen in range(generations):
                # Calculate metrics
                diversity = calculate_diversity_fast(population)
                max_fitness = np.max(np.sum(population, axis=1))
                
                diversity_history.append(diversity)
                fitness_history.append(max_fitness)
                
                # Evolve
                population = evolve_generation_fast(population, mr)
            
            run_diversities.append(diversity_history)
            run_fitnesses.append(fitness_history)
        
        # Average across runs
        avg_diversity = np.mean(run_diversities, axis=0)
        avg_fitness = np.mean(run_fitnesses, axis=0)
        
        # Fit exponential decay model to diversity
        generations_array = np.arange(len(avg_diversity))
        
        try:
            # Initial guess
            D0_guess = avg_diversity[0]
            D_min_guess = np.mean(avg_diversity[-15:])  # Last 15 generations
            lambda_guess = 0.05
            
            popt, _ = curve_fit(
                exponential_decay_model, 
                generations_array, 
                avg_diversity,
                p0=[D0_guess, lambda_guess, D_min_guess],
                bounds=([0, 0, 0], [1, 1, 1]),
                maxfev=1000
            )
            
            D0_fit, lambda_fit, D_min_fit = popt
            
            # Calculate R-squared
            y_pred = exponential_decay_model(generations_array, *popt)
            ss_res = np.sum((avg_diversity - y_pred) ** 2)
            ss_tot = np.sum((avg_diversity - np.mean(avg_diversity)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
        except:
            D0_fit = lambda_fit = D_min_fit = r_squared = None
        
        # Store results
        results[mr] = {
            'final_diversity': float(avg_diversity[-1]),
            'final_fitness': float(avg_fitness[-1]),
            'D0_fit': float(D0_fit) if D0_fit is not None else None,
            'lambda_fit': float(lambda_fit) if lambda_fit is not None else None,
            'D_min_fit': float(D_min_fit) if D_min_fit is not None else None,
            'r_squared': float(r_squared) if r_squared is not None else None,
            'diversity_trend': 'decreasing' if avg_diversity[-1] < avg_diversity[0] else 'stable'
        }
        
        print(f"  Final diversity: {avg_diversity[-1]:.3f}")
        print(f"  Final fitness: {avg_fitness[-1]:.1f}")
        if D_min_fit is not None:
            print(f"  D_min fitted: {D_min_fit:.3f}, R²: {r_squared:.3f}")
    
    # Analysis and visualization
    mrs = list(mutation_rates)
    final_divs = [results[mr]['final_diversity'] for mr in mrs]
    final_fits = [results[mr]['final_fitness'] for mr in mrs]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot diversity vs mutation rate
    ax1.semilogx(mrs, final_divs, 'bo-', linewidth=2, markersize=8)
    ax1.axvspan(0.01, 0.03, alpha=0.3, color='red', label='Predicted Critical Zone')
    ax1.set_xlabel('Mutation Rate')
    ax1.set_ylabel('Final Diversity (D_min)')
    ax1.set_title('Diversity Floor vs Mutation Rate')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot fitness vs mutation rate
    ax2.semilogx(mrs, final_fits, 'go-', linewidth=2, markersize=8)
    ax2.set_xlabel('Mutation Rate')
    ax2.set_ylabel('Final Max Fitness')
    ax2.set_title('Optimization Performance vs Mutation Rate')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/evolutionary_criticality_fast.png', 
                dpi=150, bbox_inches='tight')
    
    # Analysis
    print("\n=== CRITICALITY ANALYSIS ===")
    
    # Check for critical zone behavior
    critical_zone_mrs = [mr for mr in mutation_rates if 0.01 <= mr <= 0.03]
    low_mrs = [mr for mr in mutation_rates if mr < 0.01]
    high_mrs = [mr for mr in mutation_rates if mr > 0.03]
    
    critical_diversity = np.mean([results[mr]['final_diversity'] for mr in critical_zone_mrs])
    low_diversity = np.mean([results[mr]['final_diversity'] for mr in low_mrs]) if low_mrs else 0
    high_diversity = np.mean([results[mr]['final_diversity'] for mr in high_mrs]) if high_mrs else 0
    
    critical_fitness = np.mean([results[mr]['final_fitness'] for mr in critical_zone_mrs])
    low_fitness = np.mean([results[mr]['final_fitness'] for mr in low_mrs]) if low_mrs else 0
    high_fitness = np.mean([results[mr]['final_fitness'] for mr in high_mrs]) if high_mrs else 0
    
    print(f"Critical zone (0.01-0.03) avg diversity: {critical_diversity:.3f}")
    print(f"Low mutation (<0.01) avg diversity: {low_diversity:.3f}")
    print(f"High mutation (>0.03) avg diversity: {high_diversity:.3f}")
    
    print(f"Critical zone fitness: {critical_fitness:.1f}")
    print(f"Low mutation fitness: {low_fitness:.1f}")
    print(f"High mutation fitness: {high_fitness:.1f}")
    
    # Check exponential decay fits
    good_fits = [mr for mr in mutation_rates 
                if results[mr]['r_squared'] is not None and results[mr]['r_squared'] > 0.7]
    print(f"Mutation rates with exponential decay fits (R²>0.7): {good_fits}")
    
    # Check diversity patterns
    diversity_range = max(final_divs) - min(final_divs)
    print(f"Diversity range across mutation rates: {diversity_range:.3f}")
    
    # Determine support level
    has_nonzero_asymptotes = min(final_divs) > 0.05  # Non-zero D_min
    has_diversity_variation = diversity_range > 0.1   # Significant variation
    has_good_fits = len(good_fits) >= len(mutation_rates) // 2
    optimal_in_critical = critical_fitness >= max(low_fitness, high_fitness)
    
    support_factors = [has_nonzero_asymptotes, has_diversity_variation, 
                      has_good_fits, optimal_in_critical]
    support_count = sum(support_factors)
    
    if support_count >= 3:
        verdict = "STRONG SUPPORT"
    elif support_count == 2:
        verdict = "MODERATE SUPPORT"
    else:
        verdict = "LIMITED SUPPORT"
    
    print(f"\nSupport factors: Non-zero asymptotes: {has_nonzero_asymptotes}, "
          f"Diversity variation: {has_diversity_variation}, "
          f"Good fits: {has_good_fits}, Optimal critical: {optimal_in_critical}")
    print(f"VERDICT: {verdict} for Evolutionary Criticality Hypothesis")
    
    return results, verdict

if __name__ == "__main__":
    results, verdict = test_evolutionary_criticality_fast()