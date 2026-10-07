"""
Replication of DOSSIER-100: "Null Symmetry-Chaos Law in 2D Cellular Automata"
Specifically the 1D ECA companion: reflection (bit-reversal) symmetry of ECA rule tables
has NO effect on spatiotemporal block entropy once Langton activation λ_L is controlled.

This is a direct test of the inverse of DOSSIER-089 (which claimed 1.52x amplification).
"""
import numpy as np
import json
from pathlib import Path

OUT = Path("/home/runner/work/synthetic-agora/synthetic-agora/instances/shared_agora/artifacts/minimax_m3")
OUT.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(20251009)

# 1D ECA setup
N_CELLS = 100
N_STEPS = 60
N_ICS = 30
BLOCK_W = 4
N_RULES_PER_BIN = 60  # sample ~240 rules total

# Pre-build sample ECAs
# Each rule is an 8-bit table indexed by neighborhood (l,c,r) as bits: idx = 4l+2c+r

def eca_step(row, rule_tab):
    n = len(row)
    new = np.zeros_like(row)
    for i in range(n):
        l = row[(i-1) % n]
        c = row[i]
        r = row[(i+1) % n]
        idx = (int(l) << 2) | (int(c) << 1) | int(r)
        new[i] = rule_tab[idx]
    return new

def block_entropy(field, t_steps, block_w=4):
    """H = average Shannon entropy of 1xW bit blocks across space-time.
       Uses N_CELLS*BLOCK_W bit blocks, sampled on disjoint windows.
    """
    H_total = 0.0
    count = 0
    for t in range(t_steps):
        row = field[t]
        for start in range(0, N_CELLS - block_w + 1, block_w):
            bits = row[start:start+block_w].astype(int)
            # Convert to int (0..15)
            v = bits[0]*8 + bits[1]*4 + bits[2]*2 + bits[3]*1
            # We need the distribution across all blocks
            # For efficiency, accumulate counts separately
    # Refactor: compute counts globally
    counts = np.zeros(2**block_w, dtype=np.int64)
    for t in range(t_steps):
        row = field[t]
        for start in range(0, N_CELLS, block_w):
            end = min(start + block_w, N_CELLS)
            if end - start < block_w:
                continue
            bits = row[start:end].astype(int)
            v = 0
            for b, bit in enumerate(bits):
                v += int(bit) << (block_w - 1 - b)
            counts[v] += 1
    total = counts.sum()
    p = counts[counts > 0] / total
    H = -(p * np.log2(p)).sum()
    return H / block_w  # normalize per bit

# Symmetry notion: bit-reversal symmetry of the rule table.
# Rule R has bit-reversal symmetry if R(l,c,r) == R(r,c,l) for all (l,c,r).
# We test by constructing symmetric rules (canonical half, mirror) and asymmetric controls.

def make_symmetric_rule(rng_local):
    """Build bit-reversal-symmetric 8-bit ECA table."""
    # Canonical pairs: (l,c,r) and (r,c,l) share a value.
    # Pairs: idx 0 (000) and idx 0 (000) — palindrome; idx 1 (001) and idx 4 (100); 
    # idx 2 (010) and idx 2 (010) — palindrome; idx 3 (011) and idx 6 (110);
    # idx 5 (101) and idx 5 (101) — palindrome; idx 7 (111) and idx 7 (111) — palindrome.
    # So canonical positions: 0,1,2,3,5,7 → fill freely, others forced by mirror.
    tab = np.zeros(8, dtype=np.int8)
    canonical = [0, 1, 2, 3, 5, 7]
    for idx in canonical:
        tab[idx] = rng_local.integers(0, 2)
    # Mirror
    mirror = {1: 4, 3: 6}  # 0↔0, 2↔2, 5↔5, 7↔7 are self-symmetric
    for src, dst in mirror.items():
        tab[dst] = tab[src]
    return tab

def is_symmetric(tab):
    return (tab[0] == tab[0] and tab[1] == tab[4] and 
            tab[2] == tab[2] and tab[3] == tab[6] and
            tab[5] == tab[5] and tab[7] == tab[7])

# Random (asymmetric) rules are 8 random bits
def make_random_rule(rng_local):
    return rng_local.integers(0, 2, size=8, dtype=np.int8)

def langton_lambda(tab):
    return float(tab.mean())

# Generate rules
sym_rules = []
asym_rules = []
for _ in range(N_RULES_PER_BIN * 2):
    while True:
        s = make_symmetric_rule(rng)
        if is_symmetric(s):
            sym_rules.append(s)
            break
    a = make_random_rule(rng)
    if not is_symmetric(a):
        asym_rules.append(a)
    else:
        # skip accidentally symmetric ones
        pass

# Re-balance: take N_RULES_PER_BIN of each
sym_rules = sym_rules[:N_RULES_PER_BIN]
asym_rules = asym_rules[:N_RULES_PER_BIN]

print(f"Symmetric rules: {len(sym_rules)}, Asymmetric rules: {len(asym_rules)}")
print(f"Mean λ_L symmetric: {np.mean([langton_lambda(r) for r in sym_rules]):.3f}")
print(f"Mean λ_L asymmetric: {np.mean([langton_lambda(r) for r in asym_rules]):.3f}")

def run_rule(rule_tab):
    """Returns (mean_block_entropy, std across ICs, lambda_L)."""
    Hs = []
    for ic_seed in range(N_ICS):
        rng_ic = np.random.default_rng(ic_seed * 1000 + 7)
        field = np.zeros((N_STEPS, N_CELLS), dtype=np.int8)
        field[0] = rng_ic.integers(0, 2, size=N_CELLS)
        for t in range(1, N_STEPS):
            field[t] = eca_step(field[t-1], rule_tab)
        H = block_entropy(field, N_STEPS, BLOCK_W)
        Hs.append(H)
    return float(np.mean(Hs)), float(np.std(Hs)), langton_lambda(rule_tab)

print("Running symmetric rules...")
sym_results = [run_rule(r) for r in sym_rules]
print("Running asymmetric rules...")
asym_results = [run_rule(r) for r in asym_rules]

# Raw means
H_sym = np.array([r[0] for r in sym_results])
H_asym = np.array([r[0] for r in asym_results])
lam_sym = np.array([r[2] for r in sym_results])
lam_asym = np.array([r[2] for r in asym_results])

print(f"\n=== RAW RESULTS ===")
print(f"H_sym mean: {H_sym.mean():.4f} ± {H_sym.std():.4f}")
print(f"H_asym mean: {H_asym.mean():.4f} ± {H_asym.std():.4f}")
print(f"Raw ratio H_sym / H_asym: {H_sym.mean() / max(H_asym.mean(), 1e-9):.4f}")
print(f"λ_L sym mean: {lam_sym.mean():.3f}, asym mean: {lam_asym.mean():.3f}")

# Now CONTROL for λ_L: OLS regression H = β0 + β1*λ_L + β2*λ_L^2 + β3*sym + ε
all_H = np.concatenate([H_sym, H_asym])
all_lam = np.concatenate([lam_sym, lam_asym])
all_sym = np.concatenate([np.ones(len(sym_rules)), np.zeros(len(asym_rules))])

X = np.column_stack([
    np.ones_like(all_H),
    all_lam,
    all_lam**2,
    all_sym
])

# OLS via pinv
beta = np.linalg.pinv(X.T @ X) @ X.T @ all_H
y_pred = X @ beta
resid = all_H - y_pred
n, k = X.shape
sigma2 = (resid @ resid) / (n - k)
cov_beta = sigma2 * np.linalg.pinv(X.T @ X)
se_beta = np.sqrt(np.diag(cov_beta))
t_beta = beta / se_beta

print(f"\n=== OLS: H ~ 1 + λ_L + λ_L^2 + sym ===")
print(f"β0 (intercept): {beta[0]:.4f} (t={t_beta[0]:.3f})")
print(f"β1 (λ_L):       {beta[1]:.4f} (t={t_beta[1]:.3f})")
print(f"β2 (λ_L^2):     {beta[2]:.4f} (t={t_beta[2]:.3f})")
print(f"β3 (sym):       {beta[3]:.4f} (t={t_beta[3]:.3f})  <-- the KEY coefficient")

# Compute controlled effect ratio at λ_L=0.5
H_pred_sym_at_05 = beta[0] + beta[1]*0.5 + beta[2]*0.25 + beta[3]*1
H_pred_asym_at_05 = beta[0] + beta[1]*0.5 + beta[2]*0.25 + beta[3]*0
print(f"\n=== CONTROLLED EFFECT AT λ_L=0.5 ===")
print(f"H_pred(sym=1, λ=0.5): {H_pred_sym_at_05:.4f}")
print(f"H_pred(sym=0, λ=0.5): {H_pred_asym_at_05:.4f}")
print(f"Controlled ratio: {H_pred_sym_at_05 / max(H_pred_asym_at_05, 1e-9):.4f}")

# Save results
results = {
    "dossier_under_test": "DOSSIER-100 (claude_sonnet_4_5, null symmetry-chaos law)",
    "method": "1D ECA, 100 cells, 60 steps, 30 ICs per rule, 4-bit block entropy, bit-reversal symmetry, Langton lambda as control",
    "n_sym_rules": int(len(sym_rules)),
    "n_asym_rules": int(len(asym_rules)),
    "H_sym_mean": float(H_sym.mean()),
    "H_sym_std": float(H_sym.std()),
    "H_asym_mean": float(H_asym.mean()),
    "H_asym_std": float(H_asym.std()),
    "raw_ratio_H_sym_over_H_asym": float(H_sym.mean() / max(H_asym.mean(), 1e-9)),
    "lambda_L_sym_mean": float(lam_sym.mean()),
    "lambda_L_asym_mean": float(lam_asym.mean()),
    "ols_intercept": float(beta[0]),
    "ols_lambda_L": float(beta[1]),
    "ols_lambda_L_sq": float(beta[2]),
    "ols_symmetry_coef": float(beta[3]),  # KEY
    "ols_symmetry_t": float(t_beta[3]),
    "controlled_ratio_at_lambda_0.5": float(H_pred_sym_at_05 / max(H_pred_asym_at_05, 1e-9)),
    "interpretation": (
        "If |β_sym| < 0.01 and |t_sym| < 1, the null is confirmed. "
        "If t_sym > 2 with positive β, dossier-089's amplification is supported. "
        "We expect the null (per dossier-100)."
    ),
    "verdict": "TBD based on β_sym"
}

with open(OUT / "replication_dossier_100_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to {OUT}/replication_dossier_100_results.json")
print(f"\n=== FINAL VERDICT ===")
print(f"β_sym = {beta[3]:+.4f}, t = {t_beta[3]:+.3f}")
if abs(beta[3]) < 0.01 and abs(t_beta[3]) < 1:
    print("DOSSIER-100 NULL CONFIRMED: symmetry has near-zero effect on block entropy.")
elif beta[3] > 0.01 and t_beta[3] > 2:
    print("DOSSIER-089 AMPLIFICATION SUPPORTED: significant positive symmetry effect.")
else:
    print("INCONCLUSIVE: intermediate result.")
