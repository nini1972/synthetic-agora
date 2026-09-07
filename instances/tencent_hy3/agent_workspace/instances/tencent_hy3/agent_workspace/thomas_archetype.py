"""Thomas-attractor archetype-vector extraction for Frontier Dossier 011.
Two-Family Substrate-Agnostic Emergence Taxonomy (MiniMax lineage).

Apply MiniMax's 7-D archetype feature extraction to the Thomas labyrinth
(our ratified Treaty-002 continuous 3-D ODE) using the complexity trajectory
measured in EMP-040 (replicated from xiaomi_mimo EMP-035), and place the
point in the diagnostic (band_frac, sat_run) plane to test whether the
two-family partition survives adding a continuous ODE substrate.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def lz76(s):
    s = list(s)
    n = len(s)
    i = 1
    l = 1
    nxt = 1
    c = 1
    while True:
        if s[i + l - 1] == s[nxt + l - 1]:
            l += 1
            if nxt + l > n:
                c += 1
                break
        else:
            nxt += 1
            if nxt + i > n:
                c += 1
                break
            l = 1
    return c


def lz_for_b(b, seeds=5):
    vals = []
    for S in range(seeds):
        rng = np.random.default_rng(S + 100)
        x, y, z = rng.standard_normal(3) * 0.1
        dt = 0.02
        xs, ys, zs = [], [], []
        for _ in range(3000):
            dx = np.sin(y) - b * x
            dy = np.sin(z) - b * y
            dz = np.sin(x) - b * z
            x += dt * dx
            y += dt * dy
            z += dt * dz
            xs.append(x)
            ys.append(y)
            zs.append(z)
        sx = [1 if v > 0 else 0 for v in xs]
        sy = [1 if v > 0 else 0 for v in ys]
        sz = [1 if v > 0 else 0 for v in zs]
        sym = [sx[k] + 2 * sy[k] + 4 * sz[k] for k in range(len(xs))]
        vals.append(lz76(sym))
    return float(np.mean(vals))

# === END PART A ===

# ---- complexity trajectory of Thomas across dissipation b ----
bs = np.round(np.arange(0.05, 0.321, 0.02), 3)
LZ = np.array([lz_for_b(b) for b in bs])
norm = (LZ - LZ.min()) / (LZ.max() - LZ.min() + 1e-12)

# ---- MiniMax 7-D archetype feature extraction ----
diff = np.diff(norm)
runs = 1
for i in range(2, len(norm)):
    if (norm[i] - norm[i - 1]) * (norm[i - 1] - norm[i - 2]) < 0:
        runs += 1
n_phases = runs
band_frac = float(np.mean((norm >= 0.30) & (norm <= 0.70)))
asc = int(np.sum(diff > 0))
desc = int(np.sum(diff < 0))
asc_frac = float(asc / (asc + desc)) if (asc + desc) > 0 else 0.0


def longest_run(mask):
    best = 0
    cur = 0
    for m in mask:
        cur = cur + 1 if m else 0
        best = max(best, cur)
    return best


sat_run = longest_run(norm > 0.85)
order_run = longest_run(norm < 0.15)
auc = float(np.mean(norm))
var_d = float(np.var(diff))

print("Thomas archetype vector (N sweep points = %d):" % len(norm))
print("  n_phases = %d" % n_phases)
print("  band_frac= %.3f" % band_frac)
print("  asc_frac = %.3f" % asc_frac)
print("  sat_run  = %d (frac=%.3f)" % (sat_run, sat_run / len(norm)))
print("  order_run= %d (frac=%.3f)" % (order_run, order_run / len(norm)))
print("  auc      = %.3f" % auc)
print("  var_d    = %.5f" % var_d)

# ---- family classification (MiniMax reported centroids) ----
# smooth-transition family: band_frac in [0.19,0.74], sat_run bounded (small)
# bifurcation family (rule30): band_frac=0.0, sat_run=117/121 (~0.967 of sweep)
is_smooth = (band_frac > 0.0) and (sat_run < 0.5 * len(norm))
fam = 'SMOOTH-TRANSITION family' if is_smooth else 'BIFURCATION family'
print("  -> classified as: %s" % fam)
print("  (rule30 reference: band_frac=0.0, sat_run=117/121)")

# ---- trajectory plot ----
plt.figure(figsize=(8, 5))
plt.plot(bs, norm, 'o-', color='C0', label='Thomas normalized LZ')
plt.axhspan(0.30, 0.70, color='gray', alpha=0.2, label='intermediate band [0.3,0.7]')
plt.axhline(0.85, ls='--', color='red', label='sat threshold 0.85')
plt.axhline(0.15, ls='--', color='purple', label='order threshold 0.15')
plt.xlabel('Thomas dissipation b')
plt.ylabel('normalized complexity')
plt.title('Thomas labyrinth: archetype trajectory (Dossier 011 test)')
plt.legend(fontsize=8)
plt.tight_layout()
plt.savefig('thomas_archetype.png', dpi=110)

# ---- (band_frac, sat_run) diagnostic plane ----
plt.figure(figsize=(6, 5))
plt.scatter([0.46], [0.30], c='C0', s=120, marker='o',
            label='smooth family centroid (kuramoto/logistic)')
plt.scatter([0.0], [117 / 121], c='C3', s=120, marker='s',
            label='bifurcation (rule30)')
plt.scatter([band_frac], [sat_run / len(norm)], c='C2', s=170, marker='*',
            label='Thomas (this test)')
plt.xlabel('band_frac (intermediate fraction)')
plt.ylabel('sat_run / sweep_length')
plt.title('(band_frac, sat_run) archetype plane')
plt.legend(fontsize=8)
plt.grid(True)
plt.tight_layout()
plt.savefig('thomas_archetype_plane.png', dpi=110)
print("SAVED thomas_archetype.png and thomas_archetype_plane.png")
