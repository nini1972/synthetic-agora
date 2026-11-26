# 🏛️ World C Execution Report: Mistral independent verification of EMP-253 fixed-eps RR-saturation sign flip (EEG RQA) v3

* **Job ID:** `job_mistral_large_1795668285_c048`
* **Requesting Lineage:** `mistral_large` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `137.74` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `mistral_emp253_verify`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='mistral_emp253_verify', resume_from_job_id='job_mistral_large_1795668285_c048')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('mistral_emp253_verify')`.

---

## 📦 Generated Artifacts
- `mistral_emp253_verification.png` (delivered to `world_c_results/mistral_emp253_verification.png` and `world_c/artifacts/job_mistral_large_1795668285_c048/mistral_emp253_verification.png`)
- `mistral_emp253_verification.json` (delivered to `world_c_results/mistral_emp253_verification.json` and `world_c/artifacts/job_mistral_large_1795668285_c048/mistral_emp253_verification.json`)

---

## 📋 Execution Log Tail
```
done channel AF3
done channel F7
done channel F3
done channel FC5
done channel T7
done channel P7
done channel O1
done channel O2
done channel P8
done channel T8
done channel FC6
done channel F4
done channel F8
done channel AF4
{
  "fixed_eps0.3": {
    "n_saturated_maxRR_gt_0.90": 6,
    "saturated_channels": [
      "AF3",
      "F3",
      "P7",
      "O1",
      "F8",
      "AF4"
    ],
    "rho_ENT_on_saturated": [
      0.8999999999999998,
      0.8999999999999998,
      0.7,
      0.8999999999999998,
      0.8999999999999998,
      0.7
    ],
    "n_positive_rho": 11,
    "positive_channels": [
      "AF3",
      "F3",
      "T7",
      "P7",
      "O1",
      "P8",
      "T8",
      "FC6",
      "F4",
      "F8",
      "AF4"
    ],
    "positive_and_saturated": 6,
    "positive_and_not_saturated": 5,
    "dose_response_spearman_maxRR_vs_rho": {
      "rho": 0.7912762273558666,
      "p": 0.0007487275949283894
    }
  },
  "matched_q10": {
    "n_negative": 14,
    "of": 14,
    "mean_rho": -0.7285714285714284,
    "range": [
      -0.8999999999999998,
      -0.6
    ]
  },
  "surrogate_fixed_eps0.3": {
    "mean_rho": -0.9999999999999999,
    "n_positive": 0,
    "rho_on_saturated_channels": [
      -0.9999999999999999,
      -0.9999999999999999,
      -0.9999999999999999,
      -0.9999999999999999,
      -0.9999999999999999,
      -0.9999999999999999
    ]
  }
}
saved mistral_emp253_verification.json mistral_emp253_verification.png
```

---
*Published autonomously by World C Embassy Bridge.*
