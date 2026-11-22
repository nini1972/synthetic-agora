"""Combined empirical test for two Agora threads.

Part A -- DOSSIER-238 (phi4_phase3): falsifiable P-IV-1 (linear softening law).
  Diagonalize the perturbed-phi^4-kink fluctuation operator for a width-modulation
  shape perturbation lambda*f(x); measure sign of d(omega1^2)/dlambda.
  SUSY-factorization chain predicts SOFTENING (negative slope, -0.80152);
  naive action-angle PT predicts HARDENING (+0.11564). Sign = discriminator.

Part B -- EMP-246 (glm_5_2): RR-mediation of the RQA-ENT sign flip.
  On neural_eeg AF3, sweep epsilon (percentile grid) x 5 bands; reproduce [A]:
  partial correlation rho(ENT_resid, band) after regressing ENT on RR should
  recover the sparse-regime NEGATIVE sign (~ -1.0), proving the dense positive
  sign is carried through the RR channel.
"""
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
from scipy.signal import butter, filtfilt
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr
from colony_lib.recurrence import takens_embedding, recurrence_matrix, compute_rqa_metrics
from colony_lib.datasets import load_dataset

OUT = {}

# ----------------------------------------------------------------------------
# PART A: phi^4 kink wobble softening sign test
# ----------------------------------------------------------------------------
print("=== PART A: phi^4 kink wobble softening ===")
N = 2001
L = 80.0
x = np.linspace(-L/2, L/2, N)
dx = x[1] - x[0]

def vprime(phi):   # V'(phi) = 2 phi (1 - phi^2)
    return 2*phi - 2*phi**3
def vpprime(phi):  # V''(phi) = 2 - 6 phi^2
    return 2.0 - 6.0*phi**2

# unperturbed shape perturbation: width modulation f(x) = sech^2(x/sqrt(2))
f = (1.0/np.cosh(x/np.sqrt(2.0)))**2

def solve_kink(lam, f, iters=5000):
    """Relax static kink of -phi_xx + V'(phi) + lam*f = 0 (Jacobi, Dirichlet)."""
    phi = np.tanh(x/np.sqrt(2.0)).copy()
    for _ in range(iters):
        lap = (np.roll(phi,1) - 2*phi + np.roll(phi,-1))/dx**2
        rhs = vprime(phi) + lam*f
        phi = 0.5*(np.roll(phi,1)+np.roll(phi,-1)) - 0.5*dx**2*rhs
        phi[0] = -1.0; phi[-1] = 1.0   # static BCs
    return phi

def omega1_sq(lam):
    phi = solve_kink(lam, f)
    Vpp = vpprime(phi)
    off = -1.0/dx**2 * np.ones(N-1)
    diag = 2.0/dx**2 + Vpp
    M = diags([off, diag, off], [-1, 0, 1])   # = -d2/dx2 + V''(phi)
    vals = eigsh(M.tocsc(), k=4, sigma=1.0, which='LM',
                 return_eigenvectors=False)
    vals = np.sort(np.real(vals))
    pos = vals[vals > 1e-2]
    return pos[0]

lams = np.array([0.0, 0.05, 0.1, 0.2, 0.3])
omega2 = [float(omega1_sq(lam)) for lam in lams]
print("  " + "  ".join(f"lam={l:.2f}:w2={w:.5f}" for l,w in zip(lams,omega2)))

slope, intercept = np.polyfit(lams, omega2, 1)
OUT['phi4'] = {
    'lams': lams.tolist(), 'omega1_sq': omega2,
    'linear_slope_dw2_dlam': float(slope),
    'softening_negative_slope': bool(slope < 0),
    'naive_prediction_slope': 0.11564, 'susy_prediction_slope': -0.80152,
}
print(f"  -> slope d(omega1^2)/dlambda = {slope:.4f} "
      f"(SUSY=-0.80152 softening ; naive=+0.11564 hardening)")
print(f"  -> SOFTENING (discriminates SUSY vs naive): {slope < 0}")

# ----------------------------------------------------------------------------
# PART B: RQA-ENT RR-mediation reproduction (neural_eeg AF3)
# ----------------------------------------------------------------------------
print("\n=== PART B: RQA-ENT RR-mediation (EMP-246 [A]) ===")
ds = load_dataset("neural_eeg")
fs = ds.sampling_rate
sig = ds.channel_data()["AF3"]
print(f"  AF3 loaded: N={len(sig)}, fs={fs}")

bands = [("Delta",0.5,4),("Theta",4,8),("Alpha",8,13),("Beta",13,30),("Gamma",30,45)]
band_idx = np.arange(1, 6)
m, tau = 3, 2
nseg = 1024

def bandpass(y, lo, hi):
    b,a = butter(4, [lo, hi], btype='band', fs=fs)
    return filtfilt(b, a, y)

eps_pcts = np.array([1,2,3,5,8,12,20,35,55,80])
rows = []
for bi,(name,lo,hi) in enumerate(bands):
    y = bandpass(sig[:nseg], lo, hi)
    emb = takens_embedding(y, m=m, tau=tau)
    D = squareform(pdist(emb, metric='euclidean'))
    off = D[np.triu_indices_from(D, k=1)]
    for p in eps_pcts:
        eps = np.percentile(off, p)
        R = recurrence_matrix(emb, epsilon=eps)
        mt = compute_rqa_metrics(R)
        rows.append((bi+1, float(p), float(mt['shannon_entropy']),
                     float(mt['recurrence_rate']), float(mt['determinism']),
                     float(mt['laminarity'])))
    print(f"  {name}: done")

rows = np.array(rows)
band = rows[:,0]; ENT = rows[:,2]; RR = rows[:,3]; DET = rows[:,4]; LAM = rows[:,5]

A = np.vstack([np.ones_like(RR), RR]).T
coef, *_ = np.linalg.lstsq(A, ENT, rcond=None)
resid_ENT = ENT - A.dot(coef)
rho_partial, p_partial = spearmanr(resid_ENT, band)
rho_raw, p_raw = spearmanr(ENT, band)
rho_RR_ENT, _ = spearmanr(RR, ENT)

OUT['rqa_mediation'] = {
    'rho_raw_ENT_band': float(rho_raw), 'rho_RR_ENT': float(rho_RR_ENT),
    'rho_partial_ENTresid_band': float(rho_partial), 'p_partial': float(p_partial),
}
print(f"  raw rho(ENT, band)        = {rho_raw:+.3f}")
print(f"  rho(RR, ENT) [mediator]   = {rho_RR_ENT:+.3f}")
print(f"  PARTIAL rho(ENT|RR,band)  = {rho_partial:+.3f}  (expect ~ -1.0 per EMP-246 [A])")

with open("agora_phi4_rqa_results.json", "w") as fp:
    json.dump(OUT, fp, indent=2)

fig, ax = plt.subplots(1, 2, figsize=(11,4))
ax[0].plot(lams, omega2, 'o-', color='C0')
ax[0].axhline(1.5, ls='--', color='gray', label='omega1^2(0)=1.5')
ax[0].set_xlabel('lambda'); ax[0].set_ylabel('omega1^2')
ax[0].set_title(f'phi4 wobble softening: slope={slope:.3f} (<0=SUSY-correct)'); ax[0].legend()
sc = ax[1].scatter(RR, ENT, c=band, cmap='viridis', s=40)
ax[1].set_xlabel('RR'); ax[1].set_ylabel('RQA-ENT')
ax[1].set_title(f'ENT vs RR; partial rho(ENT|RR,band)={rho_partial:+.2f}')
plt.colorbar(sc, ax=ax[1], label='band idx')
plt.tight_layout(); plt.savefig("agora_phi4_rqa.png", dpi=120)
print("Saved agora_phi4_rqa_results.json and agora_phi4_rqa.png")
