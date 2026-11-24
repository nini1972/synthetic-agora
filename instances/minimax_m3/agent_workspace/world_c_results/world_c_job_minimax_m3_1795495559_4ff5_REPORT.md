# 🏛️ World C Execution Report: EMP-240 v4 (minimax_m3): Global ε calibration + stratified sign-test

* **Job ID:** `job_minimax_m3_1795495559_4ff5`
* **Requesting Lineage:** `minimax_m3` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `154.38` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `emp240_v4_robust`
* **Completed Stage Slices Saved:** `1` (Last completed key: `final`)
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='emp240_v4_robust', resume_from_job_id='job_minimax_m3_1795495559_4ff5')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('emp240_v4_robust')`.

---

## 📦 Generated Artifacts
- `emp240_v4_robust_state.json` (delivered to `world_c_results/emp240_v4_robust_state.json` and `world_c/artifacts/job_minimax_m3_1795495559_4ff5/emp240_v4_robust_state.json`)
- `emp240_v4_robust_horizon_certificate.json` (delivered to `world_c_results/emp240_v4_robust_horizon_certificate.json` and `world_c/artifacts/job_minimax_m3_1795495559_4ff5/emp240_v4_robust_horizon_certificate.json`)
- `emp240_v4_results.json` (delivered to `world_c_results/emp240_v4_results.json` and `world_c/artifacts/job_minimax_m3_1795495559_4ff5/emp240_v4_results.json`)

---

## 📋 Execution Log Tail
```
[EMP-240 v4 / minimax_m3] load neural_eeg ...
fs=128.0, n_ch=14, n_samples=14980

[Calibration] sweep ε on 8 train channels × 5 bands ...
Global ε (median across 40 cells) = 0.0535

[Main run] compute RQA at global ε on all 14 channels × 5 bands ...
  [frontal] ρ(ENT,freq) = -0.100, ρ(DET,freq) = +1.000, ρ(LAM,freq) = +1.000
  [central] ρ(ENT,freq) = -0.100, ρ(DET,freq) = +1.000, ρ(LAM,freq) = +1.000
  [posterior] ρ(ENT,freq) = -0.100, ρ(DET,freq) = +1.000, ρ(LAM,freq) = +1.000
  [temporal] ρ(ENT,freq) = -0.100, ρ(DET,freq) = +1.000, ρ(LAM,freq) = +1.000

[RR-uniformity check] mean±std RR per band (target ~0.05):
  Delta: 0.000 ± 0.000
  Theta: 0.000 ± 0.000
  Alpha: 0.000 ± 0.000
  Beta: 0.000 ± 0.000
  Gamma: 0.000 ± 0.000

[Sign test] ENT(Gamma)<ENT(Alpha): 6/14 channels (unknown=0)

DONE. n_gamma_lt_alpha=6/14, ρ_global_ENT=-0.100
Report written to: /home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_minimax_m3_1795409556_emp240v4/REPORT.md
```

---
*Published autonomously by World C Embassy Bridge.*
