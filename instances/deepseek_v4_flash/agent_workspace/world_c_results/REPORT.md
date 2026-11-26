# 🏛️ World C Execution Report: EMP-238 self-correction + FT-surrogate control: is the RQA-ENT band ordering nonlinear information?

* **Job ID:** `job_deepseek_v4_flash_1795668150_a81e`
* **Requesting Lineage:** `deepseek_v4_flash` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `86.95` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `emp238_saturation_discriminator`
* **Completed Stage Slices Saved:** `15` (Last completed key: `final`)
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='emp238_saturation_discriminator', resume_from_job_id='job_deepseek_v4_flash_1795668150_a81e')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('emp238_saturation_discriminator')`.

---

## 📦 Generated Artifacts
- `emp238_saturation_discriminator.json` (delivered to `world_c_results/emp238_saturation_discriminator.json` and `world_c/artifacts/job_deepseek_v4_flash_1795668150_a81e/emp238_saturation_discriminator.json`)
- `emp238_surrogate_correction.json` (delivered to `world_c_results/emp238_surrogate_correction.json` and `world_c/artifacts/job_deepseek_v4_flash_1795668150_a81e/emp238_surrogate_correction.json`)
- `emp238_saturation_discriminator_horizon_certificate.json` (delivered to `world_c_results/emp238_saturation_discriminator_horizon_certificate.json` and `world_c/artifacts/job_deepseek_v4_flash_1795668150_a81e/emp238_saturation_discriminator_horizon_certificate.json`)
- `emp238_saturation_discriminator_state.json` (delivered to `world_c_results/emp238_saturation_discriminator_state.json` and `world_c/artifacts/job_deepseek_v4_flash_1795668150_a81e/emp238_saturation_discriminator_state.json`)

---

## 📋 Execution Log Tail
```
[CONTROL] logistic_r3.9      RR=0.050 gap=+1.870 z=+8.50
[CONTROL] AR1_a0.95          RR=0.050 gap=+0.090 z=+1.03
[CONTROL] narrowband_sine    RR=0.050 gap=-0.006 z=-0.06
[EEG] ch 0 rho_real=-1.00 rho_surr=-0.90 gap_p5=+0.096
[EEG] ch 1 rho_real=-1.00 rho_surr=-1.00 gap_p5=+0.128
[EEG] ch 2 rho_real=-1.00 rho_surr=-1.00 gap_p5=-0.010
[EEG] ch 3 rho_real=-1.00 rho_surr=-1.00 gap_p5=-0.074
[EEG] ch 4 rho_real=-1.00 rho_surr=-0.90 gap_p5=+0.092
[EEG] ch 5 rho_real=-1.00 rho_surr=-1.00 gap_p5=+0.095
[EEG] ch 6 rho_real=-1.00 rho_surr=-0.90 gap_p5=+0.106
[EEG] ch 7 rho_real=-0.90 rho_surr=-1.00 gap_p5=-0.063
[EEG] ch 8 rho_real=-0.90 rho_surr=-0.70 gap_p5=+0.036
[EEG] ch 9 rho_real=-1.00 rho_surr=-0.90 gap_p5=-0.029
[EEG] ch10 rho_real=-0.90 rho_surr=-0.90 gap_p5=-0.045
[EEG] ch11 rho_real=-0.90 rho_surr=-0.70 gap_p5=+0.054
[EEG] ch12 rho_real=-0.90 rho_surr=-0.70 gap_p5=-0.004
[EEG] ch13 rho_real=-0.90 rho_surr=-1.00 gap_p5=+0.030
[EEG SUMMARY] rho_real=-0.957 rho_surr=-0.900 Wilcoxon p=0.057
[EEG SUMMARY] mean_gap=+0.030 mean_z=+0.28 frac(gap>0.5)=0.00
SAVED
```

---
*Published autonomously by World C Embassy Bridge.*
