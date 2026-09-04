"""Independent second-lineage verification of Kuramoto criticality (PRF-007/EMP-034).

For a Lorentzian (Cauchy) frequency distribution g(omega)= (D/pi)/(omega^2+D^2),
Ott-Antonsen predicts continuous onset at Kc = 2*D, with order parameter
r = sqrt(1 - Kc/K) for K>Kc  =>  r^2 = 1 - Kc/K  (linear in 1/K near onset),
so r ~ (K-Kc)^{1/2} (mean-field exponent beta=1/2).
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def simulate(K, D=1.0, N=800, dt=0.05, T=120.0, seed=1):
    rng = np.random.default_rng(seed)
    omega = rng.standard_cauchy(N) * D
    theta = rng.uniform(-np.pi, np.pi, N)
    n = int(T / dt)
    sinT = np.sin(theta)
    cosT = np.cos(theta)
    for _ in range(n):
        z = sinT.sum() + 1j * cosT.sum()
        coup = (K / N) * np.imag(z * np.exp(-1j * theta))
        theta = theta + dt * (omega + coup)
        sinT = np.sin(theta)
        cosT = np.cos(theta)
    z = sinT.sum() + 1j * cosT.sum()
    return np.abs(z) / N


def main():
    Ks = np.array([1.0, 1.4, 1.7, 1.9, 2.0, 2.1, 2.3, 2.6, 3.0, 4.0])
    Rs = np.array([np.mean([simulate(K, seed=s) for s in range(3)]) for K in Ks])
    # fit r^2 = 1 - Kc/K for K>Kc
    mask = Ks >= 2.0
    invK = 1.0 / Ks[mask]
    r2 = Rs[mask] ** 2
    A = np.vstack([invK, np.ones_like(invK)]).T
    slope, intercept = np.linalg.lstsq(A, r2, rcond=None)[0]
    Kc_fit = -slope  # since r^2 = 1 - Kc/K  => slope = -Kc, intercept=1
    print(f"Kc_fit = {Kc_fit:.3f}  (theory 2.0 for Lorentzian D=1)")
    print(f"R at K=1.0,1.7,2.0,2.3,3.0,4.0 = "
          f"{np.round(Rs[[0,2,4,6,8,9]],3)}")
    plt.figure(figsize=(7, 5))
    plt.plot(Ks, Rs, 'o-', color='darkgreen', label='measured R(K)')
    Kf = np.linspace(2.0, 4.5, 50)
    plt.plot(Kf, np.sqrt(np.clip(1 - Kc_fit / Kf, 0, None)), '--',
             color='gray', label=f'fit r=sqrt(1-Kc/K), Kc={Kc_fit:.2f}')
    plt.axvline(2.0, color='red', lw=1, ls=':', label='theory Kc=2.0')
    plt.xlabel('K'); plt.ylabel('R (order parameter)')
    plt.title('Kuramoto Criticality: Independent Replication (Hunyuan/Tencent)')
    plt.legend(); plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('kuramoto_crit_check.png', dpi=130)
    print('SAVED kuramoto_crit_check.png')


if __name__ == '__main__':
    main()
