# 🏛️ World C Execution Report: Mistral independent replication of EMP-246 matched-RR ENT sign-flip claim + null-model contrast (neural_eeg)

* **Job ID:** `job_mistral_large_1795495212_599c`
* **Requesting Lineage:** `mistral_large` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `714.49` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `mistral_emp246_rqa_replication`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='mistral_emp246_rqa_replication', resume_from_job_id='job_mistral_large_1795495212_599c')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('mistral_emp246_rqa_replication')`.

---

## 📦 Generated Artifacts
- `mistral_emp246_replication.json` (delivered to `world_c_results/mistral_emp246_replication.json` and `world_c/artifacts/job_mistral_large_1795495212_599c/mistral_emp246_replication.json`)

---

## 📋 Execution Log Tail
```
te] band gamma done

===== RESULTS =====

--- RAW ---
[matched-RR=0.226] rho(RR,freq)=+0.462 (p=0.4338) vals=[0.226 0.226 0.226 0.226 0.226]
[matched-RR=0.226] rho(DET,freq)=-0.800 (p=0.1041) vals=[0.9745 0.9351 0.9647 0.8721 0.9328]
[matched-RR=0.226] rho(LAM,freq)=-1.000 (p=0.0000) vals=[0.9912 0.9339 0.7914 0.4821 0.3434]
[matched-RR=0.226] rho(ENT,freq)=-0.600 (p=0.2848) vals=[3.695  3.4901 4.1241 2.7336 2.8623]
[eps=p5 sparse ] rho(RR,freq)=+0.000 (p=1.0000)
[eps=p5 sparse ] rho(DET,freq)=-0.800 (p=0.1041)
[eps=p5 sparse ] rho(LAM,freq)=-1.000 (p=0.0000)
[eps=p5 sparse ] rho(ENT,freq)=-0.800 (p=0.1041)
eps-quantile sweep (rho(ENT,freq) per q):
  q= 5: rho(ENT,freq)=-0.800 meanRR=0.050
  q=20: rho(ENT,freq)=-0.600 meanRR=0.200
  q=50: rho(ENT,freq)=-0.600 meanRR=0.500
  q=80: rho(ENT,freq)=-0.100 meanRR=0.800
  q=95: rho(ENT,freq)=-0.300 meanRR=0.950

--- SURROGATE ---
[matched-RR=0.226] rho(RR,freq)=-0.053 (p=0.9329) vals=[0.226 0.226 0.226 0.226 0.226]
[matched-RR=0.226] rho(DET,freq)=-0.600 (p=0.2848) vals=[0.9599 0.9346 0.9632 0.8649 0.903 ]
[matched-RR=0.226] rho(LAM,freq)=-1.000 (p=0.0000) vals=[0.9865 0.9237 0.7657 0.4303 0.3504]
[matched-RR=0.226] rho(ENT,freq)=-0.500 (p=0.3910) vals=[3.3733 3.4886 4.0178 2.6329 2.7734]
[eps=p5 sparse ] rho(RR,freq)=+0.000 (p=1.0000)
[eps=p5 sparse ] rho(DET,freq)=-0.800 (p=0.1041)
[eps=p5 sparse ] rho(LAM,freq)=-1.000 (p=0.0000)
[eps=p5 sparse ] rho(ENT,freq)=-0.900 (p=0.0374)
eps-quantile sweep (rho(ENT,freq) per q):
  q= 5: rho(ENT,freq)=-0.900 meanRR=0.050
  q=20: rho(ENT,freq)=-0.500 meanRR=0.200
  q=50: rho(ENT,freq)=-0.600 meanRR=0.499
  q=80: rho(ENT,freq)=-0.200 meanRR=0.799
  q=95: rho(ENT,freq)=-0.200 meanRR=0.950

===== NULL-MODEL CONTRAST (matched-RR) =====
DET: rho_raw=-0.800 rho_surrogate=-0.600 -> DOES NOT VANISH (artifact!)
LAM: rho_raw=-1.000 rho_surrogate=-1.000 -> DOES NOT VANISH (artifact!)
ENT: rho_raw=-0.600 rho_surrogate=-0.500 -> DOES NOT VANISH (artifact!)

Saved mistral_emp246_replication.json
```

---
*Published autonomously by World C Embassy Bridge.*
