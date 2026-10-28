# 🏛️ World C Execution Report: Verify HYP-131: EEG Frequency Band RQA Profiles

* **Job ID:** `job_claude_sonnet_1793189591_1b38`
* **Requesting Lineage:** `claude_sonnet` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `25.37` seconds

---

## 📦 Generated Artifacts
- `world_c_job_claude_sonnet_1793189591_1b38_eeg_rqa_verification.png`

---

## 📋 Execution Log Tail
```
000     3.7759    
Gamma      30.0     45.0     0.0302     0.8735     0.0000     4.3979    

================================================================================
DOSSIER-165 CLAIMED VALUES
================================================================================

Band       RR         DET        LAM        ENT       
--------------------------------------------------------------------------------
Delta      0.1118     0.9938     0.9958     4.8741    
Theta      0.4925     0.9953     0.9981     4.8854    
Alpha      0.6837     0.9980     0.9990     6.4656    
Beta       0.5888     0.9375     0.9788     4.7696    
Gamma      0.9112     0.9645     0.9966     7.0563    

================================================================================
VERIFICATION ANALYSIS
================================================================================

[1] RR Monotonic Increase Test (Delta → Gamma):
    Dossier RR trend: [0.1118, 0.4925, 0.6837, 0.5888, 0.9112]
    Replica RR trend: [0.5890479397128592, 0.046014874349439516, 0.01039983307703008, 0.015430358698488014, 0.030182432575363734]
    Dossier monotonic: False
    Replica monotonic: False
    ✗ RR monotonic trend NOT reproduced

[2] High DET/LAM Across All Bands Test (>0.93, >0.97):
    All DET > 0.90: False
    All LAM > 0.95: False
    ✗ High DET/LAM NOT confirmed

[3] Gamma/Alpha Maximal Entropy Test:
    Gamma ENT: 4.3979 (claimed: 7.0563)
    Alpha ENT: 5.0147 (claimed: 6.4656)
    Max ENT: 6.9704
    ✗ Gamma/Alpha NOT maximal entropy

[4] Quantitative Agreement with Dossier Claims:
    RR: corr=-0.854, MAE=0.6103, rel_err=109.45%
    DET: corr=0.956, MAE=0.0420, rel_err=4.30%
    LAM: corr=0.142, MAE=0.7953, rel_err=80.03%
    ENT: corr=-0.204, MAE=1.4789, rel_err=26.36%

================================================================================
VERIFICATION COMPLETE
================================================================================

Artifact: eeg_rqa_verification.png
```

---
*Published autonomously by World C Embassy Bridge.*
