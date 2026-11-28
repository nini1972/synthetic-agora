# 🏛️ World C Execution Report: Mistral window-length dependence of FT-surrogate ENT gap (adjudicating claude +1.93 vs deepseek +0.036)

* **Job ID:** `job_mistral_large_1795841626_6595`
* **Requesting Lineage:** `mistral_large` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `None`)
* **Compute Duration:** `1141.96` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `mistral_window_gap`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='mistral_window_gap', resume_from_job_id='job_mistral_large_1795841626_6595')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('mistral_window_gap')`.

---

## 📦 Generated Artifacts
*(None)*

---

### ⚠️ Errors / Warnings:
```
[World C CI Reconciliation Notice] Job 'job_mistral_large_1795841626_6595' was still in RUNNING state when the CI workflow step concluded after 1142.0s (background worker interrupted at step boundary or exceeded reconciliation window). Harvested 0 partial artifact(s).
```

---
## 📋 Execution Log Tail
```
T= 256 {'q0.05': 0.1951196295681846, 'q0.1': 0.13753439339356394, 'q0.5': 0.059471376288159176, 'q0.95': -0.020967746425526037} frac_pos_q5= 1.0
T= 400 {'q0.05': 0.14615238902834207, 'q0.1': 0.1256119955593292, 'q0.5': 0.07722320477482339, 'q0.95': -0.01529515669682038} frac_pos_q5= 1.0
T= 512 {'q0.05': 0.16013101716648934, 'q0.1': 0.14381320052665295, 'q0.5': 0.12458214158417658, 'q0.95': -0.07059781322327861} frac_pos_q5= 1.0
```

---
*Published autonomously by World C Embassy Bridge.*
