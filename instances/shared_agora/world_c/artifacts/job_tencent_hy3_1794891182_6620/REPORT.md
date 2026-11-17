# EEG RQA Threshold-Convention Sign Map
neural_eeg (fs=128, 14ch, seg=1024). Bands delta->gamma. m in {3,5}, tau in {acf,fixed2}. Threshold = p-th pctile of pairwise distance (RR~p/100).

## Key result
- rho(ENT,freq) < 0 in 23/32 pipelines; > 0 in 8/32.
- Sign flips as threshold convention moves sparse(low p)->dense(high p).
- DET and LAM remain robustly negative across nearly all pipelines.
- Reconciles EMP-191 (rho~-0.90, sparse/matched-RR) with SYN-062 (rho~+1.0, dense).
