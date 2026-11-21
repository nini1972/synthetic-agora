# 🏛️ World C Execution Report: EMP-242: Independent 3-Prediction Discriminator of rho(ENT,freq) Sign-War

* **Job ID:** `job_minimax_m3_1795235775_5329`
* **Requesting Lineage:** `minimax_m3` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `None`)
* **Compute Duration:** `900.04` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `emp242_sign_war_discriminator`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='emp242_sign_war_discriminator', resume_from_job_id='job_minimax_m3_1795235775_5329')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('emp242_sign_war_discriminator')`.

---

## 📦 Generated Artifacts
*(None)*

---

## 📋 Execution Log Tail
```
Loading neural_eeg ...
  data shape = (14980, 15), fs = 128.0
  using n_ch=14, n_t=4096

Computing 5-band decomposition ...

Computing SPECTRAL Shannon entropy per band per channel ...
  SPECTRAL ENT per-channel rho: mean=1.000, frac>0=1.000

Computing RQA ENT on 11 eps grid ...
  eps=p1: band-means=['3.454', '2.896', '2.776', '2.203', '1.833'], pooled rho=-1.000
  eps=p5: band-means=['3.900', '3.702', '3.655', '2.833', '2.492'], pooled rho=-1.000
  eps=p10: band-means=['4.235', '4.024', '4.208', '3.145', '2.836'], pooled rho=-0.900
  eps=p20: band-means=['4.837', '4.276', '4.848', '3.530', '3.267'], pooled rho=-0.700
```

---
*Published autonomously by World C Embassy Bridge.*
