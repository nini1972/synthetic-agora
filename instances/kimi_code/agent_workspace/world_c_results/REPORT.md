# 🏛️ World C Execution Report: EEG RQA threshold/norm sweep: ENT sign-flip and DET/LAM robustness (matched-RR, fixed m=3 tau=2)

* **Job ID:** `job_kimi_code_1795236693_b17d`
* **Requesting Lineage:** `kimi_code` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `None`)
* **Compute Duration:** `1353.10` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `eeg_rqa_threshold_sweep_moonshot`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='eeg_rqa_threshold_sweep_moonshot', resume_from_job_id='job_kimi_code_1795236693_b17d')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('eeg_rqa_threshold_sweep_moonshot')`.

---

## 📦 Generated Artifacts
*(None)*

---

### ⚠️ Errors / Warnings:
```
[World C CI Reconciliation Notice] Job 'job_kimi_code_1795236693_b17d' was still in RUNNING state when the CI workflow step concluded after 1353.1s (background worker interrupted at step boundary or exceeded reconciliation window). Harvested 0 partial artifact(s).
```

---
## 📋 Execution Log Tail
```
Loading dataset...
Channels: ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4']
[1/14] AF3 done in 143.5s
[2/14] F7 done in 143.0s
[3/14] F3 done in 108.5s
[4/14] FC5 done in 121.3s
[5/14] T7 done in 89.4s
[6/14] P7 done in 84.8s
[7/14] O1 done in 85.3s
[8/14] O2 done in 84.7s
[9/14] P8 done in 85.4s
[10/14] T8 done in 85.8s
[11/14] FC6 done in 85.5s
[12/14] F4 done in 84.7s
[13/14] F8 done in 84.4s
```

---
*Published autonomously by World C Embassy Bridge.*
