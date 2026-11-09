"""Local probe: confirm Lenia2D API + DOSSIER-173 order-parameter behavior at small N.
Goal: (1) see what run() returns, (2) test extract_critical_exponent clip behavior.
"""
import numpy as np
from colony_lib.dynamics import Lenia2D
from colony_lib.bifurcation_cartography import extract_critical_exponent

# --- API probe ---
L = Lenia2D(grid_size=48, kernel_radius=15, mu_g=0.15, sigma_g=0.05)
init = L.init_random(seed=0, density=0.5)
print("init shape", init.shape, "min/max", init.min(), init.max())
out = L.run(steps=20)
print("run() returns dict with keys:", list(out.keys()))
print("sample values:", {k: (np.asarray(v).shape if hasattr(v,'shape') else v) for k,v in out.items()})

# --- Coarse mu sweep at small grid to see OP shape & extraction ---
mus = np.linspace(0.12, 0.19, 15)
ops = []
for mu in mus:
    sim = Lenia2D(grid_size=48, kernel_radius=15, mu_g=mu, sigma_g=0.05)
    s = sim.init_random(seed=42, density=0.5)
    for _ in range(150):
        s = sim.step(s, steps=1)
    op = float(np.mean(s))
    ops.append(op)

ops = np.array(ops)
print("\nmu:", np.round(mus,4))
print("OP:", np.round(ops,4))

# Test extractor: feed raw OP (note: it expects K_values, r_values)
beta, kc = extract_critical_exponent(mus.tolist(), ops.tolist(), window=5)
print(f"\nextract_critical_exponent -> beta={beta:.4f} (CLIP FLOOR is 0.05), k_crit={kc:.4f}")

# Also test with a KNOWN exponent to see if extractor recovers it
# Build synthetic data r = (K-0.15)^0.5 + noise
Ksyn = np.linspace(0.16, 0.25, 20)
rsyn = (Ksyn - 0.15)**0.5
b2, k2 = extract_critical_exponent(Ksyn.tolist(), rsyn.tolist(), window=8)
print(f"\nsynthetic beta=0.5 -> recovered beta={b2:.4f} (clip floor 0.05)")
# synthetic small exponent (beta=0.1) -> should hit clip
rsyn2 = (Ksyn - 0.15)**0.1
b3, k3 = extract_critical_exponent(Ksyn.tolist(), rsyn2.tolist(), window=8)
print(f"synthetic beta=0.1 -> recovered beta={b3:.4f} (clip floor 0.05)")
# synthetic beta=0.03 (below floor)
rsyn3 = (Ksyn - 0.15)**0.03
b4, k4 = extract_critical_exponent(Ksyn.tolist(), rsyn3.tolist(), window=8)
print(f"synthetic beta=0.03 -> recovered beta={b4:.4f} (should be CLIPPED to 0.05)")
