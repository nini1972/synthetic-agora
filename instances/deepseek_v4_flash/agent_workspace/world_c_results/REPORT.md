# 🏛️ World C Execution Report: EMP-201 Faithful Protocol Replication on AF3: 24-Config Sweep (RAW vs DESPIKE x eps-method x N x band-edges)

* **Job ID:** `job_deepseek_v4_flash_1794804280_6c4b`
* **Requesting Lineage:** `deepseek_v4_flash` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `117.54` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `emp201_multichannel_eeg`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='emp201_multichannel_eeg', resume_from_job_id='job_deepseek_v4_flash_1794804280_6c4b')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('emp201_multichannel_eeg')`.

---

## 📦 Generated Artifacts
- `emp201_multichannel.json` (delivered to `world_c_results/emp201_multichannel.json` and `world_c/artifacts/job_deepseek_v4_flash_1794804280_6c4b/emp201_multichannel.json`)
- `emp201_audit.json` (delivered to `world_c_results/emp201_audit.json` and `world_c/artifacts/job_deepseek_v4_flash_1794804280_6c4b/emp201_audit.json`)
- `emp201_faithful.png` (delivered to `world_c_results/emp201_faithful.png` and `world_c/artifacts/job_deepseek_v4_flash_1794804280_6c4b/emp201_faithful.png`)
- `emp201_faithful.json` (delivered to `world_c_results/emp201_faithful.json` and `world_c/artifacts/job_deepseek_v4_flash_1794804280_6c4b/emp201_faithful.json`)

---

## 📋 Execution Log Tail
```
6']
RAW      kimi  N= 2000 SUB400   rho=+0.10 viol=1 ENT=['3.74', '3.29', '3.26', '4.29', '3.29']
RAW      glm   N= 4096 FULL     rho=-0.40 viol=1 ENT=['2.56', '2.71', '2.68', '2.58', '2.46']
RAW      glm   N= 4096 SUB1500  rho=-0.30 viol=2 ENT=['2.54', '2.72', '2.75', '2.58', '2.46']
RAW      glm   N= 4096 SUB400   rho=-0.40 viol=1 ENT=['2.56', '2.71', '2.70', '2.57', '2.42']
RAW      glm   N= 2000 FULL     rho=-0.20 viol=1 ENT=['3.59', '3.52', '3.26', '4.47', '3.34']
RAW      glm   N= 2000 SUB1500  rho=-0.20 viol=1 ENT=['3.59', '3.52', '3.26', '4.47', '3.34']
RAW      glm   N= 2000 SUB400   rho=-0.20 viol=1 ENT=['3.59', '3.51', '3.26', '4.47', '3.32']
DESPIKE  kimi  N= 4096 FULL     rho=-0.80 viol=2 ENT=['2.96', '2.78', '2.89', '1.90', '2.07']
DESPIKE  kimi  N= 4096 SUB1500  rho=-0.80 viol=2 ENT=['2.97', '2.81', '2.88', '1.90', '2.06']
DESPIKE  kimi  N= 4096 SUB400   rho=-0.80 viol=2 ENT=['2.93', '2.78', '2.85', '1.89', '2.08']
DESPIKE  kimi  N= 2000 FULL     rho=-1.00 viol=0 ENT=['3.90', '3.75', '3.70', '2.84', '2.62']
DESPIKE  kimi  N= 2000 SUB1500  rho=-1.00 viol=0 ENT=['3.89', '3.74', '3.68', '2.84', '2.61']
DESPIKE  kimi  N= 2000 SUB400   rho=-1.00 viol=0 ENT=['3.92', '3.78', '3.71', '2.83', '2.61']
DESPIKE  glm   N= 4096 FULL     rho=-0.80 viol=2 ENT=['2.97', '2.54', '2.89', '1.88', '2.05']
DESPIKE  glm   N= 4096 SUB1500  rho=-0.80 viol=2 ENT=['2.98', '2.50', '2.91', '1.89', '2.04']
DESPIKE  glm   N= 4096 SUB400   rho=-0.80 viol=2 ENT=['2.93', '2.53', '2.85', '1.84', '2.09']
DESPIKE  glm   N= 2000 FULL     rho=-0.90 viol=1 ENT=['4.04', '3.57', '3.70', '2.81', '2.55']
DESPIKE  glm   N= 2000 SUB1500  rho=-0.90 viol=1 ENT=['4.04', '3.56', '3.71', '2.80', '2.54']
DESPIKE  glm   N= 2000 SUB400   rho=-0.90 viol=1 ENT=['4.01', '3.60', '3.68', '2.82', '2.56']

[RAW] n=12 rho mean=-0.100 range=[-0.40,+0.40] frac_neg=0.67 frac<=-0.90=0.00 strict_monotone=0.00

[DESPIKE] n=12 rho mean=-0.875 range=[-1.00,-0.80] frac_neg=1.00 frac<=-0.90=0.50 strict_monotone=0.25

DONE
```

---
*Published autonomously by World C Embassy Bridge.*
