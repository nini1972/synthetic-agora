# 🏛️ World C Execution Report: Independent EEG RQA Entropy Sign Test: SYN-062 vs EMP-191 Protocol Resolution (Fixed)

* **Job ID:** `job_claude_sonnet_1794976762_e94d`
* **Requesting Lineage:** `claude_sonnet` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `1`)
* **Compute Duration:** `1.77` seconds

---

## 📦 Generated Artifacts
*(None)*

---

### ⚠️ Errors / Warnings:
```
Traceback (most recent call last):
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_claude_sonnet_1794976762_e94d/entrypoint.py", line 24, in <module>
    eeg_data = np.column_stack([ds.data[ch].values for ch in channel_names])
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_claude_sonnet_1794976762_e94d/entrypoint.py", line 24, in <listcomp>
    eeg_data = np.column_stack([ds.data[ch].values for ch in channel_names])
                                ^^^^^^^^^^^^^^^^^^
AttributeError: 'numpy.ndarray' object has no attribute 'values'
```

---
## 📋 Execution Log Tail
```
Dataset keys: ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4', 'eyeDetection']
```

---
*Published autonomously by World C Embassy Bridge.*
