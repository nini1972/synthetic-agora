"""
Test the third claim: TemporalMemory * SpatialEntropy < 0.5
Check dossier's own catalog.
"""
import numpy as np

catalog = [
    {"name": "Lorenz", "TempMemory": 0.4, "SpaEntropy": 0.0},
    {"name": "Chen", "TempMemory": 0.2, "SpaEntropy": 0.0},
    {"name": "Double Pendulum", "TempMemory": 0.1, "SpaEntropy": 0.0},
    {"name": "Rule 30", "TempMemory": 0.2, "SpaEntropy": 0.8},
    {"name": "GoL", "TempMemory": 0.4, "SpaEntropy": 0.7},
    {"name": "Kuramoto (sync)", "TempMemory": 0.1, "SpaEntropy": 0.0},
    {"name": "Gray-Scott", "TempMemory": 0.2, "SpaEntropy": 0.8},
    {"name": "Turing", "TempMemory": 0.1, "SpaEntropy": 0.8},
    {"name": "Neural Spike", "TempMemory": 0.8, "SpaEntropy": 0.5},
    {"name": "Physarum", "TempMemory": 0.3, "SpaEntropy": 0.6},
]

print("TEMPORAL-SPATIAL COMPLEMENTARITY TEST (TM*SE < 0.5):")
print(f"{'System':<20}  TM={'':<5}  SE={'':<5}  TM*SE={'':<5}  Status")
for s in catalog:
    product = s["TempMemory"] * s["SpaEntropy"]
    flag = "OK" if product < 0.5 else "** VIOLATES **"
    print(f"  {s['name']:<20}  TM={s['TempMemory']:.2f}    SE={s['SpaEntropy']:.2f}    TM*SE={product:.3f}    {flag}")

violators = [s for s in catalog if s["TempMemory"] * s["SpaEntropy"] >= 0.5]
print(f"\nViolators: {len(violators)}/{len(catalog)}")

# Detailed analysis
print("\nCRITICAL OBSERVATIONS:")
print("1. GoL: TM*SE = 0.4*0.7 = 0.28 (below 0.5, so OK)")
print("2. Neural Spike: TM*SE = 0.8*0.5 = 0.40 (below 0.5)")
print("3. Rule 30: TM*SE = 0.2*0.8 = 0.16 (below 0.5)")
print("4. ALL listed systems happen to satisfy TM*SE < 0.5 in the catalog.")
print()
print("However: This may be CONFOUNDED by data construction. If Temporal Memory and")
print("Spatial Entropy are MEASURED ON DIFFERENT AXES (e.g., TM uses 1D signal, SE uses 2D)")
print("they could appear small artificially.")

# Note: The dossier says TemporalMemory*<0.5 - this is a CATASTROPHIC failure if violated
# ALL catalogued systems pass, but the claim would be falsified by ANY system with both high
# Let's see what a counterexample might look like:
print("\nCounterexample search: A system with both TM=0.8 and SE=0.8 would have TM*SE=0.64 > 0.5")
print("This could happen for: SIRS with spatial structure (DOSSIER_071),")
print("Reaction-diffusion with memory (any 2D delayed PDE),")
print("Spatiotemporal chaos (coupled map lattices).")
