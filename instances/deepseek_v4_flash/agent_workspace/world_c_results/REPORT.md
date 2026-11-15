# 🏛️ World C Execution Report: EMP-201 Definitive Audit: Impulse Artifacts in neural_eeg Inflate Per-Channel rho; Strict Monotonicity Fails at Theta

* **Job ID:** `job_deepseek_v4_flash_1794717901_11a0`
* **Requesting Lineage:** `deepseek_v4_flash` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `131.75` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `emp201_multichannel_eeg`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='emp201_multichannel_eeg', resume_from_job_id='job_deepseek_v4_flash_1794717901_11a0')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('emp201_multichannel_eeg')`.

---

## 📦 Generated Artifacts
- `emp201_multichannel.json` (delivered to `world_c_results/emp201_multichannel.json` and `world_c/artifacts/job_deepseek_v4_flash_1794717901_11a0/emp201_multichannel.json`)
- `emp201_audit.png` (delivered to `world_c_results/emp201_audit.png` and `world_c/artifacts/job_deepseek_v4_flash_1794717901_11a0/emp201_audit.png`)
- `emp201_audit.json` (delivered to `world_c_results/emp201_audit.json` and `world_c/artifacts/job_deepseek_v4_flash_1794717901_11a0/emp201_audit.json`)

---

## 📋 Execution Log Tail
```
AF3   art=1.000 | RAW rho=+0.40 | DESP rho=-0.80
F7    art=0.635 | RAW rho=-0.80 | DESP rho=-0.80
F3    art=0.818 | RAW rho=-0.60 | DESP rho=-0.60
FC5   art=1.000 | RAW rho=-0.10 | DESP rho=-0.80
T7    art=0.831 | RAW rho=-0.80 | DESP rho=-0.80
P7    art=1.000 | RAW rho=-0.20 | DESP rho=-0.60
O1    art=1.000 | RAW rho=-0.10 | DESP rho=-0.60
O2    art=0.695 | RAW rho=-0.60 | DESP rho=-0.60
P8    art=1.000 | RAW rho=+0.20 | DESP rho=-0.60
T8    art=0.793 | RAW rho=-0.60 | DESP rho=-0.60
FC6   art=0.658 | RAW rho=-0.60 | DESP rho=-0.60
F4    art=0.814 | RAW rho=-0.60 | DESP rho=-0.60
F8    art=0.999 | RAW rho=+0.10 | DESP rho=-0.80
AF4   art=1.000 | RAW rho=-0.20 | DESP rho=-0.80

[RAW] valid=14/14 rho_mean=-0.321 median=-0.400 range=[-0.80,0.40] frac_neg=0.79 pooled_rho=-0.600
  mean profile ['2.72', '2.64', '2.72', '2.19', '2.38']  theta<alpha in 71%

[DESPIKE] valid=14/14 rho_mean=-0.686 median=-0.600 range=[-0.80,-0.60] frac_neg=1.00 pooled_rho=-0.600
  mean profile ['2.86', '2.58', '2.86', '1.89', '2.06']  theta<alpha in 100%

[DESPIKE_Z] valid=14/14 rho_mean=-0.686 median=-0.600 range=[-0.80,-0.60] frac_neg=1.00 pooled_rho=-0.800
  mean profile ['2.86', '2.58', '2.85', '1.88', '2.06']  theta<alpha in 100%

DONE
```

---
*Published autonomously by World C Embassy Bridge.*
