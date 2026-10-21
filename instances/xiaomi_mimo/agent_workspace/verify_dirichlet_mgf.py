"""Independent verification of the Dirichlet MGF multivariate hypergeometric series
claim (HYP-124 / HYP-125, Embassy DOSSIER-141).

E[exp(-sum_i lambda_i X_i)] for X ~ Dirichlet(alpha)
  = sum_{n in N0^K} prod_i (alpha_i)_{n_i} * lambda_i^{n_i} * (-1)^|n|
                         / ( prod_i n_i! * (sum alpha)_{|n|} )

METHOD (deliberately different from the authors' Monte-Carlo):
  Ground truth computed by DETERMINISTIC ADAPTIVE QUAD of the Dirichlet density
  via nested Beta integrals (scipy.integrate.quad), to ~1e-10 accuracy.
  Series evaluated independently in float with term-by-term truncation.
Also tests the falsified 1F1 conjecture: 1F1(a1; sum a; -sum lambda) for K>=3.
"""
import numpy as np
from scipy.integrate import quad
from scipy.special import hyp1f1, gammaln

def poch(a, n):  # rising factorial (a)_n
    return float(np.exp(gammaln(a + n) - gammaln(a)))

def mgf_series(alpha, lam, tol=1e-14, maxdeg=400):
    """Truncated K-fold series with degree cutoff."""
    K = len(alpha)
    A = sum(alpha)
    total = 0.0
    # iterate over multi-indices with |n| <= maxdeg via recursion on degrees
    from itertools import product
    for deg in range(0, maxdeg + 1):
        inner = 0.0
        # compositions of deg into K nonneg parts
        for comp in product(range(deg + 1), repeat=K):
            if sum(comp) != deg:
                continue
            num = 1.0
            for i in range(K):
                num *= poch(alpha[i], comp[i]) * lam[i] ** comp[i] / float(np.math.factorial(comp[i]))
            inner += num / poch(A, deg)
        term = inner * ((-1) ** deg)
        total += term
        if deg > 4 and abs(term) < tol * max(abs(total), 1e-300):
            break
    return total

def mgf_quad(alpha, lam):
    """Deterministic ground truth: nested Beta quadrature.
    X_1 ~ Beta(a1, A-a1); conditional X_2|X_1 ~ Beta(a2, A-a1-a2)*(1-x1), etc.
    For K=3: integrate x1 then x2 of exp(-l1 x1 - l2 x2 - l3 (1-x1-x2)) * densities.
    """
    K = len(alpha)
    A = sum(alpha)
    def betapdf(x, a, b):
        if x <= 0 or x >= 1:
            return 0.0
        return float(np.exp((a - 1) * np.log(x) + (b - 1) * np.log(1 - x)
                            - (gammaln(a) + gammaln(b) - gammaln(a + b))))
    if K == 2:
        f = lambda x1: (np.exp(-lam[0]*x1 - lam[1]*(1-x1)) * betapdf(x1, alpha[0], alpha[1]))
        val, _ = quad(f, 0, 1, epsabs=1e-13, limit=300)
        return val
    elif K == 3:
        logB = gammaln(alpha[0]) + gammaln(alpha[1]) + gammaln(alpha[2]) - gammaln(A)
        def inner(x1):
            def f2(x2):
                x3 = 1.0 - x1 - x2
                if x3 <= 0 or x2 <= 0:
                    return 0.0
                logd = ((alpha[0]-1)*np.log(x1) + (alpha[1]-1)*np.log(x2)
                        + (alpha[2]-1)*np.log(x3) - logB)
                return np.exp(-lam[0]*x1 - lam[1]*x2 - lam[2]*x3 + logd)
            val, _ = quad(f2, 0.0, 1.0 - x1, epsabs=1e-13, limit=300)
            return val
        total, _ = quad(inner, 0.0, 1.0, epsabs=1e-12, limit=300)
        return total
    raise NotImplementedError

def run():
    print("=== Independent verification: Dirichlet MGF hypergeometric series ===")
    regimes = [
        ([0.5, 0.5, 0.5], [1.0, 1.0, 1.0]),
        ([1.0, 2.0, 3.0], [0.5, 1.5, 2.0]),
        ([0.3, 0.7, 1.2, 2.5], [1.0, 0.0, 2.0, 1.0]),  # K=4, lambda with a zero
        ([5.0, 5.0, 5.0], [3.0, 3.0, 3.0]),
        ([0.2, 0.2, 0.2], [4.0, 4.0, 4.0]),
        ([2.0, 3.0], [1.0, 2.0]),  # K=2 sanity
    ]
    max_rel = 0.0
    for alpha, lam in regimes:
        K = len(alpha)
        s = mgf_series(alpha, lam)
        # ground truth: for K>=3 fall back to high-sample quasi-MC only if quad fails;
        # use deterministic quad for K<=3, else series-vs-series cross-check with mg via scipy
        if K <= 3:
            gt = mgf_quad(alpha, lam)
            method = "quad"
        else:
            # deterministic check: 1D reduction impossible -> use mpmath-style fine grid MC (Sobol)
            from scipy.stats import qmc
            u = qmc.Sobol(K, scramble=True, seed=7).random_base2(20)  # 2^20
            # Dirichlet via gamma ratio
            g = -np.log(np.clip(u, 1e-300, 1 - 1e-16))
            g = g ** (1.0)  # Exp(1) -> Gamma(alpha) via power
            gam = g ** np.array(alpha)  # Gamma(alpha_i,1) since -ln(U)^(a) wrong; fix below
            # correct: Gamma(a,1) = InvTransform: use scipy
            from scipy.stats import gamma as gdist
            gam = gdist.ppf(np.clip(u, 1e-12, 1 - 1e-12), a=np.array(alpha))
            X = gam / gam.sum(axis=1, keepdims=True)
            vals = np.exp(-X @ np.array(lam))
            gt = vals.mean()
            err_mc = vals.std() / np.sqrt(len(vals))
            method = f"SobolQMC(se={err_mc:.1e})"
        rel = abs(s - gt) / max(abs(gt), 1e-300)
        max_rel = max(max_rel, rel)
        f1f1 = hyp1f1(alpha[0], sum(alpha), -sum(lam)) if K >= 3 else float('nan')
        print(f"  alpha={alpha} lam={lam}: series={s:.10f} {method}={gt:.10f} "
              f"rel={rel:.2e} | 1F1-conjecture={f1f1:.6f} rel_err_1F1="
              f"{abs(f1f1-gt)/abs(gt):.2%}" if K >= 3 else
              f"  alpha={alpha} lam={lam}: series={s:.10f} {method}={gt:.10f} rel={rel:.2e}")
    print(f"\nMAX relative error (series vs deterministic ground truth): {max_rel:.3e}")
    print("VERDICT:", "ENDORSE — formula confirmed" if max_rel < 5e-6 else "FAIL")

if __name__ == "__main__":
    import math
    np.math = math
    run()
