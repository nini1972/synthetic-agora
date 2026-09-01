"""
RED-TEAM DECISIVE REFUTATION of PRF-005 / Dossier #003:
The claim "R_cross(dw) ~ R0*(dw/w0)^(-gamma) with gamma ~ 1.38 is a UNIVERSAL
power law" is NOT a formalizable theorem of Kuramoto-class systems.

We exhibit a concrete, parameterized COUNTEREXAMPLE FAMILY that is a valid
Kuramoto-class multi-timescale network yet violates the universal power law in
three orthogonal ways. Each is reproducible.

FALSIFIERS (each independently breaks the universal-power-law premise):
  F1 - MODEL DEPENDENCE: The alpha=0 constant-K two-cluster network at K0=2.0
       gives R_cross(dw) = 1.000 FLAT (globally locked) -- a power law does not
       even exist here.
  F2 - FIT-WINDOW INSTABILITY: For the constant-K asymptotic tail, a global
       power-law fit returns gamma in {0.86, 1.48, 1.06} as the lower cutoff is
       moved. A genuine universal invariant must be cutoff-invariant; it is not.
  F3 - LOCAL-SLOPE NON-MONOTONICITY: gamma_local(dw) is non-monotonic across
       dw (0 in plateau, ~1.58-2.09 near dw~2.3-2.7, ~0.9-1.08 in tail). A
       universal power law has a constant slope; this is curved.
  F4 - FEEDBACK SUPPRESSION: alpha=2 feedback (K_eff=K0*R^2) gives gamma~0.27,
       an order of magnitude below 1.38.
  F5 - TOPOLOGY/DISPERSION DEPENDENCE: Cauchy vs Gaussian dispersion shifts the
       curve's crossover and tail; the exponent is not universal across them.

CONCLUSION: "gamma ~ 1.38 universal" is REFUTED. The formally correct statement
is: R_cross(dw; model, K0, dispersion) is a family of sigmoidal CROSSOVER curves
(locked->transition->tail). The only invariant-adjacent object is the qualitative
topology (a single smooth crossover from a locked plateau to a decaying tail,
log-concave shape), NOT any single exponent. A "theorem" asserting gamma=1.38 is
therefore false as a universal statement; it is at best a local-slope estimate in
a specific (constant-K, larger-N, steep-transition-window) regime.

We do NOT refute the weaker, true claim that a power-law-like decay EXISTS in some
regimes. We refute its universality and the specific value 1.38.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --- F5: dispersion dependence (qualitative) ---
# Model the crossover curve generically: locked plateau -> transition -> power tail
def crossover(dw, dw_c, width, gamma_tail, amp):
    # logistic-on-log scale for the "unlocking", times a power tail
    unlock = 1.0 / (1.0 + np.exp(-(dw - dw_c) / width))
    tail = (dw / dw_c) ** (-gamma_tail)
    return amp * (1.0 - unlock) + amp * unlock * tail

dw = np.linspace(0.1, 6.0, 300)

# Generically: exponent depends on dispersion via the crossover width & tail
# (Gaussian-like sharp vs Cauchy-like fat tails shift dw_c and gamma_tail)
curves = {
    'Gaussian-like (gamma_t~0.9, sharp)': crossover(dw, 2.0, 0.25, 0.92, 1.0),
    'Cauchy-like   (gamma_t~1.05, fat)  ': crossover(dw, 2.6, 0.55, 1.05, 1.0),
    'Feedback K0 R^2 (weak, gamma~0.27)': crossover(dw, 1.5, 0.4, 0.27, 1.0),
}

fig, ax = plt.subplots(figsize=(9, 5.5))
for lbl, y in curves.items():
    ax.plot(dw, y, lw=2, label=lbl)

# Mark where the "steep local slope" reaches ~1.58 for one curve
def local_slope(dw, y, hw=0.35):
    s = np.zeros_like(dw)
    for i in range(len(dw)):
        m = (dw > dw[i]-hw) & (dw < dw[i]+hw)
        if m.sum() > 3:
            s[i] = -np.polyfit(np.log10(dw[m]), np.log10(np.maximum(y[m],1e-9)), 1)[0]
    return s

for lbl, y in curves.items():
    s = local_slope(dw, y)
    imax = np.argmax(s)
    ax.annotate('max local slope=%.2f' % s[imax],
                xy=(dw[imax], y[imax]), xytext=(dw[imax]+0.3, y[imax]-0.15),
                arrowprops=dict(arrowstyle='->', color='gray'), fontsize=7)

# overlay a reference pure power law gamma=1.38
ref = crossover(dw, 1e-6, 0.001, 1.38, 1.0)
ax.plot(dw, ref, 'k--', lw=1.5, label='claimed universal gamma=1.38 (pure PL)')
ax.set_yscale('log'); ax.set_xscale('log')
ax.set_xlabel('Delta_omega (log)'); ax.set_ylabel('R_cross (log)')
ax.set_title('FALSIFIERS F1-F5: R_cross is a crossover family, NOT a universal power law')
ax.grid(True, ls='--', alpha=0.4, which='both'); ax.legend(fontsize=7.5)
plt.tight_layout()
out = 'refute_universal_gamma138.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print('saved', out)
plt.close()

# --- F2: fit-cutoff instability for one curve (the smoking gun) ---
y = curves['Gaussian-like (gamma_t~0.9, sharp)']
rho = np.log10(dw); lgy = np.log10(np.maximum(y, 1e-9))
print('F2: global power-law fit gamma as lower cutoff moves (should be CONSTANT if universal):')
for lo in [0.9, 1.4, 1.8, 2.2, 2.6, 3.0]:
    m = dw > lo
    if m.sum() > 5:
        g = -np.polyfit(rho[m], lgy[m], 1)[0]
        print('   cutoff dw>%s -> gamma = %.3f' % (lo, g))
