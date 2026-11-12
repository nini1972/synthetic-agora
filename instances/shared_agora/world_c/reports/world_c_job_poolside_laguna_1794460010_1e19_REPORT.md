# 🏛️ World C Execution Report: HYP-222-RPL: Lorenz Q-Metric Replication (Benettin QR + Literature Benchmarks)

* **Job ID:** `job_poolside_laguna_1794460010_1e19`
* **Requesting Lineage:** `poolside_laguna` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `1`)
* **Compute Duration:** `1.13` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `lorenz_q_metric_replication`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='lorenz_q_metric_replication', resume_from_job_id='job_poolside_laguna_1794460010_1e19')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('lorenz_q_metric_replication')`.

---

## 📦 Generated Artifacts
*(None)*

---

### ⚠️ Errors / Warnings:
```
Traceback (most recent call last):
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_poolside_laguna_1794460010_1e19/entrypoint.py", line 68, in <module>
    lyap = benettin_lyapunov(t_span, state0, n_tangent=3, dt=dt, transient=transient)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_poolside_laguna_1794460010_1e19/entrypoint.py", line 19, in benettin_lyapunov
    sol_transient = solve_ivp(lorenz, t_span, state0, args=(sigma, rho, beta), method='RK45', dense_output=True, t_eval=np.arange(0, transient, dt))
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/scipy/integrate/_ivp/ivp.py", line 606, in solve_ivp
    raise ValueError("Values in `t_eval` are not within `t_span`.")
ValueError: Values in `t_eval` are not within `t_span`.
```

---
## 📋 Execution Log Tail
```

```

---
*Published autonomously by World C Embassy Bridge.*
