import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import label
import os

def extract_emergence_features(param_values, complexity_values):
    """
    Extract 7-dimensional emergence archetype features from parameter-complexity trajectory.
    
    Args:
        param_values: array of control parameter values
        complexity_values: array of normalized complexity metric values (0-1)
    
    Returns:
        dict with 7 features
    """
    # Normalize complexity if not already done
    complexity_norm = np.array(complexity_values)
    if complexity_norm.max() > 1.0 or complexity_norm.min() < 0.0:
        complexity_norm = (complexity_norm - complexity_norm.min()) / (complexity_norm.max() - complexity_norm.min())
    
    # 1. n_phases - number of monotone segments
    diffs = np.diff(complexity_norm)
    # Find sign changes (excluding zeros)
    signs = np.sign(diffs)
    # Replace zeros with previous non-zero sign
    for i in range(1, len(signs)):
        if signs[i] == 0:
            signs[i] = signs[i-1]
    # Count sign changes
    sign_changes = np.sum(np.abs(np.diff(signs)) > 0)
    n_phases = sign_changes + 1
    
    # 2. band_frac - fraction in [0.3, 0.7]
    band_mask = (complexity_norm >= 0.3) & (complexity_norm <= 0.7)
    band_frac = np.mean(band_mask)
    
    # 3. asc_frac - fraction of ascending phases
    if n_phases == 1:
        asc_frac = 1.0 if diffs[0] > 0 else 0.0
    else:
        # Find phase boundaries
        phase_boundaries = [0]
        current_sign = signs[0]
        for i in range(1, len(signs)):
            if signs[i] != current_sign:
                phase_boundaries.append(i)
                current_sign = signs[i]
        phase_boundaries.append(len(complexity_norm))
        
        asc_count = 0
        for i in range(len(phase_boundaries)-1):
            start_idx = phase_boundaries[i]
            end_idx = phase_boundaries[i+1]
            if end_idx - start_idx > 1:
                phase_diff = complexity_norm[end_idx-1] - complexity_norm[start_idx]
                if phase_diff > 0:
                    asc_count += 1
        
        asc_frac = asc_count / n_phases if n_phases > 0 else 0.0
    
    # 4. sat_run - longest contiguous stretch > 0.85
    sat_mask = complexity_norm > 0.85
    sat_labels, sat_count = label(sat_mask)
    if sat_count > 0:
        sat_lengths = [np.sum(sat_labels == i) for i in range(1, sat_count+1)]
        sat_run = max(sat_lengths) / len(complexity_norm)
    else:
        sat_run = 0.0
    
    # 5. order_run - longest contiguous stretch < 0.15
    order_mask = complexity_norm < 0.15
    order_labels, order_count = label(order_mask)
    if order_count > 0:
        order_lengths = [np.sum(order_labels == i) for i in range(1, order_count+1)]
        order_run = max(order_lengths) / len(complexity_norm)
    else:
        order_run = 0.0
    
    # 6. auc - area under normalized curve (manual trapezoidal rule)
    if len(param_values) > 1:
        auc = np.sum((complexity_norm[:-1] + complexity_norm[1:]) * 
                    (param_values[1:] - param_values[:-1]) / 2) / (param_values[-1] - param_values[0])
    else:
        auc = 0.0
    
    # 7. var_d - variance of derivative
    if len(diffs) > 0:
        var_d = np.var(diffs)
    else:
        var_d = 0.0
    
    return {
        'n_phases': n_phases,
        'band_frac': band_frac,
        'asc_frac': asc_frac,
        'sat_run': sat_run,
        'order_run': order_run,
        'auc': auc,
        'var_d': var_d
    }

def test_thomas_labyrinth():
    """Test Thomas labyrinth data from EMP-039"""
    # Based on EMP-039: b in [0.16, 0.22], block complexity ~130 to ~390 to ~105
    b_values = np.linspace(0.16, 0.22, 20)
    # Simulate block complexity trajectory (normalized)
    # Peak around b=0.20, symmetric rise and fall
    complexity_raw = np.zeros_like(b_values)
    for i, b in enumerate(b_values):
        if b <= 0.20:
            complexity_raw[i] = 130 + (390-130) * (b-0.16)/(0.20-0.16)
        else:
            complexity_raw[i] = 390 - (390-105) * (b-0.20)/(0.22-0.20)
    
    complexity_norm = (complexity_raw - complexity_raw.min()) / (complexity_raw.max() - complexity_raw.min())
    features = extract_emergence_features(b_values, complexity_norm)
    return features, b_values, complexity_norm

def test_kuramoto_system():
    """Test Kuramoto system near critical point"""
    # Based on SYN-030: continuous transition at Kc=2.0
    K_values = np.linspace(1.0, 4.0, 30)
    # Order parameter r ~ sqrt(1 - Kc/K) for K > Kc
    complexity_raw = np.zeros_like(K_values)
    for i, K in enumerate(K_values):
        if K <= 2.0:
            complexity_raw[i] = 0.0
        else:
            complexity_raw[i] = np.sqrt(1 - 2.0/K)
    
    complexity_norm = complexity_raw.copy()  # Already normalized
    features = extract_emergence_features(K_values, complexity_norm)
    return features, K_values, complexity_norm

if __name__ == "__main__":
    # Test both systems
    thomas_features, thomas_params, thomas_complexity = test_thomas_labyrinth()
    kuramoto_features, kuramoto_params, kuramoto_complexity = test_kuramoto_system()
    
    print("Thomas Labyrinth Features:")
    for key, value in thomas_features.items():
        print(f"  {key}: {value:.4f}")
    
    print("\nKuramoto System Features:")
    for key, value in kuramoto_features.items():
        print(f"  {key}: {value:.4f}")
    
    # Plot comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    ax1.plot(thomas_params, thomas_complexity, 'b-o', markersize=4)
    ax1.set_xlabel('b parameter')
    ax1.set_ylabel('Normalized Complexity')
    ax1.set_title('Thomas Labyrinth')
    ax1.grid(True)
    
    ax2.plot(kuramoto_params, kuramoto_complexity, 'r-o', markersize=4)
    ax2.set_xlabel('K coupling')
    ax2.set_ylabel('Normalized Complexity')
    ax2.set_title('Kuramoto System')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/emergence_family_test.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Save features to JSON (convert numpy types to python types)
    import json
    def convert_numpy_types(obj):
        if isinstance(obj, dict):
            return {key: convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    results = {
        'thomas_labyrinth': convert_numpy_types(thomas_features),
        'kuramoto': convert_numpy_types(kuramoto_features)
    }
    with open('../../shared_agora/artifacts/emergence_family_features.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to emergence_family_features.json")
    print("Plot saved to emergence_family_test.png")