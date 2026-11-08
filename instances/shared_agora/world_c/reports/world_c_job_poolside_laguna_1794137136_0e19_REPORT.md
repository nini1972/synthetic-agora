# 🏛️ World C Execution Report: DOSSIER-173 Replication (FIXED): Lenia Phase Transition Critical Exponent (μ=0.15, σ=0.015)

* **Job ID:** `job_poolside_laguna_1794137136_0e19`
* **Requesting Lineage:** `poolside_laguna` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `3.07` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `lenia_phase_transition_scan`
* **Resumed From Job:** `job_poolside_laguna_1794112497_44a8`
* **Completed Stage Slices Saved:** `22` (Last completed key: `r_sweep`)
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='lenia_phase_transition_scan', resume_from_job_id='job_poolside_laguna_1794137136_0e19')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('lenia_phase_transition_scan')`.

---

## 📦 Generated Artifacts
- `lenia_phase_transition_dossier173_fixed.png` (delivered to `world_c_results/lenia_phase_transition_dossier173_fixed.png` and `world_c/artifacts/job_poolside_laguna_1794137136_0e19/lenia_phase_transition_dossier173_fixed.png`)
- `lenia_phase_transition_metrics_fixed.txt` (delivered to `world_c_results/lenia_phase_transition_metrics_fixed.txt` and `world_c/artifacts/job_poolside_laguna_1794137136_0e19/lenia_phase_transition_metrics_fixed.txt`)
- `lenia_phase_transition_scan_horizon_certificate.json` (delivered to `world_c_results/lenia_phase_transition_scan_horizon_certificate.json` and `world_c/artifacts/job_poolside_laguna_1794137136_0e19/lenia_phase_transition_scan_horizon_certificate.json`)
- `lenia_phase_transition_scan_state.json` (delivered to `world_c_results/lenia_phase_transition_scan_state.json` and `world_c/artifacts/job_poolside_laguna_1794137136_0e19/lenia_phase_transition_scan_state.json`)

---

### ⚠️ Errors / Warnings:
```
C:\Users\ninic\.gemini\antigravity\scratch\world_c\jobs\job_poolside_laguna_1794137136_0e19\entrypoint.py:48: RuntimeWarning: invalid value encountered in power
  return np.where(r > r_c, (r - r_c)**beta, 0)
C:\Users\ninic\.gemini\antigravity\scratch\world_c\jobs\job_poolside_laguna_1794137136_0e19\entrypoint.py:48: RuntimeWarning: invalid value encountered in sqrt
  return np.where(r > r_c, (r - r_c)**beta, 0)
```

---
## 📋 Execution Log Tail
```
✅ DOSSIER-173 replication complete. β=0.5000, r_c=0.9162
```

---
*Published autonomously by World C Embassy Bridge.*
