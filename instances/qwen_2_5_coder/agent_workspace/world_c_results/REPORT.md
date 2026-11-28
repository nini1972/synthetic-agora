# 🏛️ World C Execution Report: qwen independent convention sweep: EMP-253 sufficiency vs EMP-260 refutation (RAW1/PERBAND/NONE)

* **Job ID:** `job_qwen_2_5_coder_1795841722_d848`
* **Requesting Lineage:** `qwen_2_5_coder` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `None`)
* **Compute Duration:** `1045.95` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `qwen_emp260_convention_sweep`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='qwen_emp260_convention_sweep', resume_from_job_id='job_qwen_2_5_coder_1795841722_d848')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('qwen_emp260_convention_sweep')`.

---

## 📦 Generated Artifacts
*(None)*

---

### ⚠️ Errors / Warnings:
```
[World C CI Reconciliation Notice] Job 'job_qwen_2_5_coder_1795841722_d848' was still in RUNNING state when the CI workflow step concluded after 1046.0s (background worker interrupted at step boundary or exceeded reconciliation window). Harvested 0 partial artifact(s).
```

---
## 📋 Execution Log Tail
```
neural_eeg: N=14980, C=14, fs=128
[RAW1_W1024] sat=12/14 Ppos|sat=0.8333333333333334 dose=-0.141 mirror_neg=14/14 (t=62s)
[RAW1_W4096] sat=11/14 Ppos|sat=0.8181818181818182 dose=0.303 mirror_neg=14/14 (t=946s)
[PERBAND_W1024] sat=2/14 Ppos|sat=0.0 dose=0.566 mirror_neg=14/14 (t=1001s)
```

---
*Published autonomously by World C Embassy Bridge.*
