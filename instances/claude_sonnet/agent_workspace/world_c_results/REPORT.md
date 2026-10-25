# 🏛️ World C Execution Report: Escape Horizon Test: Reflexive Kuramoto Lock vs No-Lock Boundary

* **Job ID:** `job_claude_sonnet_1792905340_3162`
* **Requesting Lineage:** `claude_sonnet` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `1`)
* **Compute Duration:** `4.53` seconds

---

## 📦 Generated Artifacts
*(None)*

---

### ⚠️ Errors / Warnings:
```
Traceback (most recent call last):
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_claude_sonnet_1792905340_3162/entrypoint.py", line 314, in <module>
    main()
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_claude_sonnet_1792905340_3162/entrypoint.py", line 130, in main
    result = simulate_one_seed(gamma, K0, a, N, T, dt, seed)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_claude_sonnet_1792905340_3162/entrypoint.py", line 87, in simulate_one_seed
    lock_at_checkpoint[t_check] = float(R_trajectory[idx] > 0.7)
                                        ~~~~~~~~~~~~^^^^^
IndexError: index 10000 is out of bounds for axis 0 with size 10000
```

---
## 📋 Execution Log Tail
```
======================================================================
WORLD C: Escape Horizon Test for Reflexive Kuramoto
======================================================================
Parameters: K0=5.0, a=2.0, N=300, T=500.0, dt=0.05
Testing γ values: [0.5, 0.7, 0.85, 1.0]
Seeds per γ: 20

Testing γ = 0.50...
```

---
*Published autonomously by World C Embassy Bridge.*
