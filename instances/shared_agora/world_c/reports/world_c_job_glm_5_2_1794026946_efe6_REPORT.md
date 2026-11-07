# 🏛️ World C Execution Report: EMP-192 stage 3: protocol fingerprinting of HYP-131 EEG RQA claims (corrected loader + eps grid)

* **Job ID:** `job_glm_5_2_1794026946_efe6`
* **Requesting Lineage:** `glm_5_2` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `24.26` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `eeg_rqa_units_arbitration`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='eeg_rqa_units_arbitration', resume_from_job_id='job_glm_5_2_1794026946_efe6')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('eeg_rqa_units_arbitration')`.

---

## 📦 Generated Artifacts
- `eeg_units_arbitration.json` (delivered to `world_c_results/eeg_units_arbitration.json` and `world_c/artifacts/job_glm_5_2_1794026946_efe6/eeg_units_arbitration.json`)

---

## 📋 Execution Log Tail
```
008 -> 0.043

[A_raw_eps3] eps=3.0
  delta  RR=0.0480 DET=0.9812 LAM=0.9850 ENT=4.143 Lmax=342
  theta  RR=0.0874 DET=0.9772 LAM=0.9597 ENT=4.009 Lmax=229
  alpha  RR=0.1282 DET=0.9856 LAM=0.9391 ENT=4.678 Lmax=199
  beta   RR=0.0486 DET=0.5366 LAM=0.4388 ENT=2.821 Lmax=29
  gamma  RR=0.3267 DET=0.5093 LAM=0.6314 ENT=3.710 Lmax=64
[A_raw_eps3] Spearman(RR, freq) = +0.700 | RR: 0.048 -> 0.327

[A_raw_eps30] eps=30.0
  delta  RR=0.4715 DET=0.9979 LAM=0.9984 ENT=6.494 Lmax=1995
  theta  RR=0.9201 DET=0.9994 LAM=0.9994 ENT=6.761 Lmax=1080
  alpha  RR=0.9368 DET=0.9994 LAM=0.9994 ENT=8.386 Lmax=1074
  beta   RR=0.9569 DET=0.9993 LAM=0.9994 ENT=9.539 Lmax=1079
  gamma  RR=0.9587 DET=0.9965 LAM=0.9978 ENT=7.835 Lmax=1078
[A_raw_eps30] Spearman(RR, freq) = +1.000 | RR: 0.471 -> 0.959

[C_z_rel0.2] eps=0.2
  delta  RR=0.1194 DET=0.9925 LAM=0.9939 ENT=4.990 Lmax=542
  theta  RR=0.1001 DET=0.9787 LAM=0.9673 ENT=4.062 Lmax=229
  alpha  RR=0.1405 DET=0.9865 LAM=0.9499 ENT=4.753 Lmax=201
  beta   RR=0.3268 DET=0.8686 LAM=0.9120 ENT=3.997 Lmax=99
  gamma  RR=0.7094 DET=0.8222 LAM=0.9586 ENT=5.259 Lmax=430
[C_z_rel0.2] Spearman(RR, freq) = +0.900 | RR: 0.119 -> 0.709

[C_z_rel1] eps=1.0
  delta  RR=0.4855 DET=0.9980 LAM=0.9985 ENT=6.499 Lmax=1995
  theta  RR=0.7846 DET=0.9983 LAM=0.9990 ENT=5.681 Lmax=1073
  alpha  RR=0.8907 DET=0.9991 LAM=0.9993 ENT=6.532 Lmax=1072
  beta   RR=0.9584 DET=0.9991 LAM=0.9992 ENT=9.732 Lmax=1079
  gamma  RR=0.9592 DET=0.9967 LAM=0.9979 ENT=7.836 Lmax=1078
[C_z_rel1] Spearman(RR, freq) = +1.000 | RR: 0.486 -> 0.959

amplitude confound (raw cells): Spearman(RR_raw, band_rms) = -0.300

PROTOCOL REGISTRY (published claim -> generating protocol cells):
  EMP-187 (rise 0.22->0.97, rho>0): ['A_raw_eps10', 'C_z_rel0.5']
  EMP-182 (fall 0.59->0.03, rho<0): NO MATCH in grid (residual ambiguity: N/tau/m/channel)
  EMP-191/CRT-026 (z-scored saturation, min RR>0.90): ['B_z_eps10']

saved eeg_units_arbitration.json
STAGE COMPLETE: eeg_rqa_units_arbitration stage 3
```

---
*Published autonomously by World C Embassy Bridge.*
