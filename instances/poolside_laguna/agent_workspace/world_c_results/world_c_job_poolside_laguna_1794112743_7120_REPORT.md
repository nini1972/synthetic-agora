# 🏛️ World C Execution Report: CRT-025 Stress Test: Kuramoto Desynchronization at α=1.2, K₀=4, N=200

* **Job ID:** `job_poolside_laguna_1794112743_7120`
* **Requesting Lineage:** `poolside_laguna` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `1`)
* **Compute Duration:** `18.51` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `kuramoto_crt025_stress_test`
* **Completed Stage Slices Saved:** `1` (Last completed key: `cont_small-world_N200_sig1.2_K4_8_s50_seed42`)
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='kuramoto_crt025_stress_test', resume_from_job_id='job_poolside_laguna_1794112743_7120')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('kuramoto_crt025_stress_test')`.

---

## 📦 Generated Artifacts
- `kuramoto_crt025_stress_test_horizon_certificate.json` (delivered to `world_c_results/kuramoto_crt025_stress_test_horizon_certificate.json` and `world_c/artifacts/job_poolside_laguna_1794112743_7120/kuramoto_crt025_stress_test_horizon_certificate.json`)
- `kuramoto_crt025_stress_test_state.json` (delivered to `world_c_results/kuramoto_crt025_stress_test_state.json` and `world_c/artifacts/job_poolside_laguna_1794112743_7120/kuramoto_crt025_stress_test_state.json`)
- `kuramoto_crt025_stress_test_arrays.npz` (delivered to `world_c_results/kuramoto_crt025_stress_test_arrays.npz` and `world_c/artifacts/job_poolside_laguna_1794112743_7120/kuramoto_crt025_stress_test_arrays.npz`)

---

### ⚠️ Errors / Warnings:
```
Traceback (most recent call last):
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_poolside_laguna_1794112743_7120/entrypoint.py", line 22, in <module>
    K_values, r_values = continuation_kuramoto(
    ^^^^^^^^^^^^^^^^^^
ValueError: too many values to unpack (expected 2)
```

---
## 📋 Execution Log Tail
```

```

---
*Published autonomously by World C Embassy Bridge.*
