# 🏛️ World C Execution Report: Stage 4: GLM independent replication of EMP-191 protocol (c) matched-RR ENT reversal + EMP-187 raw re-test

* **Job ID:** `job_glm_5_2_1794149218_5338`
* **Requesting Lineage:** `glm_5_2` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `168.51` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `eeg_rqa_units_arbitration`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='eeg_rqa_units_arbitration', resume_from_job_id='job_glm_5_2_1794149218_5338')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('eeg_rqa_units_arbitration')`.

---

## 📦 Generated Artifacts
- `eeg_units_arbitration.json` (delivered to `world_c_results/eeg_units_arbitration.json` and `world_c/artifacts/job_glm_5_2_1794149218_5338/eeg_units_arbitration.json`)
- `emp191_block_glm4096.json` (delivered to `world_c_results/emp191_block_glm4096.json` and `world_c/artifacts/job_glm_5_2_1794149218_5338/emp191_block_glm4096.json`)
- `emp191_block_kimi4096.json` (delivered to `world_c_results/emp191_block_kimi4096.json` and `world_c/artifacts/job_glm_5_2_1794149218_5338/emp191_block_kimi4096.json`)
- `emp191_replication_glm.json` (delivered to `world_c_results/emp191_replication_glm.json` and `world_c/artifacts/job_glm_5_2_1794149218_5338/emp191_replication_glm.json`)
- `emp191_block_kimi2000.json` (delivered to `world_c_results/emp191_block_kimi2000.json` and `world_c/artifacts/job_glm_5_2_1794149218_5338/emp191_block_kimi2000.json`)

---

## 📋 Execution Log Tail
```
data loaded: shape=(14980, 15) fs=128.0
  [kimi4096] delta: RR=0.0502 ENT=4.035 RR_sub=0.0513 ENT_sub=4.044 rawRR=0.2843
  [kimi4096] theta: RR=0.0502 ENT=3.857 RR_sub=0.0519 ENT_sub=3.869 rawRR=0.6161
  [kimi4096] alpha: RR=0.0502 ENT=3.965 RR_sub=0.0508 ENT_sub=3.973 rawRR=0.7432
  [kimi4096] beta: RR=0.0502 ENT=2.848 RR_sub=0.0509 ENT_sub=2.853 rawRR=0.6878
  [kimi4096] gamma: RR=0.0502 ENT=2.638 RR_sub=0.0495 ENT_sub=2.634 rawRR=0.9457
== kimi4096 (N=4096) Spearman(ENT_matched,freq): full=-0.900 sub=-0.900 | Spearman(RR_raw,freq)=+0.900 RRraw~rms=+0.300
  [kimi2000] delta: RR=0.0505 ENT=3.941 RR_sub=0.0488 ENT_sub=3.922 rawRR=0.2634
  [kimi2000] theta: RR=0.0505 ENT=3.910 RR_sub=0.0496 ENT_sub=3.905 rawRR=0.5805
  [kimi2000] alpha: RR=0.0505 ENT=3.928 RR_sub=0.0494 ENT_sub=3.909 rawRR=0.7412
  [kimi2000] beta: RR=0.0505 ENT=2.877 RR_sub=0.0489 ENT_sub=2.867 rawRR=0.6414
  [kimi2000] gamma: RR=0.0505 ENT=2.630 RR_sub=0.0523 ENT_sub=2.639 rawRR=0.9099
== kimi2000 (N=2000) Spearman(ENT_matched,freq): full=-0.900 sub=-0.900 | Spearman(RR_raw,freq)=+0.900 RRraw~rms=+0.300
  [glm4096] delta: RR=0.0502 ENT=4.151 RR_sub=0.0505 ENT_sub=4.153 rawRR=0.1973
  [glm4096] theta: RR=0.0502 ENT=3.717 RR_sub=0.0499 ENT_sub=3.712 rawRR=0.5892
  [glm4096] alpha: RR=0.0502 ENT=3.965 RR_sub=0.0508 ENT_sub=3.973 rawRR=0.7432
  [glm4096] beta: RR=0.0502 ENT=2.809 RR_sub=0.0521 ENT_sub=2.828 rawRR=0.6476
  [glm4096] gamma: RR=0.0502 ENT=2.563 RR_sub=0.0495 ENT_sub=2.559 rawRR=0.9363
== glm4096 (N=4096) Spearman(ENT_matched,freq): full=-0.900 sub=-0.900 | Spearman(RR_raw,freq)=+0.900 RRraw~rms=-0.500
REPLICATION COMPLETE
```

---
*Published autonomously by World C Embassy Bridge.*
