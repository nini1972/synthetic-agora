"""Generate comprehensive comparison figure: my independent periodic-FP (continued fraction)
verification vs EMP-082 reference vs EMP-069 (invalid Gibbs) for the noisy Adler ceiling."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def R_continued(dw, K, D, NMAX=2000):
    dw = np.asarray(dw, dtype=np.complex128)
    K = np.asarray(K, dtype=np.complex128)
    D = np.asarray(D, dtype=np.complex128)
    dw, K, D = np.broadcast_arrays(dw, K, D)
    x = np.zeros(dw.shape, dtype=np.complex128)
    for n in range(NMAX, 0, -1):
        a_n = (dw - 1j * D * n) / (1j * K)
        x = 1.0 / (x - a_n)
    return np.abs(x)


def band_frac(sigma, Omega_max=6.0, band=(0.3, 0.7), Kgrid=None):
    D = sigma**2 / 2.0
    if Kgrid is None:
        Kgrid = np.linspace(0.5, 4.0, 40)
    dW = np.linspace(-Omega_max, Omega_max, 201)
    best = 0.0
    bestK = None
    for K in Kgrid:
        Rvals = R_continued(dW, K, D)
        bf = np.mean((Rvals >= band[0]) & (Rvals <= band[1]))
        if bf > best:
            best = bf
            bestK = K
    return best, bestK


if __name__ == "__main__":
    sigmas = [0.05, 0.10, 0.20, 0.30, 0.50, 0.80]
    my_vals = []
    for sig in sigmas:
        bf, bK = band_frac(sig)
        my_vals.append(bf)
        print(f"  sigma={sig:.2f} -> my CF band_frac_max={bf:.4f} (K*={bK:.2f})")

    # Reference datasets
    ref_082 = {0.00:0.4145, 0.05:0.4145, 0.10:0.4145, 0.20:0.4145, 0.30:0.4170, 0.50:0.4295, 0.80:0.4694}
    ref_069 = {0.00:0.400, 0.05:0.0025, 0.10:0.0025, 0.20:0.0100, 0.30:0.0200, 0.50:0.0750, 0.80:0.2450}

    fig, ax = plt.subplots(1, 1, figsize=(8, 5.5))
    ax.plot(sigmas, my_vals, 'o-', color='tab:blue', lw=2, label='MY independent periodic-FP (continued fraction)')
    ax.plot(list(ref_082.keys()), list(ref_082.values()), 's--', color='tab:green', label='EMP-082 (corrected periodic FP)')
    ax.plot(list(ref_069.keys()), list(ref_069.values()), '^:', color='tab:red', label='EMP-069 (invalid Gibbs form)')
    ax.set_xlabel('noise intensity sigma')
    ax.set_ylabel('band_frac_max')
    ax.set_title('Noisy Adler ceiling: independent replication confirms\nMONOTONE noise-benefit; refutes collapse-then-recover')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.02, 0.55)
    plt.tight_layout()
    plt.savefig('adler_ceiling_replication_summary.png', dpi=130)
    print("\nSaved adler_ceiling_replication_summary.png")
