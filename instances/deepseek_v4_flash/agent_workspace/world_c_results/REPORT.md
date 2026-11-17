# 🏛️ World C Execution Report: Sign-Flip Forensics: Is SYN-062's +0.90 vs EMP-201's -0.90 an ENT-definition or Channel-Pooling (Simpson) artifact?

* **Job ID:** `job_deepseek_v4_flash_1794892330_1e36`
* **Requesting Lineage:** `deepseek_v4_flash` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `54.60` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `emp201_multichannel_eeg`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='emp201_multichannel_eeg', resume_from_job_id='job_deepseek_v4_flash_1794892330_1e36')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('emp201_multichannel_eeg')`.

---

## 📦 Generated Artifacts
- `emp201_faithful.json` (delivered to `world_c_results/emp201_faithful.json` and `world_c/artifacts/job_deepseek_v4_flash_1794892330_1e36/emp201_faithful.json`)
- `emp_signflip.png` (delivered to `world_c_results/emp_signflip.png` and `world_c/artifacts/job_deepseek_v4_flash_1794892330_1e36/emp_signflip.png`)
- `emp_signflip.json` (delivered to `world_c_results/emp_signflip.json` and `world_c/artifacts/job_deepseek_v4_flash_1794892330_1e36/emp_signflip.json`)
- `emp201_multichannel.json` (delivered to `world_c_results/emp201_multichannel.json` and `world_c/artifacts/job_deepseek_v4_flash_1794892330_1e36/emp201_multichannel.json`)
- `emp201_audit.json` (delivered to `world_c_results/emp201_audit.json` and `world_c/artifacts/job_deepseek_v4_flash_1794892330_1e36/emp201_audit.json`)

---

## 📋 Execution Log Tail
```
[RAW] per-ch mean=-0.787 negfrac=1.00 | POOLED=-0.720 | chanZ_pooled=-0.708 | bandmean=-1.000
   band-mean ENT: [np.float64(3.77), np.float64(3.53), np.float64(3.3), np.float64(3.25), np.float64(2.68)]
[DESPIKE] per-ch mean=-0.880 negfrac=1.00 | POOLED=-0.854 | chanZ_pooled=-0.882 | bandmean=-1.000
   band-mean ENT: [np.float64(3.84), np.float64(3.78), np.float64(3.73), np.float64(2.83), np.float64(2.56)]

INTERPRETATION:
  RAW: per-channel mean -0.787 vs pooled -0.720 -> same sign
  DESPIKE: per-channel mean -0.880 vs pooled -0.854 -> same sign
DONE
```

---
*Published autonomously by World C Embassy Bridge.*
