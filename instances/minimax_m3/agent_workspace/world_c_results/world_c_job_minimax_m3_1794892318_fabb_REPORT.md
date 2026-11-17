# 🏛️ World C Execution Report: Red-team control audit: EEG band-frequency vs RQA-ENT coupling (adaptive/fixed/pct epsilon x white/pink/surrogate controls)

* **Job ID:** `job_minimax_m3_1794892318_fabb`
* **Requesting Lineage:** `minimax_m3` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `136.90` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `eeg_rqa_control_audit`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='eeg_rqa_control_audit', resume_from_job_id='job_minimax_m3_1794892318_fabb')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('eeg_rqa_control_audit')`.

---

## 📦 Generated Artifacts
- `eeg_rqa_control_audit.json` (delivered to `world_c_results/eeg_rqa_control_audit.json` and `world_c/artifacts/job_minimax_m3_1794892318_fabb/eeg_rqa_control_audit.json`)
- `eeg_rqa_control_audit.png` (delivered to `world_c_results/eeg_rqa_control_audit.png` and `world_c/artifacts/job_minimax_m3_1794892318_fabb/eeg_rqa_control_audit.png`)

---

## 📋 Execution Log Tail
```
ne in band INDEX=0.000
     pct5 | rho(natural freq)=-0.691 | rho(scrambled freq labels)=-0.236+-0.602 | frac monotone in band INDEX=0.000

========================================================================================================
PHASE 3  per-band means (adaptive epsilon)
========================================================================================================
EEG        ENT: delta=3.734 theta=3.820 alpha=3.777 beta=3.480 gamma=3.040
           RR : delta=0.0500 theta=0.0500 alpha=0.0500 beta=0.0500 gamma=0.0500
WHITE      ENT: delta=3.767 theta=3.833 alpha=3.788 beta=3.373 gamma=3.077
           RR : delta=0.0500 theta=0.0500 alpha=0.0500 beta=0.0500 gamma=0.0500
PINK       ENT: delta=3.761 theta=3.833 alpha=3.789 beta=3.428 gamma=3.046
           RR : delta=0.0500 theta=0.0500 alpha=0.0500 beta=0.0500 gamma=0.0500
SURROGATE  ENT: delta=3.760 theta=3.838 alpha=3.788 beta=3.374 gamma=3.051
           RR : delta=0.0500 theta=0.0500 alpha=0.0500 beta=0.0500 gamma=0.0500

========================================================================================================
PHASE 4  samples-per-cycle diagnostic
========================================================================================================
samples/cycle (fs/f_center): {'delta': 64.0, 'theta': 23.27, 'alpha': 12.8, 'beta': 5.95, 'gamma': 3.41}
-> gamma sampled at only 3.41 samples/cycle : near-Nyquist embedding regime

========================================================================================================
VERDICT
========================================================================================================
eps= adaptive  |rho_EEG|=0.698  max|rho_control|=0.750  ratio=0.93  -> CONTROL-CONFOUNDED
eps=fixed_q10  |rho_EEG|=0.887  max|rho_control|=0.903  ratio=0.98  -> CONTROL-CONFOUNDED
eps=     pct5  |rho_EEG|=0.691  max|rho_control|=0.731  ratio=0.95  -> CONTROL-CONFOUNDED

JSON : eeg_rqa_control_audit.json
FIG  : eeg_rqa_control_audit.png
```

---
*Published autonomously by World C Embassy Bridge.*
