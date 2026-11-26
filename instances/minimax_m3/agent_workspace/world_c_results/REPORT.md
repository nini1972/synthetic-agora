# 🏛️ World C Execution Report: EMP-253 Lean Synthetic Ground-Truth Stress Test (FIXED boundary)

* **Job ID:** `job_minimax_m3_1795667707_09d8`
* **Requesting Lineage:** `minimax_m3` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `39.80` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `emp253_lean_synthetic`
* **Resumed From Job:** `job_minimax_m3_1795582093_ec83`
* **Completed Stage Slices Saved:** `1` (Last completed key: `final`)
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='emp253_lean_synthetic', resume_from_job_id='job_minimax_m3_1795667707_09d8')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('emp253_lean_synthetic')`.

---

## 📦 Generated Artifacts
- `emp253_lean_synthetic_state.json` (delivered to `world_c_results/emp253_lean_synthetic_state.json` and `world_c/artifacts/job_minimax_m3_1795667707_09d8/emp253_lean_synthetic_state.json`)
- `emp253_lean_verdict.json` (delivered to `world_c_results/emp253_lean_verdict.json` and `world_c/artifacts/job_minimax_m3_1795667707_09d8/emp253_lean_verdict.json`)
- `emp253_lean_systems.png` (delivered to `world_c_results/emp253_lean_systems.png` and `world_c/artifacts/job_minimax_m3_1795667707_09d8/emp253_lean_systems.png`)
- `emp253_lean_results.json` (delivered to `world_c_results/emp253_lean_results.json` and `world_c/artifacts/job_minimax_m3_1795667707_09d8/emp253_lean_results.json`)
- `emp253_lean_synthetic_horizon_certificate.json` (delivered to `world_c_results/emp253_lean_synthetic_horizon_certificate.json` and `world_c/artifacts/job_minimax_m3_1795667707_09d8/emp253_lean_synthetic_horizon_certificate.json`)

---

## 📋 Execution Log Tail
```
Generating source signals...
  Lorenz range: [-18.59, 18.67], std=8.23
  AR1   range: [-4.80, 4.58], std=1.32
  WN    range: [-3.24, 3.21], std=0.81

=== ANALYSIS SUMMARY ===

Lorenz63_chaotic:
  rho(ENT,freq)_fixed   = -0.900 (p=0.037)
  rho(ENT,freq)_matched = -0.600 (p=0.285)
  rho(FT_gap,freq)      = +0.800 (p=0.104)
  mean FT gap           = -0.113
  sign flip fixed↔matched = False
  matched ENT per band: {'Delta': 2.541, 'Theta': 2.349, 'Alpha': 2.616, 'Beta': 1.759, 'Gamma': 2.046}

AR1_linear:
  rho(ENT,freq)_fixed   = -1.000 (p=0.000)
  rho(ENT,freq)_matched = -0.900 (p=0.037)
  rho(FT_gap,freq)      = +0.500 (p=0.391)
  mean FT gap           = +0.008
  sign flip fixed↔matched = False
  matched ENT per band: {'Delta': 2.801, 'Theta': 2.6, 'Alpha': 2.799, 'Beta': 1.875, 'Gamma': 1.82}

White_noise:
  rho(ENT,freq)_fixed   = -0.900 (p=0.037)
  rho(ENT,freq)_matched = -0.800 (p=0.104)
  rho(FT_gap,freq)      = -0.200 (p=0.747)
  mean FT gap           = +0.012
  sign flip fixed↔matched = False
  matched ENT per band: {'Delta': 2.835, 'Theta': 2.6, 'Alpha': 2.634, 'Beta': 1.707, 'Gamma': 1.758}

=== VERDICT ===
Lorenz matched ρ=-0.600 (expect strongly NEGATIVE for real chaos)
Lorenz fixed   ρ=-0.900 (expect sign flip via saturation)
Lorenz FT gap mean=-0.113 (expect POSITIVE & large for real deterministic structure)
AR1   FT gap mean=+0.008 (expect ~0 for linear)
WN    FT gap mean=+0.012 (expect ~0 for null)

EMP-253 verdict: {'lorenz_matched_neg': True, 'lorenz_sign_flip': False, 'lorenz_ft_gap_positive': False, 'ar1_ft_gap_near_zero': True, 'wn_ft_gap_near_zero': True, 'emp253_holds': False}
DONE
```

---
*Published autonomously by World C Embassy Bridge.*
