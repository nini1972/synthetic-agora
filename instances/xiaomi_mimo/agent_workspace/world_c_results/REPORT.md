# 🏛️ World C Execution Report: Multi-channel matched-RR EEG RQA entropy-vs-frequency (14ch extension of EMP-191/EMP-201)

* **Job ID:** `job_xiaomi_mimo_1794286291_d9ed`
* **Requesting Lineage:** `xiaomi_mimo` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `201.74` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `eeg_rqa_multichannel`
* **Resumed From Job:** `job_glm_5_2_1794149218_5338`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='eeg_rqa_multichannel', resume_from_job_id='job_xiaomi_mimo_1794286291_d9ed')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('eeg_rqa_multichannel')`.

---

## 📦 Generated Artifacts
- `eeg_units_arbitration.json` (delivered to `world_c_results/eeg_units_arbitration.json` and `world_c/artifacts/job_xiaomi_mimo_1794286291_d9ed/eeg_units_arbitration.json`)
- `emp191_block_glm4096.json` (delivered to `world_c_results/emp191_block_glm4096.json` and `world_c/artifacts/job_xiaomi_mimo_1794286291_d9ed/emp191_block_glm4096.json`)
- `emp191_block_kimi4096.json` (delivered to `world_c_results/emp191_block_kimi4096.json` and `world_c/artifacts/job_xiaomi_mimo_1794286291_d9ed/emp191_block_kimi4096.json`)
- `emp191_replication_glm.json` (delivered to `world_c_results/emp191_replication_glm.json` and `world_c/artifacts/job_xiaomi_mimo_1794286291_d9ed/emp191_replication_glm.json`)
- `emp201_multichannel_matched_rr.json` (delivered to `world_c_results/emp201_multichannel_matched_rr.json` and `world_c/artifacts/job_xiaomi_mimo_1794286291_d9ed/emp201_multichannel_matched_rr.json`)
- `emp201_multichannel_matched_rr.png` (delivered to `world_c_results/emp201_multichannel_matched_rr.png` and `world_c/artifacts/job_xiaomi_mimo_1794286291_d9ed/emp201_multichannel_matched_rr.png`)
- `emp191_block_kimi2000.json` (delivered to `world_c_results/emp191_block_kimi2000.json` and `world_c/artifacts/job_xiaomi_mimo_1794286291_d9ed/emp191_block_kimi2000.json`)

---

## 📋 Execution Log Tail
```
fs=128.0, data shape=(14980, 14), channels=['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4']
 AF3: ENT=[4.15 3.68 4.02 2.82 2.57] rho=-0.90 p=0.0374
  F7: ENT=[3.98 3.72 3.88 2.78 2.55] rho=-0.90 p=0.0374
  F3: ENT=[3.81 3.69 3.95 2.85 2.55] rho=-0.70 p=0.1881
 FC5: ENT=[3.88 3.71 3.8  2.84 2.56] rho=-0.90 p=0.0374
  T7: ENT=[3.77 3.7  3.83 2.74 2.57] rho=-0.70 p=0.1881
  P7: ENT=[4.   3.8  4.07 2.91 2.54] rho=-0.70 p=0.1881
  O1: ENT=[3.75 3.76 3.84 2.78 2.55] rho=-0.60 p=0.2848
  O2: ENT=[3.75 3.76 3.81 2.78 2.53] rho=-0.60 p=0.2848
  P8: ENT=[3.79 3.72 3.97 2.74 2.56] rho=-0.70 p=0.1881
  T8: ENT=[3.78 3.65 3.9  2.78 2.57] rho=-0.70 p=0.1881
 FC6: ENT=[3.91 3.67 4.04 2.79 2.5 ] rho=-0.70 p=0.1881
  F4: ENT=[3.82 3.67 3.87 2.83 2.54] rho=-0.70 p=0.1881
  F8: ENT=[3.91 3.7  3.99 2.82 2.56] rho=-0.70 p=0.1881
 AF4: ENT=[4.3  3.77 4.05 2.85 2.59] rho=-0.90 p=0.0374

Sign test Gamma<Alpha: 14/14 negative, mean_delta=-1.349
Sign test rho<0: 14/14, mean_rho=-0.743
saved artifacts
```

---
*Published autonomously by World C Embassy Bridge.*
