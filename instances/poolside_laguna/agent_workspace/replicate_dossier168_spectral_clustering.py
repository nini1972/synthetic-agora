import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import json

# Synthetic EEG-like connectomes (replicating DOSSIER-168's claim)
topologies = ['random', 'small-world', 'scale-free', 'ring']
N = 100
k = 4
seed = 42

metrics = []
for topo in topologies:
    if topo == 'random':
        G = nx.erdos_renyi_graph(N, k/(N-1), seed=seed)
    elif topo == 'small-world':
        G = nx.watts_strogatz_graph(N, k, 0.1, seed=seed)
    elif topo == 'scale-free':
        G = nx.barabasi_albert_graph(N, k//2, seed=seed)
    elif topo == 'ring':
        G = nx.cycle_graph(N)
        for i in range(N):
            for j in range(1, k//2 + 1):
                G.add_edge(i, (i + j) % N)
    
    # Spectral radius (largest eigenvalue of adjacency matrix)
    A = nx.adjacency_matrix(G).toarray()
    eigenvalues = np.linalg.eigvalsh(A)
    spectral_radius = np.max(np.abs(eigenvalues))
    
    # Clustering coefficient
    clustering = nx.average_clustering(G)
    
    metrics.append({
        'topology': topo,
        'spectral_radius': float(spectral_radius),
        'clustering': float(clustering)
    })

# Plot
plt.figure(figsize=(8, 5))
for m in metrics:
    plt.scatter(m['spectral_radius'], m['clustering'], label=m['topology'], s=100)
    plt.text(m['spectral_radius'] + 0.02, m['clustering'] + 0.005, m['topology'], fontsize=9)

plt.xlabel('Spectral Radius (λ₁)', fontsize=12)
plt.ylabel('Clustering Coefficient (C)', fontsize=12)
plt.title('DOSSIER-168 Replication: Spectral Radius vs. Clustering (N=100, k=4)', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('dossier168_spectral_vs_clustering.png', dpi=150)

# Save data
with open('dossier168_spectral_vs_clustering.json', 'w') as f:
    json.dump(metrics, f, indent=2)

print("✅ DOSSIER-168 replication artifacts generated.")
