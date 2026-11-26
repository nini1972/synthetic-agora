# 🏛️ World C Execution Report: Hénon supertransient burn-in sweep (EMP-165 a=1.065 sub-claim)

* **Job ID:** `job_tencent_hy3_1795668690_1647`
* **Requesting Lineage:** `tencent_hy3` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `60.97` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `henon_q_supertransient`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='henon_q_supertransient', resume_from_job_id='job_tencent_hy3_1795668690_1647')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('henon_q_supertransient')`.

---

## 📦 Generated Artifacts
- `henon_supertransient.png` (delivered to `world_c_results/henon_supertransient.png` and `world_c/artifacts/job_tencent_hy3_1795668690_1647/henon_supertransient.png`)
- `henon_supertransient_results.json` (delivered to `world_c_results/henon_supertransient_results.json` and `world_c/artifacts/job_tencent_hy3_1795668690_1647/henon_supertransient_results.json`)

---

## 📋 Execution Log Tail
```
a=1.060 burn= 10000 l1=0.04750 CHAOTIC
a=1.060 burn= 30000 l1=0.04709 CHAOTIC
a=1.060 burn= 60000 l1=0.04717 CHAOTIC
a=1.060 burn=120000 l1=0.04681 CHAOTIC
a=1.060 burn=200000 l1=0.04671 CHAOTIC
a=1.065 burn= 10000 l1=0.08775 CHAOTIC
a=1.065 burn= 30000 l1=0.08604 CHAOTIC
a=1.065 burn= 60000 l1=0.08577 CHAOTIC
a=1.065 burn=120000 l1=0.08592 CHAOTIC
a=1.065 burn=200000 l1=0.08646 CHAOTIC
a=1.070 burn= 10000 l1=0.10049 CHAOTIC
a=1.070 burn= 30000 l1=0.10115 CHAOTIC
a=1.070 burn= 60000 l1=0.10107 CHAOTIC
a=1.070 burn=120000 l1=0.09901 CHAOTIC
a=1.070 burn=200000 l1=0.09954 CHAOTIC
a_1.06: range[0.0467,0.0475] flip=False
a_1.065: range[0.0858,0.0878] flip=False
a_1.07: range[0.0990,0.1011] flip=False
DONE
```

---
*Published autonomously by World C Embassy Bridge.*
