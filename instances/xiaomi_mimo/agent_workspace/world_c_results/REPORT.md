# 🏛️ World C Execution Report: Condition C EEG RQA: Blinded parameter-grid arbitration isolating the sign-flip knob

* **Job ID:** `job_xiaomi_mimo_1794458501_adb6`
* **Requesting Lineage:** `xiaomi_mimo` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `None`)
* **Compute Duration:** `2345.22` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `condition_c_arbitration`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='condition_c_arbitration', resume_from_job_id='job_xiaomi_mimo_1794458501_adb6')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('condition_c_arbitration')`.

---

## 📦 Generated Artifacts
*(None)*

---

### ⚠️ Errors / Warnings:
```
[World C CI Reconciliation Notice] Job 'job_xiaomi_mimo_1794458501_adb6' was still in RUNNING state when the CI workflow step concluded after 2345.2s (background worker interrupted at step boundary or exceeded reconciliation window). Harvested 0 partial artifact(s).
```

---
## 📋 Execution Log Tail
```
[data] X=(14980, 15) fs=128.0 channels=15
[OFAT] baseline (m3,t1,q4,eps=q95,nb16,all14)        rho=-0.200 pos=0.00 d(G-A)=+1.192
[OFAT] m=2                                           rho=-0.140 pos=0.00 d(G-A)=+1.749
[OFAT] m=5                                           rho=-0.113 pos=0.00 d(G-A)=+0.257
[OFAT] tau=2                                         rho=-0.340 pos=0.00 d(G-A)=-1.078
[OFAT] tau=3                                         rho=-0.807 pos=0.00 d(G-A)=-0.051
```

---
*Published autonomously by World C Embassy Bridge.*
