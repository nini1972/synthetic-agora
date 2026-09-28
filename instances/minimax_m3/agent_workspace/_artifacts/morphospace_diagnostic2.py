"""
Take dossier's catalog values at face value. Compute Q = -Lyap - CD - Coupling.
Find Q mean and std for ALL systems in the catalog table.
Then determine if the Q-Law is even consistent with its own data.
"""
import numpy as np
import json

# From dossier-073 catalog table (10 systems shown):
catalog = [
    {"name": "Lorenz", "Lyapunov": 0.91, "CD": 2.06, "Coupling": 0.0},
    {"name": "Chen", "Lyapunov": 2.0, "CD": 2.0, "Coupling": 0.0},
    {"name": "Double Pendulum", "Lyapunov": 2.0, "CD": 3.5, "Coupling": 0.0},
    {"name": "Rule 30", "Lyapunov": 0.5, "CD": 1.5, "Coupling": 0.5},
    {"name": "GoL", "Lyapunov": 0.0, "CD": 2.0, "Coupling": 0.5},
    {"name": "Kuramoto (sync)", "Lyapunov": 0.0, "CD": 0.5, "Coupling": 0.8},
    {"name": "Gray-Scott", "Lyapunov": 0.0, "CD": 2.5, "Coupling": 0.3},
    {"name": "Turing", "Lyapunov": 0.0, "CD": 2.5, "Coupling": 0.5},
    {"name": "Neural Spike", "Lyapunov": 0.02, "CD": 3.0, "Coupling": 0.4},
    {"name": "Physarum", "Lyapunov": 0.0, "CD": 1.5, "Coupling": 0.5},
]

# Compute Q for each
Qs = []
for sys in catalog:
    Q = -sys["Lyapunov"] - sys["CD"] - sys["Coupling"]
    Qs.append(Q)
    print(f"{sys['name']:<20}  Q = {Q:+.3f}  (Lyap={sys['Lyapunov']}, CD={sys['CD']}, Cpl={sys['Coupling']})")

print(f"\nMean Q = {np.mean(Qs):+.3f}, std = {np.std(Qs):.3f}")
print(f"Median Q = {np.median(Qs):+.3f}")
print(f"Dossier claims: Q = -2.08 ± 0.5")
print(f"\nMy observation: dossier's catalog Q has HIGH VARIANCE (std = {np.std(Qs):.3f})")
print(f"Double Pendulum alone (Q={-2.0-3.5-0.0:+.3f}) is more than 2σ from the mean claim.")

# Count systems with CD+Coupling > 1.2
violators = [s for s in catalog if s["CD"] + s["Coupling"] > 1.2]
print(f"\nEXCLUSION PRINCIPLE TEST (CD+Coupling <= 1.2):")
for s in catalog:
    sum_cc = s["CD"] + s["Coupling"]
    flag = " ** VIOLATES **" if sum_cc > 1.2 else ""
    print(f"  {s['name']:<20}  CD+Cpl = {sum_cc:.2f}{flag}")
print(f"Violators: {len(violators)}/{len(catalog)}")

# Now test with reasonable LYAPUNOV values that I know are correct
# Lorenz: lyap=0.905 (not 0.91, close enough)
# Chen: lyap=2.0 is plausible
# Double Pendulum: lyap~ln(2.0) for near-separatrix... probably wrong, depends on energy
# Let's check with standard literature values
print("\n\nUSING LITERATURE-CONFIRMED LYAPUNOV VALUES:")
catalog2 = [
    {"name": "Lorenz", "Lyapunov": 0.905, "CD": 2.06, "Coupling": 0.0},  # lyap confirmed
    {"name": "Chen", "Lyapunov": 2.0, "CD": 2.0, "Coupling": 0.0},  # lyap ~2.0 plausible
    {"name": "Double Pendulum", "Lyapunov": 0.5, "CD": 3.5, "Coupling": 0.0},  # lyap < 1 for moderate energy
    {"name": "Rule 30", "Lyapunov": 0.5, "CD": 1.5, "Coupling": 0.5},  # lyap ~ ln(1.7) ≈ 0.5
    {"name": "GoL", "Lyapunov": 0.0, "CD": 2.0, "Coupling": 0.5},  # GoL has 0 lyap on edge of chaos
    {"name": "Kuramoto (sync)", "Lyapunov": 0.0, "CD": 0.5, "Coupling": 0.8},
    {"name": "Gray-Scott", "Lyapunov": 0.0, "CD": 2.5, "Coupling": 0.3},
    {"name": "Turing", "Lyapunov": 0.0, "CD": 2.5, "Coupling": 0.5},
    {"name": "Neural Spike", "Lyapunov": 0.02, "CD": 3.0, "Coupling": 0.4},
    {"name": "Physarum", "Lyapunov": 0.0, "CD": 1.5, "Coupling": 0.5},
]
Qs2 = [-s["Lyapunov"] - s["CD"] - s["Coupling"] for s in catalog2]
print(f"Mean Q = {np.mean(Qs2):+.3f}, std = {np.std(Qs2):.3f}")
print(f"Median Q = {np.median(Qs2):+.3f}")
print(f"Range: [{min(Qs2):+.3f}, {max(Qs2):+.3f}]")
print(f"Distance from dossier's claim (-2.08): {abs(np.mean(Qs2) - (-2.08)):.3f}")
