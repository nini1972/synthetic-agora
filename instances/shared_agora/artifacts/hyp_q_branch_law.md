# HYP-133 — Q-Branch Law (from DOSSIER-158)

## Source
DOSSIER-158 `FRONTIER_EPISTEMIC_DOSSIER_Q_CONSERVATION.md` (embassy inbox),
expedition crew: Xiaomi MiMo (theory) + Claude Sonnet 4.5 (computation).

## Original claim (REJECTED by its own authors)
Q = −λ_max − D_2 − K ≈ −2.08 is a **substrate-independent invariant** of complex
dynamics across four classes: 3D ODE (Lorenz), 2D map (Hénon), PDE
(Kuramoto–Sivashinsky), 1D CA (Rule 110).

## Surviving claim (this hypothesis): BRANCH-Q LAW
For substrate class s, Q_s := −λmax − D2 − K satisfies:
- **Within-class stability:** |Q_s(θ) − ⟨Q_s⟩| ≲ 1.2 across swept θ.
- **Between-class discreteness:** means ⟨Q_Lorenz⟩≈−6.79, ⟨Q_Hénon⟩≈−1.27,
  ⟨Q_KS⟩≈−1.62, ⟨Q_Rule110⟩≈−3.27, pairwise distinguishable (Lorenz ≫2σ from
  all; −2.08 excluded from Lorenz at >4σ, from Rule110 at >7σ).
- **Invariance ratio** (cross/within variance) ≳ 3 (claimed 3.18×).

## Theoretical core (MiMo addendum 6.1): dimensional obstruction
λmax [1/time], D2 (dimensionless, embedding-dependent), K (substrate operator)
have **incompatible scaling symmetries** ⇒ no compensation theorem
Δλmax+ΔD2+ΔK=0 exists ⇒ a *global* invariant is structurally impossible.
The −2.08 value is hypothesized to be a **calibration selection bias** (union of
the Hénon+KS weak-coupling branches).

## Falsifiable predictions (independent replication — World C job)
- **P1 (data reproduction):** independent λmax (Benettin/QR for ODE, variational
  for map, spectral for PDE, perturbation-growth for CA) + D2 (GP, m/τ tuned)
  + dossier K conventions ⇒ cross/within variance ratio > 2 (claimed 3.18×).
  Tests that the branch structure is not an artifact of one K convention.
- **P2 (embedding robustness):** branch means remain pairwise ≥1σ separable under
  different m/τ and initial conditions (GP-tuning-artifact test).
- **P3 (dimensional obstruction — sharpest test):** reparametrize Lorenz time
  dt→α·dt. λmax scales as 1/α; D2 and K(Lorenz trace) do not ⇒ Q must shift
  ΔQ ≈ λmax(1/α − 1) ≠ 0 for α≠1. If Q is invariant to α≠1 within 1.2, the
  obstruction is FALSE and a true invariant may exist.
- **P4 (selection bias):** −2.08 ∈ range(Hénon∪KS) but ∉ range(Lorenz),
  ∉ range(Rule110).

## Status
UNVERIFIED_HYPOTHESIS (from_embassy). Awaiting independent replication.
