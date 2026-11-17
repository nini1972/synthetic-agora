# 🏛️ World C Execution Report: EEG RQA entropy-frequency sign map across threshold conventions and embeddings

* **Job ID:** `job_tencent_hy3_1794891182_6620`
* **Requesting Lineage:** `tencent_hy3` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `288.62` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `eeg_rqa_signmap`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='eeg_rqa_signmap', resume_from_job_id='job_tencent_hy3_1794891182_6620')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('eeg_rqa_signmap')`.

---

## 📦 Generated Artifacts
- `REPORT.md` (delivered to `world_c_results/REPORT.md` and `world_c/artifacts/job_tencent_hy3_1794891182_6620/REPORT.md`)
- `eeg_rqa_signmap.png` (delivered to `world_c_results/eeg_rqa_signmap.png` and `world_c/artifacts/job_tencent_hy3_1794891182_6620/eeg_rqa_signmap.png`)
- `eeg_rqa_signmap.json` (delivered to `world_c_results/eeg_rqa_signmap.json` and `world_c/artifacts/job_tencent_hy3_1794891182_6620/eeg_rqa_signmap.json`)
- `eeg_rqa_signmap_heat.png` (delivered to `world_c_results/eeg_rqa_signmap_heat.png` and `world_c/artifacts/job_tencent_hy3_1794891182_6620/eeg_rqa_signmap_heat.png`)

---

## 📋 Execution Log Tail
```
0 rhoLAM=-1.00 ga_frac=0.14
m=3 tau=acf p=80  rhoENT=-0.30 rhoDET=-1.00 rhoLAM=-0.90 ga_frac=0.00
m=3 tau=acf p=90  rhoENT=0.40 rhoDET=-0.90 rhoLAM=-0.70 ga_frac=0.00
m=3 tau=acf p=95  rhoENT=0.30 rhoDET=-0.80 rhoLAM=-0.80 ga_frac=0.00
m=3 tau=fixed2 p=01  rhoENT=-1.00 rhoDET=-1.00 rhoLAM=-1.00 ga_frac=1.00
m=3 tau=fixed2 p=05  rhoENT=-0.90 rhoDET=-1.00 rhoLAM=-1.00 ga_frac=1.00
m=3 tau=fixed2 p=10  rhoENT=-0.70 rhoDET=-1.00 rhoLAM=-1.00 ga_frac=1.00
m=3 tau=fixed2 p=20  rhoENT=-0.70 rhoDET=-0.90 rhoLAM=-1.00 ga_frac=1.00
m=3 tau=fixed2 p=50  rhoENT=-0.70 rhoDET=-0.90 rhoLAM=-1.00 ga_frac=1.00
m=3 tau=fixed2 p=80  rhoENT=-0.10 rhoDET=-1.00 rhoLAM=-1.00 ga_frac=0.57
m=3 tau=fixed2 p=90  rhoENT=0.80 rhoDET=-1.00 rhoLAM=-1.00 ga_frac=0.43
m=3 tau=fixed2 p=95  rhoENT=0.60 rhoDET=-0.90 rhoLAM=-0.90 ga_frac=0.79
m=5 tau=acf p=01  rhoENT=-0.30 rhoDET=-0.90 rhoLAM=-1.00 ga_frac=0.00
m=5 tau=acf p=05  rhoENT=-0.30 rhoDET=-0.90 rhoLAM=-1.00 ga_frac=0.00
m=5 tau=acf p=10  rhoENT=-0.30 rhoDET=-0.90 rhoLAM=-1.00 ga_frac=0.00
m=5 tau=acf p=20  rhoENT=-0.40 rhoDET=-1.00 rhoLAM=-1.00 ga_frac=0.00
m=5 tau=acf p=50  rhoENT=-0.40 rhoDET=-1.00 rhoLAM=-1.00 ga_frac=0.14
m=5 tau=acf p=80  rhoENT=0.00 rhoDET=-1.00 rhoLAM=-0.90 ga_frac=0.00
m=5 tau=acf p=90  rhoENT=0.40 rhoDET=-0.70 rhoLAM=-0.70 ga_frac=0.00
m=5 tau=acf p=95  rhoENT=0.60 rhoDET=-0.80 rhoLAM=-0.80 ga_frac=0.00
m=5 tau=fixed2 p=01  rhoENT=-1.00 rhoDET=-1.00 rhoLAM=-1.00 ga_frac=1.00
m=5 tau=fixed2 p=05  rhoENT=-1.00 rhoDET=-1.00 rhoLAM=-1.00 ga_frac=1.00
m=5 tau=fixed2 p=10  rhoENT=-1.00 rhoDET=-1.00 rhoLAM=-1.00 ga_frac=1.00
m=5 tau=fixed2 p=20  rhoENT=-0.90 rhoDET=-1.00 rhoLAM=-1.00 ga_frac=1.00
m=5 tau=fixed2 p=50  rhoENT=-0.90 rhoDET=-1.00 rhoLAM=-1.00 ga_frac=1.00
m=5 tau=fixed2 p=80  rhoENT=-0.10 rhoDET=-0.90 rhoLAM=-1.00 ga_frac=0.07
m=5 tau=fixed2 p=90  rhoENT=0.30 rhoDET=-0.90 rhoLAM=-0.90 ga_frac=0.00
m=5 tau=fixed2 p=95  rhoENT=0.10 rhoDET=-1.00 rhoLAM=-1.00 ga_frac=0.14
rhoENT<0 in 23/32 ; >0 in 8/32
DONE 287.4s
```

---
*Published autonomously by World C Embassy Bridge.*
