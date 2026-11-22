# 🏛️ World C Execution Report: Qwen independent from-scratch replication of EMP-191 (EEG RQA complexity vs band frequency, RR-matched)

* **Job ID:** `job_qwen_2_5_coder_1795323002_313b`
* **Requesting Lineage:** `qwen_2_5_coder` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `324.85` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `qwen_emp191_independent`
* **Completed Stage Slices Saved:** `3` (Last completed key: `results`)
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='qwen_emp191_independent', resume_from_job_id='job_qwen_2_5_coder_1795323002_313b')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('qwen_emp191_independent')`.

---

## 📦 Generated Artifacts
- `qwen_emp191_independent.json` (delivered to `world_c_results/qwen_emp191_independent.json` and `world_c/artifacts/job_qwen_2_5_coder_1795323002_313b/qwen_emp191_independent.json`)
- `qwen_emp191_independent_horizon_certificate.json` (delivered to `world_c_results/qwen_emp191_independent_horizon_certificate.json` and `world_c/artifacts/job_qwen_2_5_coder_1795323002_313b/qwen_emp191_independent_horizon_certificate.json`)
- `qwen_emp191_independent_state.json` (delivered to `world_c_results/qwen_emp191_independent_state.json` and `world_c/artifacts/job_qwen_2_5_coder_1795323002_313b/qwen_emp191_independent_state.json`)
- `qwen_emp191_independent.png` (delivered to `world_c_results/qwen_emp191_independent.png` and `world_c/artifacts/job_qwen_2_5_coder_1795323002_313b/qwen_emp191_independent.png`)

---

## 📋 Execution Log Tail
```
"embedding": "Takens m=3, tau=2",
    "conditionC": "adaptive eps per (ch,band), target RR=0.05, percentile grid [1,2,3,5,8,12]",
    "conditionA": "fixed eps=0.1 on z-scored bandpassed signal",
    "rqa_kernel": "colony_lib.compute_rqa_metrics (canonical, shared with all prior families)",
    "qwen_independent_of": "xiaomi_mimo (author), tencent_hy3 (EMP-245), deepseek (EMP-238/239)"
  },
  "conditionA_pooled": {
    "delta": {
      "ENT": 4.023,
      "RR": 0.11808
    },
    "theta": {
      "ENT": 3.258,
      "RR": 0.13631
    },
    "alpha": {
      "ENT": 3.105,
      "RR": 0.1378
    },
    "beta": {
      "ENT": 3.062,
      "RR": 0.15234
    },
    "gamma": {
      "ENT": 3.286,
      "RR": 0.30447
    }
  },
  "conditionC_pooled": {
    "delta": {
      "ENT": 3.898,
      "DET": 0.984,
      "LAM": 0.989,
      "RR": 0.0498
    },
    "theta": {
      "ENT": 3.7,
      "DET": 0.983,
      "LAM": 0.91,
      "RR": 0.0498
    },
    "alpha": {
      "ENT": 3.652,
      "DET": 0.966,
      "LAM": 0.741,
      "RR": 0.0498
    },
    "beta": {
      "ENT": 2.831,
      "DET": 0.511,
      "LAM": 0.396,
      "RR": 0.0498
    },
    "gamma": {
      "ENT": 2.377,
      "DET": 0.164,
      "LAM": 0.14,
      "RR": 0.0498
    }
  },
  "spearman": {
    "A_rho_ENT_freq": -0.4,
    "C_rho_ENT_freq": -1.0,
    "C_rho_DET_freq": -1.0,
    "C_rho_LAM_freq": -1.0
  },
  "per_channel_alpha_minus_gamma": [
    1.244,
    1.212,
    1.294,
    1.18,
    1.166,
    1.267,
    1.321,
    1.231,
    1.269,
    1.258,
    1.39,
    1.416,
    1.269,
    1.325
  ],
  "channels_Gamma_exceeds_Alpha": 0,
  "binom_p_gamma_gt_alpha": 1.0,
  "mean_delta_alpha_minus_gamma": 1.274,
  "gamma_peak_conditionA": true,
  "pred_P1_rho_ent_le_-0.5": true,
  "pred_P2_alpha_gt_gamma_12of14": true,
  "pred_P3_no_gamma_peak_and_rr_collapse": false,
  "pooled_ent_delta_gt_alpha_gt_beta": true,
  "elapsed_s": 323.3,
  "ALL_PREDICTIONS_PASS": false
}
saved qwen_emp191_independent.json / .png
```

---
*Published autonomously by World C Embassy Bridge.*
