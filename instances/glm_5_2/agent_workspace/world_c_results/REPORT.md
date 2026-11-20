# 🏛️ World C Execution Report: RQA-ENT sign-flip phase diagram vs matched RR operating point (neural_eeg, full 14-ch)

* **Job ID:** `job_glm_5_2_1795150061_7704`
* **Requesting Lineage:** `glm_5_2` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `1`)
* **Compute Duration:** `1.07` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `rqa_flip_phase_diagram`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='rqa_flip_phase_diagram', resume_from_job_id='job_glm_5_2_1795150061_7704')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('rqa_flip_phase_diagram')`.

---

## 📦 Generated Artifacts
*(None)*

---

### ⚠️ Errors / Warnings:
```
Traceback (most recent call last):
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_glm_5_2_1795150061_7704/entrypoint.py", line 32, in <module>
    if X.shape[0] < X.shape[1]:
                    ~~~~~~~^^^
IndexError: tuple index out of range
```

---
## 📋 Execution Log Tail
```

```

---
*Published autonomously by World C Embassy Bridge.*
