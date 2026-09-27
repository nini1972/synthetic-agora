#!/usr/bin/env python3
"""
Empirical Test: Motif-Frame Separation in Coupled Map Lattices
Testing HYP-056 predictions about distinct memory mechanisms
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless mode
import matplotlib.pyplot as plt

def coupled_map_lattice(N, r, epsilon, T, x0=None):
    """
    Simulate coupled map lattice with logistic maps
    x_{i,t+1} = (1-ε)f(x_{i,t}) + ε/2[f(x_{i-1,t}) + f(x_{i+1,t})]
    where f(x) = rx(1-x)
    """
    if x0 is None:
        x = np.random.random(N)
    else:
        x = x0.copy()
    
    trajectory = np.zeros((T, N))
    trajectory[0] = x
    
    for t in range(1, T):
        x_new = np.zeros(N)
        for i in range(N):
            # Periodic boundary conditions
            left = (i - 1) % N
            right = (i + 1) % N
            
            # Coupled map update
            local = r * x[i] * (1 - x[i])
            neighbor = (r * x[left] * (1 - x[left]) + r * x[right] * (1 - x[right])) / 2
            x_new[i] = (1 - epsilon) * local + epsilon * neighbor
            
        x = x_new
        trajectory[t] = x
    
    return trajectory

def compute_motif_similarity(traj, lag, motif_size=3):
    """
    Compute motif similarity at given lag
    Motifs are spatial patterns of size motif_size
    """
    T, N = traj.shape
    if lag >= T or motif_size > N:
        return 0.0
    
    similarities = []
    for t in range(T - lag):
        if t + motif_size <= N:
            motif_t = traj[t, :motif_size]
            motif_t_lag = traj[t + lag, :motif_size]
            # Cosine similarity
            norm_t = np.linalg.norm(motif_t)
            norm_lag = np.linalg.norm(motif_t_lag)
            if norm_t > 0 and norm_lag > 0:
                sim = np.dot(motif_t, motif_t_lag) / (norm_t * norm_lag)
                similarities.append(sim)
    
    return np.mean(similarities) if similarities else 0.0

def compute_frame_correlation(traj, lag):
    """
    Compute whole-frame autocorrelation at given lag
    """
    T, N = traj.shape
    if lag >= T:
        return 0.0
    
    correlations = []
    for t in range(T - lag):
        frame_t = traj[t, :]
        frame_t_lag = traj[t + lag, :]
        corr = np.corrcoef(frame_t, frame_t_lag)[0, 1]
        if not np.isnan(corr):
            correlations.append(corr)
    
    return np.mean(correlations) if correlations else 0.0

def compute_order_parameters(traj, max_lag=10):
    """
    Compute P, S, R order parameters from Dossier #006
    """
    # Motif similarities for even and odd lags
    even_similarities = []
    odd_similarities = []
    
    for lag in range(2, max_lag + 1, 2):  # Even lags
        sim = compute_motif_similarity(traj, lag)
        even_similarities.append(sim)
    
    for lag in range(1, max_lag + 1, 2):  # Odd lags
        sim = compute_motif_similarity(traj, lag)
        odd_similarities.append(sim)
    
    M_even = np.mean(even_similarities)
    M_odd = np.mean(odd_similarities)
    
    # Parity index P
    P = np.clip(M_even - M_odd, 0, 1)
    
    # Simplified versions of S and R (missing some components from dossier)
    # Frame correlations
    frame_corrs = []
    for lag in range(1, max_lag + 1):
        corr = compute_frame_correlation(traj, lag)
        frame_corrs.append(corr)
    
    # Tail retention (how well correlations are maintained)
    T_retention = np.mean(frame_corrs[-3:]) if len(frame_corrs) >= 3 else 0
    
    # Even-lag motif range
    H = np.std(even_similarities) if len(even_similarities) > 1 else 0
    
    # Simplified S (smooth index)
    S = np.clip(P * T_retention * (1 - H), 0, 1)
    
    # Simplified R (resonance index)  
    R = np.clip((0.5 * H + 0.5 * T_retention) * np.clip(M_even / 0.45, 0, 1), 0, 1)
    
    return P, S, R, M_even, M_odd, frame_corrs

def test_parameter_space():
    """
    Test the hypothesis across parameter space focusing on claimed regions
    """
    # Test parameters from dossier
    test_points = [
        # Ordinary frame persistence candidates
        (3.8883, 0.1030, "ordinary_frame"),
        (3.9050, 0.1030, "ordinary_frame"), 
        (3.9050, 0.1083, "ordinary_frame"),
        (3.8717, 0.1030, "ordinary_frame"),
        # Motif-memory candidates  
        (3.8450, 0.1307, "motif_memory"),
        (3.8450, 0.1200, "motif_memory"),
        # Additional test points
        (3.860, 0.125, "test"),
        (3.870, 0.130, "test"),
    ]
    
    N = 50  # Lattice size
    T = 200  # Time steps
    results = []
    
    print("=== MOTIF-FRAME SEPARATION TEST ===")
    print("Testing HYP-056 predictions")
    print()
    
    for r, epsilon, expected_class in test_points:
        print(f"Testing r={r:.4f}, epsilon={epsilon:.4f} (expected: {expected_class})")
        
        # Run multiple seeds
        P_values = []
        S_values = []
        R_values = []
        
        for seed in range(3):
            np.random.seed(42 + seed)
            traj = coupled_map_lattice(N, r, epsilon, T)
            P, S, R, M_even, M_odd, frame_corrs = compute_order_parameters(traj)
            P_values.append(P)
            S_values.append(S)  
            R_values.append(R)
        
        P_mean = np.mean(P_values)
        S_mean = np.mean(S_values)
        R_mean = np.mean(R_values)
        
        print(f"  P = {P_mean:.3f} ± {np.std(P_values):.3f}")
        print(f"  S = {S_mean:.3f} ± {np.std(S_values):.3f}")
        print(f"  R = {R_mean:.3f} ± {np.std(R_values):.3f}")
        
        # Classification based on P threshold
        predicted_class = "motif_memory" if P_mean > 0.4 else "ordinary_frame"
        if expected_class == "test":
            match = True  # Test points don't have expected classification
        else:
            match = predicted_class.replace('_', '_') == expected_class
        
        print(f"  Predicted: {predicted_class}, Expected: {expected_class}, Match: {match}")
        print()
        
        results.append({
            'r': r, 'epsilon': epsilon, 'expected': expected_class,
            'P': P_mean, 'S': S_mean, 'R': R_mean,
            'predicted': predicted_class, 'match': match
        })
    
    return results

def generate_visualization(results):
    """
    Create visualization of parameter space classification
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # Extract data
    r_vals = [res['r'] for res in results]
    eps_vals = [res['epsilon'] for res in results] 
    P_vals = [res['P'] for res in results]
    S_vals = [res['S'] for res in results]
    R_vals = [res['R'] for res in results]
    matches = [res['match'] for res in results]
    
    # P vs parameters
    scatter1 = ax1.scatter(r_vals, eps_vals, c=P_vals, cmap='viridis', s=80, alpha=0.7)
    ax1.set_xlabel('r')
    ax1.set_ylabel('epsilon')  
    ax1.set_title('Parity Index P')
    plt.colorbar(scatter1, ax=ax1)
    
    # S vs parameters
    scatter2 = ax2.scatter(r_vals, eps_vals, c=S_vals, cmap='plasma', s=80, alpha=0.7)
    ax2.set_xlabel('r')
    ax2.set_ylabel('epsilon')
    ax2.set_title('Smooth Index S')
    plt.colorbar(scatter2, ax=ax2)
    
    # R vs parameters  
    scatter3 = ax3.scatter(r_vals, eps_vals, c=R_vals, cmap='coolwarm', s=80, alpha=0.7)
    ax3.set_xlabel('r')
    ax3.set_ylabel('epsilon')
    ax3.set_title('Resonance Index R')
    plt.colorbar(scatter3, ax=ax3)
    
    # Classification accuracy
    colors = ['red' if not m else 'green' for m in matches]
    ax4.scatter(r_vals, eps_vals, c=colors, s=80, alpha=0.7)
    ax4.set_xlabel('r')
    ax4.set_ylabel('epsilon')
    ax4.set_title('Classification Match (Green=Correct, Red=Wrong)')
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/motif_frame_separation_test.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """
    Run complete empirical test
    """
    results = test_parameter_space()
    generate_visualization(results)
    
    # Analysis
    total_tests = len(results)
    correct_matches = sum(1 for res in results if res['match'])
    accuracy = correct_matches / total_tests
    
    print("=== ANALYSIS ===")
    print(f"Classification Accuracy: {correct_matches}/{total_tests} = {accuracy:.3f}")
    print()
    
    # Test parity separation prediction
    ordinary_P = [res['P'] for res in results if 'ordinary' in res['expected']]
    motif_P = [res['P'] for res in results if 'motif' in res['expected']]
    
    print("Parity Index Statistics:")
    print(f"  Ordinary Frame P: {np.mean(ordinary_P):.3f} ± {np.std(ordinary_P):.3f}")
    print(f"  Motif Memory P: {np.mean(motif_P):.3f} ± {np.std(motif_P):.3f}")
    
    # Test clustering prediction
    motif_r = [res['r'] for res in results if 'motif' in res['expected']]
    motif_eps = [res['epsilon'] for res in results if 'motif' in res['expected']]
    
    print("Parameter Clustering (Motif Memory):")
    print(f"  r range: [{min(motif_r):.3f}, {max(motif_r):.3f}]")
    print(f"  epsilon range: [{min(motif_eps):.3f}, {max(motif_eps):.3f}]")
    
    # Verdict
    separation_quality = (np.mean(motif_P) - np.mean(ordinary_P)) / (np.std(ordinary_P) + np.std(motif_P) + 1e-6)
    
    print()
    print("=== VERDICT ===")
    if accuracy >= 0.75 and separation_quality > 1.0:
        print("STRONG SUPPORT for motif-frame separation hypothesis")
    elif accuracy >= 0.5 and separation_quality > 0.5:
        print("PARTIAL SUPPORT for motif-frame separation hypothesis") 
    else:
        print("WEAK/NO SUPPORT for motif-frame separation hypothesis")
        
    print(f"Evidence: {accuracy:.1%} classification accuracy, {separation_quality:.2f} separation quality")
    
    return results

if __name__ == "__main__":
    results = main()