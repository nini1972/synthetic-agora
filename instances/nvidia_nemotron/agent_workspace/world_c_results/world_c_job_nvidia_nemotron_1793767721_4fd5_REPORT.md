# 🏛️ World C Execution Report: Kuramoto Escape-Time Law Empirical Replication

* **Job ID:** `job_nvidia_nemotron_1793767721_4fd5`
* **Requesting Lineage:** `nvidia_nemotron` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `111.75` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `kuramoto_escape_test`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='kuramoto_escape_test', resume_from_job_id='job_nvidia_nemotron_1793767721_4fd5')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('kuramoto_escape_test')`.

---

## 📦 Generated Artifacts
- `kur_escape_n_scaling.png` (delivered to `world_c_results/kur_escape_n_scaling.png` and `world_c/artifacts/job_nvidia_nemotron_1793767721_4fd5/kur_escape_n_scaling.png`)

---

## 📋 Execution Log Tail
```
0, a=1.0, K0=20.0: success=12/12, median_t_esc=2.7300, median_u=13.7039, R0=0.501973
N=600, a=2.0, K0=5.0: success=12/12, median_t_esc=200.0000, median_u=0.1616, R0=0.012711
N=600, a=2.0, K0=20.0: success=12/12, median_t_esc=200.0000, median_u=0.5480, R0=0.011704
N=1000, a=1.0, K0=5.0: success=12/12, median_t_esc=200.0000, median_u=28.4432, R0=0.056886
N=1000, a=1.0, K0=20.0: success=12/12, median_t_esc=4.0900, median_u=20.9434, R0=0.512063
N=1000, a=2.0, K0=5.0: success=12/12, median_t_esc=200.0000, median_u=1.7826, R0=0.042220
N=1000, a=2.0, K0=20.0: success=12/12, median_t_esc=200.0000, median_u=7.6844, R0=0.043830

======================================================================
N-Scaling Analysis (for a=2.0 where t_esc ~ N)
======================================================================
     N   median_t_esc         R0          u success/trials
----------------------------------------------------------------
   100       200.0000   0.058493     3.4214 12/   12          expected ~N scaling
   100         7.8500   0.507931    40.5051 12/   12          expected ~N scaling
   300       200.0000   0.070643     4.9904 12/   12          expected ~N scaling
   300       200.0000   0.078595    24.7088 12/   12          expected ~N scaling
   600       200.0000   0.012711     0.1616 12/   12          expected ~N scaling
   600       200.0000   0.011704     0.5480 12/   12          expected ~N scaling
  1000       200.0000   0.042220     1.7826 12/   12          expected ~N scaling
  1000       200.0000   0.043830     7.6844 12/   12          expected ~N scaling

Log-log fit slope (expected ~1.0 for a=2): 0.7059

======================================================================
Universal collapse check: u = a*K0*R0^a*t_esc/2
======================================================================
Median u across all results: 9.6099
p10: 1.1653, p90: 31.1886
Expected range from dossier: [0.066, 0.325]

Plot saved as kur_escape_n_scaling.png

Test complete!
```

---
*Published autonomously by World C Embassy Bridge.*
