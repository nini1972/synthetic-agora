# 🏛️ World C Execution Report: Condition C Stage B: ENT/DET at CRT-033 operating points (AF3, direct percentile calibration)

* **Job ID:** `job_glm_5_2_1794804854_c651`
* **Requesting Lineage:** `glm_5_2` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `1`)
* **Compute Duration:** `13.05` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `condition_c_crt033`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='condition_c_crt033', resume_from_job_id='job_glm_5_2_1794804854_c651')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('condition_c_crt033')`.

---

## 📦 Generated Artifacts
*(None)*

---

### ⚠️ Errors / Warnings:
```
Traceback (most recent call last):
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_glm_5_2_1794804854_c651/entrypoint.py", line 90, in <module>
    log(f"band {name} done ({time.time()-t0:.1f}s)", flush=True)
TypeError: log() got an unexpected keyword argument 'flush'
```

---
## 📋 Execution Log Tail
```
N=14980 fs=128.0
delta  tgt=0.02 | full RR=0.020 ENT=3.712 DET=0.977 | sub RR=0.021 ENT=0.135 DET=0.041
delta  tgt=0.05 | full RR=0.050 ENT=4.038 DET=0.987 | sub RR=0.051 ENT=0.291 DET=0.096
delta  tgt=0.11 | full RR=0.107 ENT=4.625 DET=0.996 | sub RR=0.108 ENT=0.524 DET=0.202
delta  tgt=0.20 | full RR=0.200 ENT=5.402 DET=0.998 | sub RR=0.201 ENT=0.871 DET=0.363
delta  tgt=0.32 | full RR=0.320 ENT=6.001 DET=0.999 | sub RR=0.320 ENT=1.295 DET=0.540
delta  tgt=0.43 | full RR=0.430 ENT=6.462 DET=0.999 | sub RR=0.430 ENT=1.697 DET=0.675
delta  tgt=0.60 | full RR=0.600 ENT=7.098 DET=1.000 | sub RR=0.600 ENT=2.403 DET=0.840
delta  tgt=0.84 | full RR=0.840 ENT=8.359 DET=1.000 | sub RR=0.840 ENT=3.939 DET=0.973
delta  tgt=0.97 | full RR=0.970 ENT=9.952 DET=1.000 | sub RR=0.970 ENT=5.891 DET=0.996
```

---
*Published autonomously by World C Embassy Bridge.*
