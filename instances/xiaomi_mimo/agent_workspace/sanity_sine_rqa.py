"""Sanity check: hand-rolled RQA vs colony_lib on a clean sine + noise.
A smooth quasi-periodic signal must give high DET at matched RR=5%."""
import numpy as np
from scipy.spatial.distance import cdist
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics

rng = np.random.default_rng(0)
t = np.arange(3000)
x = np.sin(2 * np.pi * t / 64.0) + 0.1 * rng.standard_normal(len(t))


def mine(x, m=3, tau=2, rr=0.05):
    idx = np.arange(m) * tau
    N = len(x) - (m - 1) * tau
    emb = np.stack([x[i:i + N] for i in idx], axis=1)
    D = cdist(emb, emb, metric="chebyshev")
    iu = np.triu_indices(len(D), 1)
    eps = float(np.quantile(D[iu], rr))
    R = D <= eps
    n = len(R)
    np.fill_diagonal(R, False)
    mask = ~np.eye(n, dtype=bool)
    RR = R[mask].mean()
    cont = np.zeros_like(R)
    cont[:-1, :-1] |= R[:-1, :-1] & R[1:, 1:]
    cont[1:, 1:] |= R[:-1, :-1] & R[1:, 1:]
    DET = (R & cont)[mask].mean()
    vcont = np.zeros_like(R)
    vcont[:-1] |= R[:-1] & R[1:]
    vcont[1:] |= R[:-1] & R[1:]
    LAM = (R & vcont)[mask].mean()
    return dict(eps=eps, RR=RR, DET=DET, LAM=LAM)


def colony(x, m=3, tau=2, rr=0.05):
    emb = takens_embedding(x, m=m, tau=tau)
    n = len(emb)
    D = cdist(emb, emb, metric="chebyshev")
    iu = np.triu_indices(n, 1)
    eps = float(np.quantile(D[iu], rr))
    R = recurrence_matrix(emb, epsilon=eps)
    mm = compute_rqa_metrics(R)
    return dict(eps=eps, RR=mm["RR"], DET=mm["DET"], LAM=mm["LAM"], ENT=mm["ENT"],
                raw_keys={k: mm[k] for k in ("L", "Lmax", "N", "recurrence_rate")})


print("mine   :", mine(x))
print("colony :", colony(x))