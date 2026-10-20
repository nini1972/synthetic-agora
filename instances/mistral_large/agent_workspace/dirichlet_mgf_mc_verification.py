#!/usr/bin/env python3
"""
Independent Monte Carlo Verification of Dirichlet MGF (HYP-124).
Tests 3 parameter regimes against the series formula.
"""

import numpy as np
import math
from scipy.special import gamma, poch
from numpy.random import dirichlet

# Dirichlet MGF Series Formula (HYP-124)
def dirichlet_mgf_series(alpha, lambd, N_max=80):
    from itertools import product
    from scipy.special import poch
    K = len(alpha)
    total = 0.0
    for n in product(range(N_max), repeat=K):
        n_sum = sum(n)
        if n_sum >= N_max:
            continue
        numerator = (-1)**n_sum
        for i in range(K):
            numerator *= poch(alpha[i], n[i]) * (lambd[i]**n[i])
        denominator = np.prod([math.factorial(ni) for ni in n]) * poch(sum(alpha), n_sum)
        total += numerator / denominator
    return total

# Monte Carlo Simulator
def dirichlet_mgf_mc(alpha, lambd, samples=50_000_000):
    X = dirichlet(alpha, size=samples)
    mgf = np.exp(-np.dot(X, lambd))
    return np.mean(mgf), np.std(mgf) / np.sqrt(samples)

# Test Cases
test_cases = [
    {
        "alpha": [0.5, 0.5, 0.5],
        "lambd": [2.0, 1.0, 0.5],
        "label": "Small α (Uniform)"
    },
    {
        "alpha": [5.0, 2.0, 0.5],
        "lambd": [0.3, 0.8, 1.2],
        "label": "Large α (Skewed)"
    },
    {
        "alpha": [2.0, 3.0, 1.5],
        "lambd": [0.5, 1.0, 0.7],
        "label": "Medium α (Anchor Case)"
    }
]

# Report
with open('REPORT_dirichlet_mgf_verification.md', 'w') as f:
    f.write("# Dirichlet MGF Verification (HYP-124)\n\n")
    f.write("## Test Cases\n")
    for case in test_cases:
        f.write(f"- **{case['label']}**: α={case['alpha']}, λ={case['lambd']}\n")
    
    f.write("\n## Results\n")
    f.write("| Case | MC Mean | MC SE | Series Value | |Diff| |\n")
    f.write("|------|---------|--------|--------------|--------|\n")
    
    for case in test_cases:
        mc_mean, mc_se = dirichlet_mgf_mc(case["alpha"], case["lambd"])
        series_value = dirichlet_mgf_series(case["alpha"], case["lambd"])
        diff = abs(mc_mean - series_value)
        f.write(f"| {case['label']} | {mc_mean:.6f} | {mc_se:.6f} | {series_value:.6f} | {diff:.6f} |\n")
        
    f.write("\n## Verdict\n")
    f.write("- **HYP-124**: **Endorsed** if all |Diff| < 3σ.\n")
    f.write("- **Refuted** otherwise.\n")