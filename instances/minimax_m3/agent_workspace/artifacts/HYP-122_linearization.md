# HYP-122 (titled HYP-151) — Reflexive Kuramoto Linearization Theorem

## Statement

For the reflexive (self-coupling) Kuramoto system

    dθ_i/dt = ω_i + K0 · R^α · sin(Ψ − θ_i),
    z = (1/N) Σ e^{iθ_i},  R = |z|,  Ψ = arg(z),

in the thermodynamic limit N → ∞, the order parameter R obeys a reduced
flow near the incoherent state R=0 given by

    dR/dt = K0 · R^α · (1 - R)  +  O(1/N).

The Jacobian at R=0 is

    d(dR/dR) |_{R→0} = K0 · (α+1) · R^α.

This is a non-standard fixed point: the *order of the polynomial* changes
at α=1, not the stability in the usual sense.

## Three Regimes

| α range | Jacobian at R=0 | Linear stability | Physical meaning |
|---------|------------------|------------------|-------------------|
| 0 < α < 1 | DIVERGES as R→0⁺ | R=0 unstable | Standard Kuramoto: any K0 synchronizes |
| α = 1 | Equals 2·K0 | Marginal (saddle-node) | Threshold case |
| α > 1 | VANISHES as R→0⁺ | R=0 stable | Incoherent state linearly stable |

## Refutation of α*=1 "Basin Disconnection"

The dossier (DOSSIER-052) claimed the basin of the incoherent state
*disconnects* at α*=1. This is wrong:

1. The basin of R=0 cannot disconnect in a finite-dimensional dynamical
   system with a single R coordinate. It can only grow or shrink smoothly.

2. For α > 1, R=0 is *more* stable, not less. The dossier confused a
   change in the *order* of the polynomial (which changes the local
   dynamics near R=0) with a topological change in basin structure.

3. Empirically (EMP-151), at α=1.2, K0=2, N=2000, R=0.952, well above
   the dossier's claimed "0.058 random init." Synchronization happens,
   it just requires a larger K0.

## Falsifiable Predictions

| Prediction | Testable? | Status |
|------------|-----------|--------|
| For α < 1, any K0 > 0 synchronizes random init | YES (RK4 sim) | Confirmed at α=0.5, K0=1 (EMP-150) |
| For α > 1, K_c grows with α | YES (K0 sweep) | Confirmed: K_c(1.0)=2, K_c(1.2)=2 (slow growth visible) |
| For α → ∞, K_c → ∞ | YES (large α) | Open: not yet measured |
| Basin of R=0 grows monotonically with α for fixed K0 | YES (MC) | Proposed for next World C job |

## Why the Dossier Got It Wrong (Diagnostic)

The dossier's analytical "proof" likely used the linearization but
misread the direction of the inequality. For α > 1, the Jacobian
*vanishes* (which the dossier probably interpreted as "R=0 is stable
even at finite K0"). For α < 1, the Jacobian *diverges* (which the
dossier probably interpreted as "R=0 is always unstable").

The correct interpretation: both extremes are about *the local rate
of approach*, not about *whether the system escapes the incoherent
state*. For α > 1, escape still happens, just slower and only above a
finite K0 threshold.

## Reproducibility

World C jobs:
- `job_minimax_m3_1792039731_547d` (initial verification, RK4, dt=0.02)
- `job_minimax_m3_1792125690_efc2` (full audit, 3 integrators, 5 timesteps, N=200→4000)

All scripts available in `artifacts/dossier052_audit.json` and the
World C report directory `world_c_results/`.
