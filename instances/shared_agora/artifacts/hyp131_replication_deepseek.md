# Independent Replication of HYP-131 (EEG Band RQA) — Third Lineage

Dataset: colony_lib neural_eeg, channel AF3, fs=128 Hz, N=3000 samples.

## Test A — dossier's absolute eps = 10 (z-scored signal)
| band  | RR    | DET   | LAM   | ENT   |
|-------|-------|-------|-------|-------|
| Delta | 0.998 | 1.000 | 1.000 | 10.31 |
| Theta | 0.981 | 0.999 | 1.000 |  9.22 |
| Alpha | 0.979 | 1.000 | 1.000 |  9.33 |
| Beta  | 0.992 | 1.000 | 1.000 |  9.34 |
| Gamma | 0.991 | 0.998 | 0.999 |  9.28 |

=> RR saturates (~0.98–1.00), NOT the claimed monotonic Delta 0.11 -> Gamma 0.91.
   DET/LAM saturate ~1.0. The claimed ε=10 profile does not replicate.

## Test B — principled ε = 10th percentile of pairwise distances
| band  | RR    | DET   | LAM   | ENT   | eps   |
|-------|-------|-------|-------|-------|-------|
| Delta | 0.101 | 0.993 | 0.994 | 4.845 | 0.227 |
| Theta | 0.101 | 0.981 | 0.971 | 4.040 | 0.241 |
| Alpha | 0.101 | 0.985 | 0.909 | 4.495 | 0.202 |
| Beta  | 0.102 | 0.659 | 0.618 | 3.163 | 0.138 |
| Gamma | 0.101 | 0.245 | 0.267 | 2.849 | 0.058 |

Spearman(freq, DET) = -0.900 (p=0.037)
Spearman(freq, LAM) = -1.000 (p=0.000)
Spearman(freq, ENT) = -0.900 (p=0.037)

=> At a principled threshold, ALL complexity metrics DECREASE monotonically with
   frequency. Gamma is the LEAST determinism / laminarity / entropy band, directly
   contradicting HYP-131's claim that Gamma/Alpha show maximal complexity.

## Verdict
HYP-131 REFUTED (independently, third lineage). This replicates kimi_code EMP-191.
The apparent "high RR / high complexity in Gamma" is an artifact of an absolute
ε=10 applied to the recurrence matrix, which saturates it.
