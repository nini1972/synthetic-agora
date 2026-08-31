import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull

# Ensure headless plotting
import matplotlib
matplotlib.use('Agg')

# Use reported coordinates from PRF-004
points = {
    'R-pentomino': (0.065, 0.036),
    'Random': (0.045, 0.046),
    'Glider': (0.055, 0.036),
    'Block': (0.060, 0.036)
}

labels = list(points.keys())
coords = np.array([points[label] for label in labels])

# Hull from first three points
hull_points = coords[[0, 1, 2]]  # R-pentomino, Random, Glider
hull = ConvexHull(hull_points)

# Check if Block is inside
from matplotlib.path import Path
hull_path = Path(hull_points[hull.vertices])
block_inside = hull_path.contains_point(points['Block'])

# Plot
plt.figure(figsize=(6, 5))
plt.plot(coords[:, 0], coords[:, 1], 'o', markersize=8)
for i, label in enumerate(labels):
    plt.text(coords[i, 0] + 0.001, coords[i, 1] + 0.001, label)

# Plot hull edges
for simplex in hull.simplices:
    plt.plot(hull_points[simplex, 0], hull_points[simplex, 1], 'k-')

plt.xlabel('Spatial LZ Complexity')
plt.ylabel('Temporal LZ Complexity')
plt.title(f'GoL Complexity Hull — Block inside: {block_inside}')
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/gol_hull_verification.png')
print(f"Block inside hull: {block_inside}")