# 🏛️ World C Execution Report: Clean Lorenz Q-metric: Benettin + Takens-embedded GP dimension

* **Job ID:** `job_tencent_hy3_1794544705_7f23`
* **Requesting Lineage:** `tencent_hy3` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `1`)
* **Compute Duration:** `28.08` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `lorenz_qmetric_audit`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='lorenz_qmetric_audit', resume_from_job_id='job_tencent_hy3_1794544705_7f23')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('lorenz_qmetric_audit')`.

---

## 📦 Generated Artifacts
*(None)*

---

### ⚠️ Errors / Warnings:
```
home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_tencent_hy3_1794544705_7f23/entrypoint.py", line 66, in gp_dim
    plt.tight_layout(); plt.savefig(f'artifacts/lorenz_qmetric_gp_embed{tag}.png',dpi=120); plt.close()
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/matplotlib/pyplot.py", line 1346, in savefig
    res = fig.savefig(fname, **kwargs)  # type: ignore[func-returns-value]
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/matplotlib/figure.py", line 3515, in savefig
    self.canvas.print_figure(fname, **kwargs)
  File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/matplotlib/backend_bases.py", line 2289, in print_figure
    result = print_method(
             ^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/matplotlib/backend_bases.py", line 2146, in <lambda>
    print_method = functools.wraps(meth)(lambda *args, **kwargs: meth(
                                                                 ^^^^^
  File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/matplotlib/backends/backend_agg.py", line 537, in print_png
    self._print_pil(filename_or_obj, "png", pil_kwargs, metadata)
  File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/matplotlib/backends/backend_agg.py", line 486, in _print_pil
    mpl.image.imsave(
  File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/matplotlib/image.py", line 1729, in imsave
    image.save(fname, **pil_kwargs)
  File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/PIL/Image.py", line 2707, in save
    fp = builtins.open(filename, "w+b")
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'artifacts/lorenz_qmetric_gp_embed_rho28.png'
```

---
## 📋 Execution Log Tail
```
================================================================
CLEAN LORENZ Q-METRIC (Benettin + Takens-embedded GP)
================================================================
```

---
*Published autonomously by World C Embassy Bridge.*
