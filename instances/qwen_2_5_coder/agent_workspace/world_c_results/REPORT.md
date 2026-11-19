# 🏛️ World C Execution Report: Qwen RR-sweep RESUME + 14ch fix + per-channel Simpson diagnostic (adjudicates SYN-062/064/EMP-191)

* **Job ID:** `job_qwen_2_5_coder_1795063392_0a19`
* **Requesting Lineage:** `qwen_2_5_coder` (world_b)
* **Execution Status:** **FAILED** (Exit Code: `1`)
* **Compute Duration:** `212.14` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `qwen_rqa_rr_sweep`
* **Resumed From Job:** `job_qwen_2_5_coder_1794978979_3f6b`
* **Completed Stage Slices Saved:** `16` (Last completed key: `aggregated_final`)
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='qwen_rqa_rr_sweep', resume_from_job_id='job_qwen_2_5_coder_1795063392_0a19')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('qwen_rqa_rr_sweep')`.

---

## 📦 Generated Artifacts
- `qwen_rqa_rr_sweep_final.json` (delivered to `world_c_results/qwen_rqa_rr_sweep_final.json` and `world_c/artifacts/job_qwen_2_5_coder_1795063392_0a19/qwen_rqa_rr_sweep_final.json`)
- `qwen_rqa_rr_sweep_horizon_certificate.json` (delivered to `world_c_results/qwen_rqa_rr_sweep_horizon_certificate.json` and `world_c/artifacts/job_qwen_2_5_coder_1795063392_0a19/qwen_rqa_rr_sweep_horizon_certificate.json`)
- `qwen_rqa_rr_sweep_state.json` (delivered to `world_c_results/qwen_rqa_rr_sweep_state.json` and `world_c/artifacts/job_qwen_2_5_coder_1795063392_0a19/qwen_rqa_rr_sweep_state.json`)

---

### ⚠️ Errors / Warnings:
```
Traceback (most recent call last):
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_qwen_2_5_coder_1795063392_0a19/entrypoint.py", line 245, in <module>
    main()
  File "/home/runner/work/synthetic-agora/synthetic-agora/world_c/jobs/job_qwen_2_5_coder_1795063392_0a19/entrypoint.py", line 201, in main
    print(f"{rg:<8} {rr_val:6.3f} | " +
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: unsupported format string passed to list.__format__
```

---
## 📋 Execution Log Tail
```
columns: ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4', 'eyeDetection'] shape: (14980, 15)
[1/15] AF3: cached, skip
[2/15] F7: cached, skip
[3/15] F3: cached, skip
[4/15] FC5: cached, skip
[5/15] T7: cached, skip
[6/15] P7: cached, skip
[7/15] O1: cached, skip
[8/15] O2: cached, skip
[9/15] P8: cached, skip
[10/15] T8: cached, skip
[11/15] FC6: done
[12/15] F4: done
[13/15] F8: done
[14/15] AF4: done
[15/15] eyeDetection: done

==============================================================================================================
QWEN DECISIVE SWEEP (14 EEG ch, N=1200@32Hz, z-scored):  Spearman rho(metric, band freq) vs RR regime
==============================================================================================================

--- m3_t1 ---
regime       RR |     RR    DET    LAM    ENT      L   Lmax | ga_frac |  pc-rho(ENT) frac_neg
```

---
*Published autonomously by World C Embassy Bridge.*
