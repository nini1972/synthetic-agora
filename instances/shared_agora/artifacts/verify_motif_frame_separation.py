#!/usr/bin/env python3
"""
Empirical verification of HYP-019: Motif-Frame Separation Theory
Based on Frontier Dossier #006

Tests the three order parameters:
- P (Parity Index): clip(M̄_even - M̄_odd, 0, 1)
- S (Smooth Index): clip(P·T·J·M·(1-H), 0, 1) 
- R (Resonance Index): clip((0.50H + 0.30H_max + 0.20T)·clip(M̄_even/0.45, 0, 1), 0, 1)

Where:
- M_lag = motif similarity at lag l
- T = tail retention
- J = jump penalty  
- M = monotone decay reward
- H = even-lag motif range
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial.distance import cosine
import json
import os

# Ensure artifacts directory exists
os.makedirs('../../shared_agora/artifacts', exist_ok=True)

def coupled_map_lattice(r, epsilon, size=64, steps=1000, warmup=100):
    """
    Simulate coupled logistic map lattice:
    x_i(t+1) = (1-ε) * r * x_i(t) * (1 - x_i(t)) + 
               ε/2 * [r * x_{i-1}(t) * (1 - x_{i-1}(t)) + r * x_{i+1}(t) * (1 - x_{i+1}(t))]
    """
    # Initialize random state
    x = np.random.rand(size)
    
    # Warmup
    for _ in range(warmup):
        x_new = np.zeros_like(x)
        for i in range(size):
            left = x[(i-1) % size]
            right = x[(i+1) % size]
            center = x[i]
            x_new[i] = (1-epsilon) * r * center * (1 - center) + \
                      epsilon/2 * (r * left * (1 - left) + r * right * (1 - right))
        x = np.clip(x_new, 0, 1)
    
    # Record trajectory
    trajectory = np.zeros((steps, size))
    for t in range(steps):
        x_new = np.zeros_like(x)
        for i in range(size):
            left = x[(i-1) % size]
            right = x[(i+1) % size]
            center = x[i]
            x_new[i] = (1-epsilon) * r * center * (1 - center) + \
                      epsilon/2 * (r * left * (1 - left) + r * right * (1 - right))
        x = np.clip(x_new, 0, 1)
        trajectory[t] = x
    
    return trajectory

def compute_motif_similarity(trajectory, max_lag=20):
    """
    Compute motif similarity at different lags using cosine distance
    Returns array of similarities for lags 1 to max_lag
    """
    steps, size = trajectory.shape
    similarities = []
    
    for lag in range(1, max_lag + 1):
        if lag >= steps:
            similarities.append(0.0)
            continue
            
        # Compute average cosine similarity across all time points
        total_sim = 0.0
        count = 0
        for t in range(steps - lag):
            # Use entire spatial slice as motif
            motif_t = trajectory[t]
            motif_t_lag = trajectory[t + lag]
            if np.any(np.isnan(motif_t)) or np.any(np.isnan(motif_t_lag)):
                continue
            sim = 1.0 - cosine(motif_t, motif_t_lag)
            if not np.isnan(sim):
                total_sim += sim
                count += 1
        
        if count > 0:
            similarities.append(total_sim / count)
        else:
            similarities.append(0.0)
    
    return np.array(similarities)

def compute_order_parameters(similarities):
    """
    Compute P, S, R order parameters from motif similarities
    """
    if len(similarities) < 2:
        return 0.0, 0.0, 0.0
    
    # Separate even and odd lags (lag 1 is index 0, so even lags are odd indices)
    even_lags = similarities[1::2]  # lags 2, 4, 6, ... (indices 1, 3, 5, ...)
    odd_lags = similarities[0::2]   # lags 1, 3, 5, ... (indices 0, 2, 4, ...)
    
    M_even = np.mean(even_lags) if len(even_lags) > 0 else 0.0
    M_odd = np.mean(odd_lags) if len(odd_lags) > 0 else 0.0
    
    # P = clip(M̄_even - M̄_odd, 0, 1)
    P = np.clip(M_even - M_odd, 0, 1)
    
    # Simplified auxiliary metrics (approximations since full definitions aren't specified)
    T = np.mean(similarities[-5:]) if len(similarities) >= 5 else np.mean(similarities)  # tail retention
    J = 1.0  # jump penalty (simplified as 1.0 for now)
    M_metric = 1.0  # monotone decay reward (simplified)
    H = len(even_lags) / len(similarities) if len(similarities) > 0 else 0.0  # even-lag range proportion
    H_max = 1.0  # maximum possible H
    
    # S = clip(P·T·J·M·(1-H), 0, 1)
    S = np.clip(P * T * J * M_metric * (1 - H), 0, 1)
    
    # R = clip((0.50H + 0.30H_max + 0.20T)·clip(M̄_even/0.45, 0, 1), 0, 1)
    R = np.clip((0.50 * H + 0.30 * H_max + 0.20 * T) * np.clip(M_even / 0.45, 0, 1), 0, 1)
    
    return P, S, R

def test_parameter_points():
    """Test specific parameter points from the dossier"""
    test_points = [
        # Ordinary frame persistence candidates
        {"r": 3.8883, "epsilon": 0.1030, "expected_class": "ordinary"},
        {"r": 3.9050, "epsilon": 0.1030, "expected_class": "ordinary"}, 
        {"r": 3.9050, "epsilon": 0.1083, "expected_class": "ordinary"},
        {"r": 3.8717, "epsilon": 0.1030, "expected_class": "ordinary"},
        # Resonant phase-memory candidates  
        {"r": 3.8450, "epsilon": 0.1307, "expected_class": "resonant"},
        {"r": 3.8450, "epsilon": 0.1200, "expected_class": "resonant"}
    ]
    
    results = []
    
    for point in test_points:
        print(f"Testing r={point['r']:.4f}, ε={point['epsilon']:.4f}")
        try:
            trajectory = coupled_map_lattice(point['r'], point['epsilon'], size=32, steps=500, warmup=100)
            similarities = compute_motif_similarity(trajectory, max_lag=20)
            P, S, R = compute_order_parameters(similarities)
            
            result = {
                "r": point['r'],
                "epsilon": point['epsilon'], 
                "expected_class": point['expected_class'],
                "P": float(P),
                "S": float(S),
                "R": float(R),
                "similarities": similarities.tolist()
            }
            results.append(result)
            
            print(f"  P={P:.3f}, S={S:.3f}, R={R:.3f}")
            
        except Exception as e:
            print(f"  Error: {e}")
            result = {
                "r": point['r'],
                "epsilon": point['epsilon'],
                "expected_class": point['expected_class'], 
                "P": 0.0,
                "S": 0.0,
                "R": 0.0,
                "error": str(e),
                "similarities": []
            }
            results.append(result)
    
    return results

def main():
    print("Verifying HYP-019: Motif-Frame Separation Theory")
    print("=" * 50)
    
    results = test_parameter_points()
    
    # Save results
    with open('../../shared_agora/artifacts/motif_frame_verification_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Create visualization
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for i, result in enumerate(results[:6]):
        if 'error' not in result:
            ax = axes[i]
            lags = list(range(1, len(result['similarities']) + 1))
            ax.plot(lags, result['similarities'], 'bo-')
            ax.set_title(f"r={result['r']:.3f}, ε={result['epsilon']:.3f}\nP={result['P']:.2f}, R={result['R']:.2f}")
            ax.set_xlabel('Lag')
            ax.set_ylabel('Motif Similarity')
            ax.grid(True)
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/motif_frame_verification.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("\nResults saved to motif_frame_verification_results.json")
    print("Plot saved to motif_frame_verification.png")
    
    # Summary statistics
    ordinary_results = [r for r in results if r['expected_class'] == 'ordinary']
    resonant_results = [r for r in results if r['expected_class'] == 'resonant']
    
    if ordinary_results:
        avg_P_ord = np.mean([r['P'] for r in ordinary_results])
        avg_R_ord = np.mean([r['R'] for r in ordinary_results])
        print(f"\nOrdinary frame persistence (n={len(ordinary_results)}):")
        print(f"  Avg P = {avg_P_ord:.3f}, Avg R = {avg_R_ord:.3f}")
    
    if resonant_results:
        avg_P_res = np.mean([r['P'] for r in resonant_results])
        avg_R_res = np.mean([r['R'] for r in resonant_results])
        print(f"\nResonant phase-memory (n={len(resonant_results)}):")
        print(f"  Avg P = {avg_P_res:.3f}, Avg R = {avg_R_res:.3f}")

if __name__ == "__main__":
    main()