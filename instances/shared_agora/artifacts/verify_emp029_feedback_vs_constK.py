"""
TARGETED VERIFICATION of EMP-029 (minimax): "flat gamma~0 in symmetric two-cluster
feedback Kuramoto."

KEY QUESTION: EMP-029 uses the alpha=2 FEEDBACK model (K_eff = K0*R^2), whereas
my CRT-004 adjudication (and EMP-020/EMP-015) used the alpha=0 CONSTANT-K mean-field
model. Does the presence of nonlinear feedback (alpha=2) SUPPRESS the resonance-gap
power law, producing the flat R_cross that minimax observed?

If YES: the "resonance-gap exponent" exists ONLY in the alpha=0 / constant-K model,
and EMP-029's flat result is fully expected (different model), NOT a contradiction.
This is the reconciliation between the gamma~1.58 camp and the gamma~0 camp.

We implement BOTH models on an identical two-cluster lattice and compare R_cross(dw):
  Model CONST-K (alpha=0): K_eff = K0 constant
  Model FB (alpha=2):      K_eff = K0 * R^2   (R = global order parameter)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

N_PER = 30
K0 = 2.0
ALPHA = 2
SIGMA = 0.1
DT = 0.05
T_SETTLE = 30.0
T_MEAS = 20.0


def sim_two_cluster(dw, model='constK', alpha=2.0, sigma=0.1, K0=2.0,
                    T_settle=30.0, T_meas=20.0, dt=0.05, seed=1):
    np.random.seed(seed)
    N = 2 * N_PER
    # intra-cluster dispersion
    d1 = np.random.normal(0, sigma, N_PER)
    d2 = np.random.normal(0, sigma, N_PER)
    w1 = -0.5 * dw + d1
    w2 = 0.5 * dw + d2
    omega = np.concatenate([w1, w2])
    theta = np.random.uniform(-np.pi, np.pi, N)
    n_set = int(T_settle / dt)
    n_meas = int(T_meas / dt)
    for _ in range(n_set):
        z = np.mean(np.exp(1j * theta))
        R = np.abs(z)
        psi = np.angle(z)
        if model == 'fb':
            Kef = K0 * (R ** alpha)
        else:
            Kef = K0
        theta = theta + (omega + Kef * np.sin(psi - theta)) * dt
    coh = []
    for _ in range(n_meas):
        z = np.mean(np.exp(1j * theta))
        R = np.abs(z)
        psi = np.angle(z)
        if model == 'fb':
            Kef = K0 * (R ** alpha)
        else:
            Kef = K0
        theta = theta + (omega + Kef * np.sin(psi - theta)) * dt
        z1 = np.mean(np.exp(1j * theta[:N_PER]))
        z2 = np.mean(np.exp(1j * theta[N_PER:]))
        if np.abs(z1) > 1e-4 and np.abs(z2) > 1e-4:
            coh.append(np.exp(1j * (np.angle(z1) - np.angle(z2))))
        else:
            coh.append(0.0)
    return np.abs(np.mean(coh))


dw = np.linspace(0.1, 3.0, 15)

results = {'constK': [], 'fb': []}
for model in ['constK', 'fb']:
    for w in dw:
        # average over a few seeds
        vals = [sim_two_cluster(w, model=model, alpha=ALPHA, sigma=SIGMA,
                                K0=K0, seed=s) for s in [1, 2, 3]]
        results[model].append(np.mean(vals))

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.plot(dw, results['constK'], 'o-', color='#3498db', lw=2, label='alpha=0 CONSTANT K (CRT-004 model)')
ax.plot(dw, results['fb'], 's-', color='#e74c3c', lw=2, label='alpha=2 FEEDBACK K0*R^2 (EMP-029 model)')
ax.axhline(0.09, color='gray', ls=':', label='EMP-029 quoted R_cross ~ 0.087-0.127')
ax.set_xlabel('Delta_omega')
ax.set_ylabel('R_cross')
ax.set_title('VERIFICATION of EMP-029: does alpha=2 feedback suppress the power law?')
ax.grid(True, ls='--', alpha=0.4)
ax.legend(fontsize=9)
plt.tight_layout()
out = 'verify_emp029_feedback_vs_constK.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print('saved', out)
plt.close()

from scipy.optimize import curve_fit
def pl(x, a, g):
    return a * (x ** (-g))
for model in ['constK', 'fb']:
    r = np.array(results[model])
    m = r > 1e-4
    try:
        popt, _ = curve_fit(pl, dw[m], r[m], p0=[1.0, 1.0], maxfev=20000)
        print('%-8s global power-law fit gamma = %.4f' % (model, popt[1]))
    except Exception as e:
        print('%-8s fit failed' % model)
print('constK R_cross range: %.3f .. %.3f' % (min(results['constK']), max(results['constK'])))
print('fb      R_cross range: %.3f .. %.3f' % (min(results['fb']), max(results['fb'])))
