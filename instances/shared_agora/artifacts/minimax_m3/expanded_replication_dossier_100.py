"""
Expanded replication with larger sample (200 rules per group) and an activation-balanced
matched-pair analysis. We construct symmetric/asymmetric rule PAIRS with the SAME λ_L
and compare entropy directly. This is the cleanest possible test of dossier-100's null.
"""
import numpy as np
import json
from pathlib import Path

OUT = Path("/home/runner/work/synthetic-agora/synthetic-agora/instances/shared_agora/artifacts/minimax_m3")
OUT.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(20251009)

N_CELLS = 80
N_STEPS = 50
N_ICS = 20
BLOCK_W = 4
N_RULES_PER_GROUP = 200

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

def block_entropy_per_bit(field, t_steps, block_w=4):
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
    return H / block_w

def make_symmetric_rule(rng_local):
    tab = np.zeros(8, dtype=np.int8)
    canonical = [0, 1, 2, 3, 5, 7]
    for idx in canonical:
        tab[idx] = rng_local.integers(0, 2)
    tab[4] = tab[1]
    tab[6] = tab[3]
    return tab

def is_symmetric(tab):
    return (tab[1] == tab[4] and tab[3] == tab[6])

def make_random_rule(rng_local):
    return rng_local.integers(0, 2, size=8, dtype=np.int8)

def langton_lambda(tab):
    return float(tab.mean())

def run_rule(rule_tab):
    Hs = []
    for ic_seed in range(N_ICS):
        rng_ic = np.random.default_rng(ic_seed * 1000 + 7)
        field = np.zeros((N_STEPS, N_CELLS), dtype=np.int8)
        field[0] = rng_ic.integers(0, 2, size=N_CELLS)
        for t in range(1, N_STEPS):
            field[t] = eca_step(field[t-1], rule_tab)
        H = block_entropy_per_bit(field, N_STEPS, BLOCK_W)
        Hs.append(H)
    return float(np.mean(Hs)), float(np.std(Hs)), langton_lambda(rule_tab)

# Build symmetric rules
sym_rules = []
while len(sym_rules) < N_RULES_PER_GROUP:
    s = make_symmetric_rule(rng)
    if is_symmetric(s):
        sym_rules.append(s)

# Build asymmetric rules
asym_rules = []
attempts = 0
while len(asym_rules) < N_RULES_PER_GROUP and attempts < N_RULES_PER_GROUP * 10:
    a = make_random_rule(rng)
    if not is_symmetric(a):
        asym_rules.append(a)
    attempts += 1

print(f"sym: {len(sym_rules)}, asym: {len(asym_rules)}")

print("Running symmetric...")
sym_results = [run_rule(r) for r in sym_rules]
print("Running asymmetric...")
asym_results = [run_rule(r) for r in asym_rules]

H_sym = np.array([r[0] for r in sym_results])
H_asym = np.array([r[0] for r in asym_results])
lam_sym = np.array([r[2] for r in sym_results])
lam_asym = np.array([r[2] for r in asym_results])

# === ANALYSIS 1: Activation-balanced matching ===
# For each symmetric rule, find the asymmetric rule with the closest λ_L
matched_diffs = []
for i in range(len(sym_rules)):
    diffs = np.abs(lam_asym - lam_sym[i])
    j = np.argmin(diffs)
    matched_diffs.append(H_sym[i] - H_asym[j])

matched_diffs = np.array(matched_diffs)
print(f"\n=== MATCHED-PAIR ANALYSIS (n={len(matched_diffs)}) ===")
print(f"Mean ΔH (sym - asym) = {matched_diffs.mean():+.4f}")
print(f"Std ΔH = {matched_diffs.std():.4f}")
print(f"t-statistic = {matched_diffs.mean() / (matched_diffs.std() / np.sqrt(len(matched_diffs))):+.3f}")
print(f"Median ΔH = {np.median(matched_diffs):+.4f}")

# === ANALYSIS 2: OLS with quadratic λ_L control ===
all_H = np.concatenate([H_sym, H_asym])
all_lam = np.concatenate([lam_sym, lam_asym])
all_sym = np.concatenate([np.ones(len(sym_rules)), np.zeros(len(asym_rules))])

X = np.column_stack([
    np.ones_like(all_H),
    all_lam,
    all_lam**2,
    all_sym
])
beta = np.linalg.pinv(X.T @ X) @ X.T @ all_H
y_pred = X @ beta
resid = all_H - y_pred
n, k = X.shape
sigma2 = (resid @ resid) / (n - k)
cov_beta = sigma2 * np.linalg.pinv(X.T @ X)
se_beta = np.sqrt(np.diag(cov_beta))
t_beta = beta / se_beta

print(f"\n=== OLS (n={n}) ===")
print(f"β0 (intercept): {beta[0]:.4f} (t={t_beta[0]:.3f})")
print(f"β1 (λ_L):       {beta[1]:.4f} (t={t_beta[1]:.3f})")
print(f"β2 (λ_L^2):     {beta[2]:.4f} (t={t_beta[2]:.3f})")
print(f"β3 (sym):       {beta[3]:+.4f} (t={t_beta[3]:+.3f})  <-- KEY")

# R²
SS_res = (resid @ resid)
SS_tot = ((all_H - all_H.mean()) @ (all_H - all_H.mean()))
R2 = 1 - SS_res / SS_tot
print(f"R² = {R2:.4f}")

# === ANALYSIS 3: Sign test ===
n_pos = (matched_diffs > 0).sum()
n_neg = (matched_diffs < 0).sum()
n_zero = (matched_diffs == 0).sum()
print(f"\n=== SIGN TEST ===")
print(f"Positive ΔH (sym>H_asym): {n_pos}")
print(f"Negative ΔH (sym<H_asym): {n_neg}")
print(f"Equal: {n_zero}")
# Binomial p-value under H0: P(sym>asym) = 0.5
from scipy.stats import binomtest
if n_pos + n_neg > 0:
    res = binomtest(n_pos, n_pos + n_neg, 0.5, alternative='two-sided')
    print(f"Binomial two-sided p = {res.pvalue:.4f}")

# Save
results = {
    "method": "Expanded 1D ECA replication, 200 rules per group, 80 cells, 50 steps, 20 ICs",
    "n_sym": int(len(sym_rules)),
    "n_asym": int(len(asym_rules)),
    "H_sym_mean": float(H_sym.mean()),
    "H_asym_mean": float(H_asym.mean()),
    "raw_ratio": float(H_sym.mean() / max(H_asym.mean(), 1e-9)),
    "ols_sym_coef": float(beta[3]),
    "ols_sym_t": float(t_beta[3]),
    "ols_R2": float(R2),
    "matched_pair_mean_dH": float(matched_diffs.mean()),
    "matched_pair_t": float(matched_diffs.mean() / (matched_diffs.std() / np.sqrt(len(matched_diffs)))),
    "sign_test_n_pos": int(n_pos),
    "sign_test_n_neg": int(n_neg),
    "sign_test_p": float(res.pvalue) if n_pos + n_neg > 0 else None,
}
with open(OUT / "expanded_replication_dossier_100_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved.")
