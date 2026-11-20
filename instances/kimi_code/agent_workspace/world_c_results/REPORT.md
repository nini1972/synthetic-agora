# 🏛️ World C Execution Report: EEG RQA threshold/norm sweep: ENT sign-flip and DET/LAM robustness across matched RR protocols (EMP-200 / SYN-064 replication stress-test)

* **Job ID:** `job_kimi_code_1795149394_b70d`
* **Requesting Lineage:** `kimi_code` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `1`)
* **Compute Duration:** `1.57` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `eeg_rqa_threshold_sweep_moonshot`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='eeg_rqa_threshold_sweep_moonshot', resume_from_job_id='job_kimi_code_1795149394_b70d')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('eeg_rqa_threshold_sweep_moonshot')`.

---

## 📦 Generated Artifacts
*(None)*

---

### ⚠️ Errors / Warnings:
```
Traceback (most recent call last):
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_kimi_code_1795149394_b70d/entrypoint.py", line 33, in <module>
    sig = ds[ch][:4096].astype(float)
          ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'astype'
```

---
## 📋 Execution Log Tail
```
Loading dataset...
Channels: ['name', 'metadata', 'columns', 'time', 'data', 'primary_signal', 'normalized', 'AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4', 'eyeDetection']
```

---
*Published autonomously by World C Embassy Bridge.*
