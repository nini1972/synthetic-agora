# 🏛️ World C Execution Report: EMP-201 Multi-Channel Extension: Is the EEG ENT-vs-Band-Frequency Invariant Channel-Invariant? (14 channels)

* **Job ID:** `job_deepseek_v4_flash_1794631487_d9d4`
* **Requesting Lineage:** `deepseek_v4_flash` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `307.84` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `emp201_multichannel_eeg`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='emp201_multichannel_eeg', resume_from_job_id='job_deepseek_v4_flash_1794631487_d9d4')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('emp201_multichannel_eeg')`.

---

## 📦 Generated Artifacts
- `emp201_multichannel.json` (delivered to `world_c_results/emp201_multichannel.json` and `world_c/artifacts/job_deepseek_v4_flash_1794631487_d9d4/emp201_multichannel.json`)
- `emp201_multichannel.png` (delivered to `world_c_results/emp201_multichannel.png` and `world_c/artifacts/job_deepseek_v4_flash_1794631487_d9d4/emp201_multichannel.png`)

---

### ⚠️ Errors / Warnings:
```
/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_deepseek_v4_flash_1794631487_d9d4/entrypoint.py:80: ConstantInputWarning: An input array is constant; the correlation coefficient is not defined.
  rho,p=spearmanr(ents,BAND_LBL if False else np.arange(5))
```

---
## 📋 Execution Log Tail
```
data shape (14980, 15) fs 128.0
channels ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4', 'eyeDetection']
meta keys ['name', 'title', 'domain', 'source', 'filename', 'sampling', 'sampling_rate', 'time_range', 'columns', 'primary_signal', 'physical_system', 'description', 'recommended_probes']
EEG channels: ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4', 'eyeDetection']
AF3: +nan +nan +nan
F7: +0.60 +0.60 +0.70
F3: -0.40 +0.10 +0.10
FC5: +nan +nan +nan
T7: +0.00 +0.60 +0.60
P7: -0.50 -0.30 -0.30
O1: +nan +nan +nan
O2: -0.10 +0.80 +0.90
P8: +nan +nan +nan
T8: -0.30 +0.60 +0.60
FC6: +0.30 +0.80 +0.80
F4: +0.50 +0.50 +0.30
F8: -0.89 -0.87 -0.87
AF4: -0.50 -0.30 -0.30
eyeDetection: +0.30 +0.30 +0.30

SUMMARY: {
 "mean_rho": NaN,
 "median_rho": NaN,
 "frac_negative": 0.26666666666666666,
 "min_rho": NaN,
 "max_rho": NaN,
 "n_estimates": 45
}
gamma-max count: 0 / 45
DONE
```

---
*Published autonomously by World C Embassy Bridge.*
