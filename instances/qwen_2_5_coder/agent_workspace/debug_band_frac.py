import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

def compute_band_frac(time_series, num_bands=10):
    """Compute band fraction metric for a time series."""
    if len(time_series) == 0:
        return 0.0
    
    # Handle constant series
    if np.all(time_series == time_series[0]):
        return 0.0
        
    min_val, max_val = np.min(time_series), np.max(time_series)
    if max_val == min_val:
        return 0.0
        
    band_width = (max_val - min_val) / num_bands
    if band_width == 0:
        return 0.0
        
    # Assign each point to a band
    normalized = (time_series - min_val) / (max_val - min_val)
    bands = (normalized * num_bands).astype(int)
    bands = np.clip(bands, 0, num_bands - 1)
    
    # Count unique bands visited
    unique_bands = len(np.unique(bands))
    return unique_bands / num_bands

# Test with different series lengths and band counts
harmonic = np.sin(2 * np.pi * 0.1 * np.linspace(0, 100, 100))

print("Harmonic oscillator analysis:")
print(f"Series length: {len(harmonic)}")
print(f"Min: {np.min(harmonic):.3f}, Max: {np.max(harmonic):.3f}")
print(f"Unique values: {len(np.unique(harmonic))}")

# Test different band counts
for bands in [5, 10, 20, 50]:
    bf = compute_band_frac(harmonic, num_bands=bands)
    print(f"Bands={bands}: band_frac={bf:.3f}")

# Test with shorter series
short_harmonic = np.sin(2 * np.pi * 0.1 * np.linspace(0, 10, 10))
print(f"\nShort series (length 10): band_frac={compute_band_frac(short_harmonic):.3f}")

# Test constant series
constant = np.ones(100)
print(f"Constant series: band_frac={compute_band_frac(constant):.3f}")

# Test what happens with very few points
few_points = np.array([0.1, 0.9])
print(f"Two points: band_frac={compute_band_frac(few_points):.3f}")

# Let's also check the actual band assignments
normalized = (harmonic - np.min(harmonic)) / (np.max(harmonic) - np.min(harmonic))
bands_10 = (normalized * 10).astype(int)
bands_10 = np.clip(bands_10, 0, 9)
print(f"\nBand assignments for first 20 points: {bands_10[:20]}")
print(f"Unique bands visited: {len(np.unique(bands_10))}")
print(f"All bands: {np.unique(bands_10)}")