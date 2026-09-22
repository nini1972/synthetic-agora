#!/usr/bin/env python3
"""
Empirical Test: Evolutionary Criticality Hypothesis (HYP-050)
Testing the critical balance between order and chaos in genetic algorithms
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import json

def calculate_diversity(population):
    """Calculate population genetic diversity (Hamming diversity)"""
    n_individuals, n_bits = population.shape
    total_pairs = n_individuals * (n_individuals - 1) // 2
    
    if total_pairs == 0:
        return 0.0
    
    diversity_sum = 0
    for i in range(n_individuals):
        for j in range(i + 1, n_individuals):
            hamming_distance = np.sum(population[i] != population[j])
            diversity_sum += hamming_distance / n_bits
    
    return diversity_sum / total_pairs

def fitness_function(individual):
    """OneMax fitness function (count of 1s)"""
    return np.sum(individual)

def tournament_selection(population, fitness_scores, tournament_size=3):
    """Tournament selection"""
    selected = []
    pop_size = len(population)
    
    for _ in range(pop_size):
        tournament_indices = np.random.choice(pop_size, tournament_size, replace=False)
        tournament_fitness = fitness_scores[tournament_indices]
        winner_idx = tournament_indices[np.argmax(tournament_fitness)]
        selected.append(population[winner_idx].copy())
    
    return np.array(selected)

def crossover(parent1, parent2, crossover_rate=0.8):
    """Single-point crossover"""
    if np.random.random() < crossover_rate:
        crossover_point = np.random.randint(1, len(parent1))
        child1 = np.concatenate([parent1[:crossover_point], parent2[crossover_point:]])
        child2 = np.concatenate([parent2[:crossover_point], parent1[crossover_point:]])
        return child1, child2
    else:
        return parent1.copy(), parent2.copy()

def mutate(individual, mutation_rate):
    """Bit-flip mutation"""
    for i in range(len(individual)):
        if np.random.random() < mutation_rate:
            individual[i] = 1 - individual[i]
    return individual

def evolve_generation(population, mutation_rate, crossover_rate=0.8):
    """Evolve one generation"""
    # Calculate fitness
    fitness_scores = np.array([fitness_function(ind) for ind in population])
    
    # Selection
    selected = tournament_selection(population, fitness_scores)
    
    # Crossover and mutation
    new_population = []
    for i in range(0, len(selected), 2):
        if i + 1 < len(selected):
            child1, child2 = crossover(selected[i], selected[i + 1], crossover_rate)
        else:
            child1, child2 = selected[i].copy(), selected[i].copy()
        
        child1 = mutate(child1, mutation_rate)
        child2 = mutate(child2, mutation_rate)
        
        new_population.extend([child1, child2])
    
    return np.array(new_population[:len(population)])

def exponential_decay_model(t, D0, lambda_val, D_min):
    """Model: D(t) = D0 * exp(-lambda * t) + D_min"""
    return D0 * np.exp(-lambda_val * t) + D_min

def test_evolutionary_criticality():
    """Test the evolutionary criticality hypothesis"""
    print("=== EVOLUTIONARY CRITICALITY TEST ===")
    
    # Parameters
    n_bits = 50
    pop_size = 100
    generations = 150
    n_runs = 5
    
    # Test mutation rates around critical zone
    mutation_rates = [0.005, 0.01, 0.015, 0.02, 0.03, 0.05, 0.1]
    
    results = {}
    
    for mr in mutation_rates:
        print(f"\nTesting mutation rate: {mr}")
        
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
                diversity = calculate_diversity(population)
                max_fitness = max([fitness_function(ind) for ind in population])
                
                diversity_history.append(diversity)
                fitness_history.append(max_fitness)
                
                # Evolve
                population = evolve_generation(population, mr)
            
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
            D_min_guess = np.mean(avg_diversity[-20:])  # Last 20 generations
            lambda_guess = 0.05
            
            popt, _ = curve_fit(
                exponential_decay_model, 
                generations_array, 
                avg_diversity,
                p0=[D0_guess, lambda_guess, D_min_guess],
                bounds=([0, 0, 0], [1, np.inf, 1]),
                maxfev=2000
            )
            
            D0_fit, lambda_fit, D_min_fit = popt
            
            # Calculate R-squared
            y_pred = exponential_decay_model(generations_array, *popt)
            ss_res = np.sum((avg_diversity - y_pred) ** 2)
            ss_tot = np.sum((avg_diversity - np.mean(avg_diversity)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
        except Exception as e:
            print(f"Fitting failed for mr={mr}: {e}")
            D0_fit = lambda_fit = D_min_fit = r_squared = None
        
        # Store results
        results[mr] = {
            'diversity_history': avg_diversity.tolist(),
            'fitness_history': avg_fitness.tolist(),
            'final_diversity': avg_diversity[-1],
            'final_fitness': avg_fitness[-1],
            'D0_fit': float(D0_fit) if D0_fit is not None else None,
            'lambda_fit': float(lambda_fit) if lambda_fit is not None else None,
            'D_min_fit': float(D_min_fit) if D_min_fit is not None else None,
            'r_squared': float(r_squared) if r_squared is not None else None
        }
        
        print(f"  Final diversity: {avg_diversity[-1]:.3f}")
        print(f"  Final fitness: {avg_fitness[-1]:.1f}")
        if D_min_fit is not None:
            print(f"  D_min fitted: {D_min_fit:.3f}, R²: {r_squared:.3f}")
    
    # Create visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Diversity evolution
    colors = plt.cm.viridis(np.linspace(0, 1, len(mutation_rates)))
    
    for i, mr in enumerate(mutation_rates):
        if results[mr]['diversity_history'] is not None:
            ax1.plot(results[mr]['diversity_history'], 
                    color=colors[i], label=f'μ={mr}', linewidth=2)
    
    ax1.set_xlabel('Generation')
    ax1.set_ylabel('Population Diversity')
    ax1.set_title('Diversity Evolution by Mutation Rate')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Fitness evolution  
    for i, mr in enumerate(mutation_rates):
        if results[mr]['fitness_history'] is not None:
            ax2.plot(results[mr]['fitness_history'], 
                    color=colors[i], label=f'μ={mr}', linewidth=2)
    
    ax2.set_xlabel('Generation')
    ax2.set_ylabel('Maximum Fitness')
    ax2.set_title('Fitness Evolution by Mutation Rate')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Final diversity vs mutation rate
    mrs = list(mutation_rates)
    final_divs = [results[mr]['final_diversity'] for mr in mrs]
    
    ax3.plot(mrs, final_divs, 'bo-', linewidth=2, markersize=8)
    ax3.axvspan(0.01, 0.03, alpha=0.3, color='red', label='Critical Zone')
    ax3.set_xlabel('Mutation Rate')
    ax3.set_ylabel('Final Diversity (D_min)')
    ax3.set_title('Diversity Floor vs Mutation Rate')
    ax3.set_xscale('log')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Plot 4: Model fit quality
    mrs_fit = [mr for mr in mrs if results[mr]['r_squared'] is not None]
    r_squared_vals = [results[mr]['r_squared'] for mr in mrs_fit]
    
    ax4.plot(mrs_fit, r_squared_vals, 'go-', linewidth=2, markersize=8)
    ax4.axhline(y=0.8, color='red', linestyle='--', label='Good Fit Threshold')
    ax4.set_xlabel('Mutation Rate')
    ax4.set_ylabel('Model Fit (R²)')
    ax4.set_title('Exponential Decay Model Fit Quality')
    ax4.set_xscale('log')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/evolutionary_criticality_test.png', 
                dpi=150, bbox_inches='tight')
    
    # Analysis
    print("\n=== CRITICALITY ANALYSIS ===")
    
    # Check for critical zone
    critical_zone_mrs = [mr for mr in mutation_rates if 0.01 <= mr <= 0.03]
    non_critical_mrs = [mr for mr in mutation_rates if mr < 0.01 or mr > 0.03]
    
    critical_diversity = np.mean([results[mr]['final_diversity'] for mr in critical_zone_mrs])
    non_critical_diversity = np.mean([results[mr]['final_diversity'] for mr in non_critical_mrs])
    
    print(f"Critical zone (0.01-0.03) avg diversity: {critical_diversity:.3f}")
    print(f"Non-critical zone avg diversity: {non_critical_diversity:.3f}")
    
    # Check exponential decay model fit
    good_fits = [mr for mr in mutation_rates 
                if results[mr]['r_squared'] is not None and results[mr]['r_squared'] > 0.8]
    
    print(f"Mutation rates with good exponential fits (R²>0.8): {good_fits}")
    
    # Check over-exploitation and over-exploration
    low_mr_diversity = np.mean([results[mr]['final_diversity'] for mr in mutation_rates if mr <= 0.005])
    high_mr_diversity = np.mean([results[mr]['final_diversity'] for mr in mutation_rates if mr >= 0.05])
    
    print(f"Low mutation rate diversity: {low_mr_diversity:.3f}")
    print(f"High mutation rate diversity: {high_mr_diversity:.3f}")
    
    # Verdict
    has_critical_zone = critical_diversity > low_mr_diversity and critical_diversity > 0.1
    has_exponential_decay = len(good_fits) >= len(mutation_rates) // 2
    has_proper_asymptotes = low_mr_diversity < 0.05 and high_mr_diversity > 0.3
    
    if has_critical_zone and has_exponential_decay and has_proper_asymptotes:
        verdict = "STRONG SUPPORT"
    elif (has_critical_zone and has_exponential_decay) or (has_critical_zone and has_proper_asymptotes):
        verdict = "MODERATE SUPPORT"
    else:
        verdict = "LIMITED SUPPORT"
    
    print(f"\nVERDICT: {verdict} for Evolutionary Criticality Hypothesis")
    
    # Save detailed results
    with open('../../shared_agora/artifacts/evolutionary_criticality_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results, verdict

if __name__ == "__main__":
    results, verdict = test_evolutionary_criticality()