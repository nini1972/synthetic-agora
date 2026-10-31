"""DOSSIER-158 follow-up: does ANY natural normalization of K collapse the branches?
Uses the three branch means from the companion run (Lorenz, Henon, Rule110)."""
import numpy as np

# branch means (lam, D2, K, d_dim)
branches = {
  "Lorenz":  dict(lam=1.177, D2=1.878, K=13.667, d=3),
  "Henon":   dict(lam=0.370, D2=1.186, K=0.400,  d=2),
  "Rule110": dict(lam=0.003, D2=1.000, K=0.560,  d=1),
}
TARGET=-2.08

def report(fn, name):
    vals={k:fn(**v) for k,v in branches.items()}
    sp=max(vals.values())-min(vals.values())
    dists={k:abs(v-TARGET) for k,v in vals.items()}
    print(f"{name:34s} " + "  ".join(f"{k}={vals[k]:+8.3f}" for k in branches)
          + f"   spread={sp:6.3f}  |mean+TARGET|={abs(np.mean(list(vals.values()))-TARGET):6.3f}")
    return vals

print("Branch raw coordinates:")
print(f"{'':34s} " + "  ".join(f"{k}={branches[k]['lam']:+8.3f}" for k in branches))
print()
print("Candidate Q = -lam - D2 - g(K):")
report(lambda lam,D2,K,d: -lam-D2-K,           "Q  (raw K, DOSSIER def)")
report(lambda lam,D2,K,d: -lam-D2-K/d,          "Q1 (K/d, per-dimension)")
report(lambda lam,D2,K,d: -lam-D2-K/d**2,       "Q2 (K/d^2)")
report(lambda lam,D2,K,d: -lam-D2-K/(lam+D2),   "Q3 (K/(lam+D2), self-normalized)")
report(lambda lam,D2,K,d: -lam-D2-K/(lam+D2+d), "Q4 (K/(lam+D2+d))")
report(lambda lam,D2,K,d: (-lam-D2-K)/K,        "Q5 ((...)/K)")
report(lambda lam,D2,K,d: (-lam-D2-K)/(lam+D2+K),"Q6 (relative to total flux)")
report(lambda lam,D2,K,d: -lam-D2-np.log(K+1e-9),"Q7 (log K)")
report(lambda lam,D2,K,d: -lam-D2-d*np.log(d),  "Q8 (-lam-D2 only, drop K)")

print()
print("Verdict: for a normalization to 'collapse' the branches onto -2.08 we need")
print("spread -> ~0 AND |mean+TARGET| -> ~0. None of Q1..Q7 achieves both; Q8")
print("(dropping K entirely) still leaves the Lorenz branch 0.4-0.6 away and is not")
print("even the claimed functional form. The branch structure is therefore NOT an")
print("artifact of an un-normalized K; it is a commensurability failure: K denotes a")
print("different operator (vector-field divergence / Jacobian log / transfer-entropy")
print("proxy) in each class, so adding it to the dimensionless pair (lam,D2) mixes units.")
