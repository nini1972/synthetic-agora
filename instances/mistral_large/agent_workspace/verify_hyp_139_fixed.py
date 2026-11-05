#!/usr/bin/env python3
"""
World C Replication for HYP-139: Lenia2D Critical Exponent β (Fixed)
- Tests β invariance across kernel radii (σ_k) and grid sizes.
- Uses colony_lib.dynamics.Lenia2D and colony_lib.scaling_analysis.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from colony_lib.dynamics import Lenia2D
from colony_lib.scaling_analysis import fit_scaling_law
from colony_lib.persistence import StageTracker

# --- Parameters ---
mu_range = np.linspace(0.12, 0.19, 50)
sigma_g = 0.05
sigma_k_values = [5, 10, 15, 20, 25]
grid_sizes = [32, 64, 128]
T_transient = 100
T_measure = 500
stage_name = "lenia_critical_exponent_scan"

# --- Stage Tracker ---
tracker = StageTracker(stage_name)


def run_lenia_scan(sigma_k, grid_size):
    """Run Lenia scan for a given σ_k and grid_size."""
    lenia = Lenia2D(
        grid_size=grid_size,
        kernel_radius=sigma_k,
        sigma_g=sigma_g,
        sigma_k=sigma_k,
        dt=1.0
    )
    
    # Initialize random state
    A = np.random.uniform(0, 1, (grid_size, grid_size))
    
    # Transient
    for _ in range(T_transient):
        A = lenia.update(A)
    
    # Measurement
    order_param = []
    for mu in mu_range:
        lenia.mu = mu  # Set mu after initialization
        A_mu = A.copy()
        for _ in range(T_measure):
            A_mu = lenia.update(A_mu)
        order_param.append(np.mean(A_mu))
    
    return np.array(order_param)


# --- Main ---
if __name__ == "__main__":
    results = {}
    
    for sigma_k in sigma_k_values:
        for grid_size in grid_sizes:
            key = f"sigma_k_{sigma_k}_grid_{grid_size}"
            if not tracker.is_done(key):
                print(f"Running {key}...")
                order_param = run_lenia_scan(sigma_k, grid_size)
                results[key] = order_param
                tracker.save_stage(key, order_param)
            else:
                print(f"Loading {key} from stage...")
                results[key] = tracker.get_stage(key)
    
    # --- Critical Exponent Extraction ---
    plt.figure(figsize=(12, 8))
    for sigma_k in sigma_k_values:
        for grid_size in grid_sizes:
            key = f"sigma_k_{sigma_k}_grid_{grid_size}"
            order_param = results[key]
            
            # Fit scaling law: ⟨A⟩ ~ (μ - μ_c)^β
            try:
                beta, mu_c = fit_scaling_law(
                    x_data=mu_range,
                    y_data=order_param,
                    form="(x - mu_c)^beta",
                    constraints={"mu_c": (0.12, 0.19), "beta": (0.0, 1.0)}
                )
                plt.plot(mu_range, order_param, label=f"σ_k={sigma_k}, grid={grid_size}, β={beta:.3f}")
                print(f"{key}: β={beta:.3f}, μ_c={mu_c:.3f}")
            except:
                print(f"Fit failed for {key}")
    
    plt.xlabel("Growth Parameter (μ)")
    plt.ylabel("Order Parameter ⟨A⟩")
    plt.title("Lenia2D Critical Exponent β (HYP-139 Replication)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig("world_c_results/lenia_critical_exponent_replication.png")
    plt.close()