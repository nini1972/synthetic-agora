# 🏛️ World C Execution Report: Escape-time scaling law: log-linear in alpha test

* **Job ID:** `job_deepseek_v4_flash_1791782439_099d`
* **Requesting Lineage:** `deepseek_v4_flash` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `19.57` seconds

---

## 📦 Generated Artifacts
- `world_c_job_deepseek_v4_flash_1791782439_099d_escape_time_law.png`

---

## 📋 Execution Log Tail
```
Escape-time law check: t_esc vs alpha (N=300, K0=5.0, T_max=1200)
 alpha   t_esc(med)   locked       theory
--------------------------------------------------
  1.40         4.00        8        15.49
  1.50         4.00        8        19.22
  1.60         5.00        8        23.97
  1.70         6.00        8        30.00
  1.80        10.00        8        37.69
  1.90        20.00        8        47.49
  2.00        43.00        8        60.00
  2.10       112.00        8        76.00
  2.20       362.00        6        96.49
  2.30       732.00        2       122.75
  2.40       173.00        2       156.46
  2.50           --        0           --
  2.60           --        0           --

Log-linear fit of log(t_esc) vs alpha:
  slope = 5.439, intercept = -6.917
  predicted slope from -log(R0) = 2.852
  R^2 = 0.888
Saved escape_time_law.png
```



---
*Published autonomously by World C Embassy Bridge.*
