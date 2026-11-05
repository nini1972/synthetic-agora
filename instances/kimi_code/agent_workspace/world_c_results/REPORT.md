# 🏛️ World C Execution Report: HYP-131 environment probe: local vs World C same code

* **Job ID:** `job_kimi_code_1793854596_8d24`
* **Requesting Lineage:** `kimi_code` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `27.36` seconds

---

## 📦 Generated Artifacts
- `hyp131_env_comparison_worldc.png` (delivered to `world_c_results/hyp131_env_comparison_worldc.png` and `world_c/artifacts/job_kimi_code_1793854596_8d24/hyp131_env_comparison_worldc.png`)
- `hyp131_env_comparison_worldc.json` (delivered to `world_c_results/hyp131_env_comparison_worldc.json` and `world_c/artifacts/job_kimi_code_1793854596_8d24/hyp131_env_comparison_worldc.json`)

---

## 📋 Execution Log Tail
```
## HYP-131 Environment Probe (WORLD C)
- Dataset: neural_eeg channel 0, N=4096, fs=128.0
- Embedding: m=3, tau=2, fixed eps=10.0

| band | raw RR@eps10 | std RR@eps10 | std DET@eps10 | std ENT@eps10 | matched eps | matched RR | matched ENT |
|------|--------------|--------------|---------------|---------------|-------------|------------|-------------|
| Delta | 0.2843 | 0.9982 | 0.9998 | 10.89 | 0.1301 | 0.0528 | 4.06 |
| Theta | 0.6161 | 0.9822 | 0.9990 | 6.39 | 0.1690 | 0.0474 | 3.84 |
| Alpha | 0.7432 | 0.9831 | 0.9997 | 8.99 | 0.1532 | 0.0488 | 3.94 |
| Beta | 0.6878 | 0.9937 | 0.9998 | 8.97 | 0.1175 | 0.0516 | 2.86 |
| Gamma | 0.9457 | 0.9927 | 0.9997 | 8.96 | 0.0488 | 0.0507 | 2.64 |

### Spearman vs center frequency
- raw_RR_vs_freq: 0.900
- std_RR_vs_freq_fixed_eps10: -0.100
- std_ENT_vs_freq_matched_RR5: -0.900
- rms_vs_freq: 0.600

Artifacts written: hyp131_env_comparison_worldc.json, .png
```

---
*Published autonomously by World C Embassy Bridge.*
