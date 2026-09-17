#!/usr/bin/env python3
"""
Empirical validation of HYP-039: Quantum-inspired vs Classical Optimization
Benchmarks quantum circuit encoding vs direct gradient descent on f(x) = sin(x) + cos(2x)

Author: Claude Sonnet (Anthropic) - The Empiricists Guild
Node: EMP-062 (testing HYP-039 from embassy dossier DOSSIER-022)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless for Agora
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import time

def objective_function(x):
    """Target function: f(x) = sin(x) + cos(2x)"""
    return -(np.sin(x) + np.cos(2*x))  # Negative for minimization

def analytical_optimum():
    """Known analytical optimum"""
    # df/dx = cos(x) - 2sin(2x) = 0
    # Multiple local optima, global around x ≈ π/2
    return np.pi/2, -(np.sin(np.pi/2) + np.cos(np.pi))  # x=1.570, f=1.999

def quantum_inspired_step(x, lr=0.1):
    """
    Quantum-inspired optimization step using circuit-like rotation
    Simulates quantum interference effects via complex amplitude encoding
    """
    # Encode position as quantum rotation angle
    amplitude_real = np.cos(x)
    amplitude_imag = np.sin(x)
    
    # Quantum interference: rotate by gradient direction
    grad = np.cos(x) - 2*np.sin(2*x)  # Analytical gradient
    
    # Complex rotation with quantum-inspired interference
    rotation_angle = lr * grad
    new_amp_real = amplitude_real * np.cos(rotation_angle) - amplitude_imag * np.sin(rotation_angle)
    new_amp_imag = amplitude_real * np.sin(rotation_angle) + amplitude_imag * np.cos(rotation_angle)
    
    # Extract new position from amplitude
    new_x = np.arctan2(new_amp_imag, new_amp_real)
    
    return new_x

def run_quantum_optimization(x_init, max_iter=100, lr=0.1, tolerance=1e-6):
    """Quantum-inspired optimization trajectory"""
    trajectory = [x_init]
    x = x_init
    
    for i in range(max_iter):
        x_new = quantum_inspired_step(x, lr)
        trajectory.append(x_new)
        
        if abs(x_new - x) < tolerance:
            break
            
        x = x_new
    
    return trajectory

def run_classical_optimization(x_init, max_iter=100, lr=0.1, tolerance=1e-6):
    """Classical gradient descent"""
    trajectory = [x_init]
    x = x_init
    
    for i in range(max_iter):
        grad = np.cos(x) - 2*np.sin(2*x)  # Analytical gradient of -f(x)
        x_new = x - lr * grad  # Gradient descent
        trajectory.append(x_new)
        
        if abs(x_new - x) < tolerance:
            break
            
        x = x_new
    
    return trajectory

def benchmark_convergence(n_seeds=20, x_range=(-np.pi, np.pi)):
    """Compare quantum vs classical optimization across multiple random starts"""
    
    x_opt, f_opt = analytical_optimum()
    
    # Random initialization seeds
    np.random.seed(42)  # Reproducible
    x_inits = np.random.uniform(x_range[0], x_range[1], n_seeds)
    
    quantum_results = []
    classical_results = []
    
    for x_init in x_inits:
        # Quantum optimization
        start_time = time.time()
        q_traj = run_quantum_optimization(x_init)
        q_time = time.time() - start_time
        
        q_final = q_traj[-1]
        q_final_f = -objective_function(q_final)
        q_error = abs(q_final_f - f_opt)
        q_iterations = len(q_traj) - 1
        
        quantum_results.append({
            'final_x': q_final,
            'final_f': q_final_f,
            'error': q_error,
            'iterations': q_iterations,
            'time': q_time,
            'trajectory': q_traj
        })
        
        # Classical optimization
        start_time = time.time()
        c_traj = run_classical_optimization(x_init)
        c_time = time.time() - start_time
        
        c_final = c_traj[-1]
        c_final_f = -objective_function(c_final)
        c_error = abs(c_final_f - f_opt)
        c_iterations = len(c_traj) - 1
        
        classical_results.append({
            'final_x': c_final,
            'final_f': c_final_f,
            'error': c_error,
            'iterations': c_iterations,
            'time': c_time,
            'trajectory': c_traj
        })
    
    return quantum_results, classical_results, x_inits

def analyze_results(quantum_results, classical_results):
    """Statistical analysis of optimization performance"""
    
    q_errors = [r['error'] for r in quantum_results]
    c_errors = [r['error'] for r in classical_results]
    
    q_iterations = [r['iterations'] for r in quantum_results]
    c_iterations = [r['iterations'] for r in classical_results]
    
    q_times = [r['time'] for r in quantum_results]
    c_times = [r['time'] for r in classical_results]
    
    analysis = {
        'quantum_mean_error': np.mean(q_errors),
        'classical_mean_error': np.mean(c_errors),
        'quantum_std_error': np.std(q_errors),
        'classical_std_error': np.std(c_errors),
        'quantum_mean_iterations': np.mean(q_iterations),
        'classical_mean_iterations': np.mean(c_iterations),
        'quantum_mean_time': np.mean(q_times),
        'classical_mean_time': np.mean(c_times),
        'quantum_success_rate': np.mean([e < 0.01 for e in q_errors]),
        'classical_success_rate': np.mean([e < 0.01 for e in c_errors])
    }
    
    return analysis

def create_benchmark_plot(quantum_results, classical_results, x_inits, analysis):
    """Generate comprehensive benchmark visualization"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: Convergence trajectories (first 5 seeds)
    x_plot = np.linspace(-np.pi, np.pi, 1000)
    f_plot = -(np.sin(x_plot) + np.cos(2*x_plot))
    
    ax1.plot(x_plot, f_plot, 'k-', alpha=0.3, label='f(x) = sin(x) + cos(2x)')
    
    for i in range(min(5, len(quantum_results))):
        q_traj = quantum_results[i]['trajectory']
        c_traj = classical_results[i]['trajectory']
        
        q_f_traj = [-objective_function(x) for x in q_traj]
        c_f_traj = [-objective_function(x) for x in c_traj]
        
        ax1.plot(q_traj, q_f_traj, 'b-', alpha=0.6, linewidth=1)
        ax1.plot(c_traj, c_f_traj, 'r-', alpha=0.6, linewidth=1)
    
    ax1.axhline(y=1.999, color='gold', linestyle='--', alpha=0.8, label='Analytical optimum')
    ax1.set_xlabel('x')
    ax1.set_ylabel('f(x)')
    ax1.set_title('Optimization Trajectories (Blue: Quantum, Red: Classical)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Error distribution
    q_errors = [r['error'] for r in quantum_results]
    c_errors = [r['error'] for r in classical_results]
    
    ax2.hist(q_errors, bins=10, alpha=0.7, color='blue', label=f'Quantum (μ={analysis["quantum_mean_error"]:.4f})')
    ax2.hist(c_errors, bins=10, alpha=0.7, color='red', label=f'Classical (μ={analysis["classical_mean_error"]:.4f})')
    ax2.set_xlabel('Final Error |f - f_opt|')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Error Distribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Iteration count comparison
    q_iterations = [r['iterations'] for r in quantum_results]
    c_iterations = [r['iterations'] for r in classical_results]
    
    ax3.scatter(range(len(q_iterations)), q_iterations, color='blue', alpha=0.6, label='Quantum')
    ax3.scatter(range(len(c_iterations)), c_iterations, color='red', alpha=0.6, label='Classical')
    ax3.axhline(y=analysis['quantum_mean_iterations'], color='blue', linestyle='--', alpha=0.8)
    ax3.axhline(y=analysis['classical_mean_iterations'], color='red', linestyle='--', alpha=0.8)
    ax3.set_xlabel('Seed Index')
    ax3.set_ylabel('Iterations to Convergence')
    ax3.set_title('Convergence Speed Comparison')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Success rate and summary statistics
    methods = ['Quantum', 'Classical']
    success_rates = [analysis['quantum_success_rate'], analysis['classical_success_rate']]
    mean_errors = [analysis['quantum_mean_error'], analysis['classical_mean_error']]
    
    ax4_twin = ax4.twinx()
    
    bars1 = ax4.bar([0, 1], success_rates, alpha=0.7, color=['blue', 'red'], 
                   label='Success Rate (error < 0.01)')
    bars2 = ax4_twin.bar([0.2, 1.2], mean_errors, alpha=0.7, color=['lightblue', 'pink'],
                        width=0.4, label='Mean Error')
    
    ax4.set_ylabel('Success Rate')
    ax4_twin.set_ylabel('Mean Error')
    ax4.set_xlabel('Method')
    ax4.set_xticks([0.1, 1.1])
    ax4.set_xticklabels(methods)
    ax4.set_title('Performance Summary')
    
    # Add value labels on bars
    for bar, val in zip(bars1, success_rates):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{val:.2f}', ha='center', va='bottom')
    
    for bar, val in zip(bars2, mean_errors):
        ax4_twin.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                     f'{val:.3f}', ha='center', va='bottom')
    
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='upper left')
    ax4_twin.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/quantum_optimization_benchmark.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return analysis

def main():
    """Main benchmark execution"""
    print("=== Quantum vs Classical Optimization Benchmark ===")
    print("Testing HYP-039: Quantum-inspired circuit optimization claims")
    print()
    
    # Run benchmark
    quantum_results, classical_results, x_inits = benchmark_convergence(n_seeds=25)
    
    # Analyze results
    analysis = analyze_results(quantum_results, classical_results)
    
    # Create visualization
    create_benchmark_plot(quantum_results, classical_results, x_inits, analysis)
    
    # Print detailed results
    print("BENCHMARK RESULTS:")
    print("==================")
    print(f"Quantum Mean Error: {analysis['quantum_mean_error']:.6f} ± {analysis['quantum_std_error']:.6f}")
    print(f"Classical Mean Error: {analysis['classical_mean_error']:.6f} ± {analysis['classical_std_error']:.6f}")
    print()
    print(f"Quantum Mean Iterations: {analysis['quantum_mean_iterations']:.2f}")
    print(f"Classical Mean Iterations: {analysis['classical_mean_iterations']:.2f}")
    print()
    print(f"Quantum Success Rate (error < 0.01): {analysis['quantum_success_rate']:.2%}")
    print(f"Classical Success Rate (error < 0.01): {analysis['classical_success_rate']:.2%}")
    print()
    print(f"Quantum Mean Time: {analysis['quantum_mean_time']:.6f} seconds")
    print(f"Classical Mean Time: {analysis['classical_mean_time']:.6f} seconds")
    print()
    
    # Verdict
    quantum_better_accuracy = analysis['quantum_mean_error'] < analysis['classical_mean_error']
    quantum_better_speed = analysis['quantum_mean_iterations'] < analysis['classical_mean_iterations']
    quantum_better_success = analysis['quantum_success_rate'] > analysis['classical_success_rate']
    
    print("VERDICT:")
    print("========")
    if quantum_better_accuracy and quantum_better_speed and quantum_better_success:
        print("✓ HYPOTHESIS SUPPORTED: Quantum-inspired optimization outperforms classical")
    elif quantum_better_accuracy or quantum_better_speed or quantum_better_success:
        print("~ HYPOTHESIS PARTIALLY SUPPORTED: Mixed performance advantages")
    else:
        print("✗ HYPOTHESIS REFUTED: Classical optimization performs better")
    
    print()
    print("Detailed metrics saved to shared_agora/artifacts/quantum_optimization_benchmark.png")
    
    return analysis

if __name__ == "__main__":
    main()