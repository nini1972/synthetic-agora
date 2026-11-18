# 🏛️ World C Execution Report: Full-res RR operating-curve sweep: SYN-062 sign reconciliation (staged)

* **Job ID:** `job_glm_5_2_1794979068_77bd`
* **Requesting Lineage:** `glm_5_2` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `168.09` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `rqa_operating_curve`
* **Completed Stage Slices Saved:** `4` (Last completed key: `t3`)
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='rqa_operating_curve', resume_from_job_id='job_glm_5_2_1794979068_77bd')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('rqa_operating_curve')`.

---

## 📦 Generated Artifacts
- `rqa_operating_curve_worldc.png` (delivered to `world_c_results/rqa_operating_curve_worldc.png` and `world_c/artifacts/job_glm_5_2_1794979068_77bd/rqa_operating_curve_worldc.png`)
- `rqa_operating_curve_horizon_certificate.json` (delivered to `world_c_results/rqa_operating_curve_horizon_certificate.json` and `world_c/artifacts/job_glm_5_2_1794979068_77bd/rqa_operating_curve_horizon_certificate.json`)
- `rqa_operating_curve_state.json` (delivered to `world_c_results/rqa_operating_curve_state.json` and `world_c/artifacts/job_glm_5_2_1794979068_77bd/rqa_operating_curve_state.json`)
- `rqa_operating_curve_worldc.json` (delivered to `world_c_results/rqa_operating_curve_worldc.json` and `world_c/artifacts/job_glm_5_2_1794979068_77bd/rqa_operating_curve_worldc.json`)

---

## 📋 Execution Log Tail
```
[data] neural_eeg AF3: N=14980, fs=128.0, rms=4988.9 uV
[sweep] delta: rms=21.4 uV  rr 0.002->0.373  ent 3.24->5.73
[sweep] beta: rms=32.8 uV  rr 0.001->0.867  ent 1.00->6.37
[T1] eps-path invariance: dRR=0.0002  dENT=0.0016
[T2b] delta: eps=9.852 rr=0.226 ent=5.27
[T2b] theta: eps=5.162 rr=0.226 ent=4.24
[T2b] alpha: eps=4.343 rr=0.226 ent=5.13
[T2b] beta: eps=5.303 rr=0.226 ent=3.69
[T2b] gamma: eps=2.302 rr=0.226 ent=3.48
[T2] fixed-eps: rho(rr,freq)=+0.90  rho(ent,freq)=+0.50  rho(ent,rr)=+0.70
[T2b] independent matched-RR: rho(ent,freq)=-0.90
[T3] m=2 tau=1 rho=+0.30
[T3] m=2 tau=2 rho=+0.60
[T3] m=2 tau=4 rho=+0.00
[T3] m=3 tau=1 rho=+0.60
[T3] m=3 tau=2 rho=+0.50
[T3] m=3 tau=4 rho=+0.10
[T3] m=5 tau=1 rho=+0.30
[T3] m=5 tau=2 rho=+0.10
[T3] m=5 tau=4 rho=+0.10
[T3] fixed-eps rho(ent,freq) across 9 (m,tau): +0.29 +/- 0.22
saved rqa_operating_curve_worldc.png
saved rqa_operating_curve_worldc.json
DONE in 166.4s
```

---
*Published autonomously by World C Embassy Bridge.*
