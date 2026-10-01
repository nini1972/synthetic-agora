import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

def compute_band_frac(time_series, num_bands=10):
    """Compute band fraction metric for a time series."""
    if len(time_series) == 0:
        return 0.0
    
    if np.all(time_series == time_series[0]):
        return 0.0
        
    min_val, max_val = np.min(time_series), np.max(time_series)
    if max_val == min_val:
        return 0.0
        
    normalized = (time_series - min_val) / (max_val - min_val)
    bands = (normalized * num_bands).astype(int)
    bands = np.clip(bands, 0, num_bands - 1)
    
    unique_bands = len(np.unique(bands))
    return unique_bands / num_bands

def compute_band_exploration_rate(time_series, num_bands=10, window_size=50):
    """Compute how quickly bands are explored over time."""
    if len(time_series) < window_size:
        return compute_band_frac(time_series, num_bands)
    
    # Compute band fraction in sliding windows
    rates = []
    for i in range(0, len(time_series) - window_size + 1, window_size//2):
        window = time_series[i:i+window_size]
        bf = compute_band_frac(window, num_bands)
        rates.append(bf)
    
    return np.mean(rates)

def generate_adler_type_system(duration=200):
    """Simple periodic system - should be Adler-type."""
    t = np.linspace(0, duration, duration)
    return np.sin(2 * np.pi * 0.1 * t)

def generate_complex_system(duration=200):
    """More complex system with multiple frequencies."""
    t = np.linspace(0, duration, duration)
    return (np.sin(0.1*t) + 0.5*np.sin(0.3*t) + 0.2*np.sin(0.7*t))

def generate_chaotic_system(duration=200):
    """Chaotic-like system."""
    np.random.seed(42)
    return np.cumsum(np.random.randn(duration)) * 0.1

# Test with shorter duration to avoid saturation
systems = {
    "Adler_Type_Short": generate_adler_type_system(100),
    "Complex_Short": generate_complex_system(100), 
    "Chaotic_Short": generate_chaotic_system(100),
    "Adler_Type_VeryShort": generate_adler_type_system(30),
    "Complex_VeryShort": generate_complex_system(30)
}

results = {}
for name, series in systems.items():
    bf_final = compute_band_frac(series, num_bands=10)
    bf_rate = compute_band_exploration_rate(series, num_bands=10, window_size=20)
    results[name] = {"final_bf": bf_final, "exploration_rate": bf_rate}
    print(f"{name}: final_bf={bf_final:.3f}, exploration_rate={bf_rate:.3f}")

# Save results
import json
with open('../../shared_agora/artifacts/refined_band_analysis_results.json', 'w') as f:
    json.dump(results, f, indent=2)

# Create comparison plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

names = list(results.keys())
final_bf = [results[n]["final_bf"] for n in names]
exp_rates = [results[n]["exploration_rate"] for n in names]

ax1.bar(range(len(names)), final_bf, alpha=0.7, color='blue')
ax1.axhline(y=0.414, color='red', linestyle='--', label='Adler Ceiling')
ax1.set_xticks(range(len(names)))
ax1.set_xticklabels(names, rotation=45, ha='right')
ax1.set_ylabel('Final Band Fraction')
ax1.set_title('Final Band Fraction Comparison')
ax1.legend()

ax2.bar(range(len(names)), exp_rates, alpha=0.7, color='green')
ax2.axhline(y=0.414, color='red', linestyle='--', label='Adler Ceiling')
ax2.set_xticks(range(len(names)))
ax2.set_xticklabels(names, rotation=45, ha='right')
ax2.set_ylabel('Exploration Rate')
ax2.set_title('Band Exploration Rate Comparison')
ax2.legend()

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/refined_band_analysis_plot.png')
plt.close()

print("\nAnalysis Summary:")
print("-" * 50)
for name, vals in results.items():
    classification_final = "Adler" if vals["final_bf"] <= 0.414 else "Cascade"
    classification_rate = "Adler" if vals["exploration_rate"] <= 0.414 else "Cascade"
    print(f"{name}: Final={classification_final}, Rate={classification_rate}")