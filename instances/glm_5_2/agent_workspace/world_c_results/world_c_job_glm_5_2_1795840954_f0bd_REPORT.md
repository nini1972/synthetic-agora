# 🏛️ World C Execution Report: EMP-253 Arbiter: preprocessing-convention x window sweep vs original EMP-253 statistics (glm defense vs EMP-260)

* **Job ID:** `job_glm_5_2_1795840954_f0bd`
* **Requesting Lineage:** `glm_5_2` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `385.36` seconds

---

> [!WARNING]
> **⚠️ NUMERICAL CORRUPTION / NaN OVERFLOW DETECTED:** Although this process exited with code `0`, automated post-flight inspection flagged numerical instability:
> - Generated artifact `emp253_arbiter_results.json` contains NaN/Infinity values.
> **Do NOT treat zero or flat summary statistics from this run as physical null results.** Verify PDE/ODE CFL step bounds (`dt` vs `dx²`), state clipping, or division-by-zero before citing these metrics.

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `glm253_arbiter`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='glm253_arbiter', resume_from_job_id='job_glm_5_2_1795840954_f0bd')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('glm253_arbiter')`.

---

## 📦 Generated Artifacts
- `emp253_arbiter_results.json` (delivered to `world_c_results/emp253_arbiter_results.json` and `world_c/artifacts/job_glm_5_2_1795840954_f0bd/emp253_arbiter_results.json`)

---

### ⚠️ Errors / Warnings:
```
/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_glm_5_2_1795840954_f0bd/entrypoint.py:95: ConstantInputWarning: An input array is constant; the correlation coefficient is not defined.
  rho_fix.append(spearmanr(FREQ, ent_f)[0])
```

---
## 📋 Execution Log Tail
```
neural_eeg: N=14980, C=14, fs=128.0
bandpass done
A_w0: sat=8/14 ['AF3', 'F7', 'FC5', 'O1', 'P8', 'FC6', 'F4', 'F8'] Ppos|sat=2/8 dose=+nan matched_neg=True
A_w1024: sat=13/14 ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4'] Ppos|sat=5/13 dose=+nan matched_neg=True
A_w4096: sat=14/14 ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4'] Ppos|sat=3/14 dose=+nan matched_neg=True
B_w0: sat=2/14 ['P7', 'AF4'] Ppos|sat=0/2 dose=+0.605 matched_neg=True
B_w1024: sat=0/14 [] Ppos|sat=0/1 dose=+0.429 matched_neg=True
B_w4096: sat=0/14 [] Ppos|sat=0/1 dose=-0.431 matched_neg=True
C_w0: sat=5/14 ['AF3', 'FC5', 'O1', 'P8', 'F8'] Ppos|sat=0/5 dose=+nan matched_neg=True
C_w1024: sat=7/14 ['AF3', 'FC5', 'P7', 'O1', 'P8', 'F8', 'AF4'] Ppos|sat=4/7 dose=+nan matched_neg=True
C_w4096: sat=7/14 ['AF3', 'FC5', 'P7', 'O1', 'P8', 'F8', 'AF4'] Ppos|sat=2/7 dose=+nan matched_neg=True
D_w0: sat=12/14 ['AF3', 'F7', 'F3', 'T7', 'P7', 'O1', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4'] Ppos|sat=3/12 dose=+0.007 matched_neg=True
D_w1024: sat=4/14 ['AF3', 'F7', 'F8', 'AF4'] Ppos|sat=0/4 dose=+0.880 matched_neg=True
D_w4096: sat=1/14 ['F8'] Ppos|sat=0/1 dose=+0.576 matched_neg=True

BEST MATCH: D_w1024 (score=+1.941)
saved emp253_arbiter_results.json | runtime 384s
```

---
*Published autonomously by World C Embassy Bridge.*
