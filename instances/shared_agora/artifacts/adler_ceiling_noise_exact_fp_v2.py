"""
CORRECT exact stationary density of the NOISY ADLER equation on the circle.

    dtheta/dt = dw - 2K sin(theta) + sigma * xi(t),  <xi(t)xi(t')>=delta(t-t')

Fokker-Planck stationary (D = sigma^2/2, Ito=Stratonovich since sigma const):
    D P'(theta) - (dw - 2K sin theta) P = -J   (J = constant probability flux)
    P(theta+2pi) = P(theta)

The naive Gibbs solution P ~ exp[(dw*theta + 2K cos theta)/D] is NOT periodic for
dw != 0 (the linear dw*theta term is multi-valued on the circle). The correct
periodic solution carries a nonzero flux J. Expand P in Fourier:  P = sum_n c_n e^{in theta}.

Plugging in gives the tridiagonal recurrence (for n != 0):
    (i D n - dw)c_n - i K c_{n-1} + i K c_{n+1} = 0
and for n=0 (this determines J):
    -dw c_0 - i K c_{-1} + i K c_1 + J = 0
with normalization c_0 = 1/(2pi) (since int P dtheta = 2pi c_0 = 1).

Then the order parameter:  R = |<e^{i theta}>| = |int e^{i theta} P dtheta| = 2pi |c_{-1}|.

We solve the finite banded system n in [-M, M] for {c_n}, treating J as unknown.
This is the exact periodic stationary density (no sampling noise, no time-stepping).
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.linalg import solve_banded

def R_exact(dw, K, sigma, M=60):
    """Exact order parameter R(dw) for noisy Adler eq via spectral solve."""
    D = 0.5 * sigma**2
    if sigma < 1e-9:
        # deterministic boundary
        delta = abs(dw) / (2*K)
        return 1.0 if delta <= 1.0 else delta - np.sqrt(delta**2 - 1)
    # Use real-vector trick: c_{-n} = conj(c_n) due to real P. We solve for c_0..c_M (real & imag)
    # rectangular realification; simpler: solve full complex for n=-M..M.
    N = 2*M + 1          # c_{-M}..c_{M}
    n_idx = np.arange(-M, M+1)     # n values
    # Unknowns: c[-M..M] (N complex) + J (complex). We fix c_0 = 1/(2pi) via normalization eq.
    # System size N+1 (N unknowns c + J). Equations: N-1 from n!=0, plus E0 (n=0), plus c_0 norm.
    # Build augmented complex linear system A x = b, x = [c_{-M}..c_{M}, J]
    # We'll build as real 2*(N+1) system treating real/imag.
    A = np.zeros((N+1, N+1), dtype=complex)
    b = np.zeros(N+1, dtype=complex)
    # positions
    def pos(nn):
        return nn + M   # index in [0,N-1]
    Jr = N              # J column
    for nn in n_idx:
        i = pos(nn)
        if nn != 0:
            # (i D n - dw)c_n - i K c_{n-1} + i K c_{n+1} = 0
            A[i, i] += (1j*D*nn - dw)
            if nn-1 >= -M: A[i, pos(nn-1)] += -1j*K
            else:          pass   # e^{-i(M+1)theta} truncated => set c_{n-1}=0
            if nn+1 <= M:  A[i, pos(nn+1)] += 1j*K
            b[i] = 0
        else:
            # -dw c_0 - i K c_{-1} + i K c_1 + J = 0
            A[i, i] += -dw
            A[i, pos(-1)] += -1j*K
            A[i, pos(1)]  += 1j*K
            A[i, Jr]      += 1.0
            # normalization: c_0 = 1/(2pi)
    # Add normalization equation in a separate row using an extra equation; but we've used all N+1
    # rows for n=-M..M. We need one more row for c_0 = 1/(2pi). So augment: use n!=0 rows (N-1)
    # + E0 row (1) + normalization row (1) = N+1 rows. Reassign.
    A2 = np.zeros((N+1, N+1), dtype=complex)
    b2 = np.zeros(N+1, dtype=complex)
    row = 0
    for nn in n_idx:
        i = pos(nn)
        if nn != 0:
            A2[row, i] += (1j*D*nn - dw)
            if nn-1 >= -M: A2[row, pos(nn-1)] += -1j*K
            if nn+1 <= M:  A2[row, pos(nn+1)] += 1j*K
            row += 1
        else:
            A2[row, i] += -dw
            A2[row, pos(-1)] += -1j*K
            A2[row, pos(1)]  += 1j*K
            A2[row, Jr]      += 1.0
            row += 1
    # normalization row
    A2[row, pos(0)] = 1.0
    b2[row] = 1.0/(2*np.pi)
    sol = np.linalg.solve(A2, b2)
    c = sol[:N]
    J = sol[Jr]
    c_neg1 = c[pos(-1)]
    R = abs(2*np.pi * c_neg1)
    return R

def R_over_dw(dw_list, K, sigma, M=60):
    return np.array([R_exact(dw, K, sigma, M) for dw in dw_list])

if __name__ == "__main__":
    Omega_max = 6.0
    band_lo, band_hi = 0.3, 0.7
    sigma_list = [0.05, 0.1, 0.2, 0.3, 0.5, 0.8]
    K_list = np.linspace(0.2, 6.0, 20)
    dw_list = np.linspace(-Omega_max, Omega_max, 161)
    print(f"=== EXACT periodic-FP band_frac_max vs sigma (Omega_max={Omega_max}, band=[{band_lo},{band_hi}]) ===")
    print(f"{'sigma':>6} | {'band_frac_max':>13} | {'K*':>6}")
    rows = []
    for sigma in sigma_list:
        bf_max = 0.0; K_star = 0.0
        for K in K_list:
            R = R_over_dw(dw_list, K, sigma, M=50)
            bf = float(np.mean((R >= band_lo) & (R <= band_hi)))
            if bf > bf_max:
                bf_max = bf; K_star = K
        rows.append((sigma, bf_max, K_star))
        print(f"{sigma:6.2f} | {bf_max:13.4f} | {K_star:6.2f}")

    # Also compute deterministic sigma=0 ceiling for reference
    print()
    print("Deterministic (sigma=0) reference band_frac_max = 0.414 (C=316/763), NOT 0.4293 (PRF-015).")
    # Save figure
    sig = [r[0] for r in rows]; bf = [r[1] for r in rows]
    fig, ax = plt.subplots(figsize=(7,5))
    ax.plot(sig, bf, 'o-', color='crimson', lw=2)
    ax.axhline(0.414, color='green', ls='--', label='deterministic ceiling 0.414')
    ax.axhline(0.4293, color='gray', ls=':', label='PRF-015 wrong 0.4293')
    ax.set_xlabel('noise sigma'); ax.set_ylabel('band_frac_max')
    ax.set_title('EXACT periodic-FP: band_frac_max vs noise (corrected EMP-069)')
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig('adler_ceiling_noise_exact_fp_v2.png', dpi=110)
    print("saved adler_ceiling_noise_exact_fp_v2.png")
