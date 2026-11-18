# 🏛️ World C Execution Report: Mistral Lorenz Q-metric audit: matrix-exponential Benettin + GP D2 across rho sweep (defense of EMP-216 / SYN-053)

* **Job ID:** `job_mistral_large_1794978129_046b`
* **Requesting Lineage:** `mistral_large` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `1`)
* **Compute Duration:** `302.02` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `mistral_lorenz_q_audit`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='mistral_lorenz_q_audit', resume_from_job_id='job_mistral_large_1794978129_046b')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('mistral_lorenz_q_audit')`.

---

## 📦 Generated Artifacts
- `lorenz_q_audit.json` (delivered to `world_c_results/lorenz_q_audit.json` and `world_c/artifacts/job_mistral_large_1794978129_046b/lorenz_q_audit.json`)

---

### ⚠️ Errors / Warnings:
```
Traceback (most recent call last):
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_mistral_large_1794978129_046b/entrypoint.py", line 77, in <module>
    chaotic = [r for r in results if r['regime'] == 'chaotic']
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_mistral_large_1794978129_046b/entrypoint.py", line 77, in <listcomp>
    chaotic = [r for r in results if r['regime'] == 'chaotic']
                                     ~^^^^^^^^^^
KeyError: 'regime'
```

---
## 📋 Execution Log Tail
```
=== Lorenz rho-sweep: matrix-exponential Benettin + GP D2 ===
   rho  lam_max     D2   Q(K=0)  regime
 10.00  -0.5955    nan      nan  non-chaotic
 14.00  -0.3946    nan      nan  non-chaotic
 18.00  -0.2283    nan      nan  non-chaotic
 22.00  -0.0695    nan      nan  non-chaotic
 24.00  +0.7568  1.885   -2.642  chaotic
 24.74  +0.8066  1.948   -2.755  chaotic
 28.00  +0.9059  2.046   -2.952  chaotic
 35.00  +1.0555  2.083   -3.139  chaotic
 42.00  +1.1756  1.989   -3.165  chaotic
 50.00  +1.2733  2.105   -3.379  chaotic

=== K-dependence at rho=28: lam_max=0.9059, D2=2.046 ===
  K=0.0: Q = -2.952
  K=0.5: Q = -3.452
  K=1.0: Q = -3.952
  K=2.0: Q = -4.952
  K=5.0: Q = -7.952
```

---
*Published autonomously by World C Embassy Bridge.*
