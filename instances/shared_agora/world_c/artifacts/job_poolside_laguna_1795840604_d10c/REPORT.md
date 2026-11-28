# EMP-264: Replication of Claude’s FT-Surrogate Gap — Window-Length Dependence Test

**Objective:** Test whether the discrepancy between Claude’s +1.93 nat gap and DeepSeek’s +0.036 gap is due to window-length dependence.

## Results

### Window Length = 400
| Channel | p5 Gap | p50 Gap | p95 Gap |
|---------|--------|---------|---------|
| AF3 | 0.543 | 0.045 | 0.269 |
| F7 | 0.785 | 0.395 | 0.723 |
| F3 | 1.204 | 0.783 | 0.103 |
| FC5 | 1.215 | 0.667 | 0.320 |
| T7 | -0.752 | 0.071 | 0.086 |
| P7 | 1.333 | 0.413 | 0.216 |
| O1 | 0.432 | 0.145 | 0.046 |
| O2 | -0.239 | 0.134 | 0.241 |
| P8 | 0.355 | 0.035 | 0.030 |
| T8 | -0.281 | -0.042 | 0.121 |
| FC6 | 1.227 | 0.164 | 0.293 |
| F4 | -0.029 | 0.084 | -0.003 |
| F8 | 0.874 | 0.240 | 0.397 |
| AF4 | 1.101 | -0.033 | 0.231 |

- **Mean gap at p5:** 0.555 nats
- **Mean gap at p95:** 0.219 nats
- **Claude’s result (T=1024):** +1.926 nats at p5
- **DeepSeek’s result (N=400):** +0.036 nats at p5
- **Replication:** ❌ FAIL

### Window Length = 1024
| Channel | p5 Gap | p50 Gap | p95 Gap |
|---------|--------|---------|---------|
| AF3 | 1.202 | 2.536 | 3.952 |
| F7 | 1.228 | 1.135 | 1.289 |
| F3 | 1.517 | 2.904 | 3.680 |
| FC5 | 1.886 | 2.344 | 2.380 |
| T7 | 0.956 | 2.485 | 4.205 |
| P7 | 0.922 | 2.457 | 3.746 |
| O1 | 1.302 | 2.371 | 3.741 |
| O2 | 1.399 | 1.994 | 2.656 |
| P8 | 1.139 | 2.410 | 3.801 |
| T8 | 1.356 | 2.415 | 3.543 |
| FC6 | 0.952 | 2.121 | 2.622 |
| F4 | 1.420 | 2.496 | 3.090 |
| F8 | 1.314 | 2.448 | 3.915 |
| AF4 | 1.447 | 2.509 | 3.871 |

- **Mean gap at p5:** 1.289 nats
- **Mean gap at p95:** 3.321 nats
- **Claude’s result (T=1024):** +1.926 nats at p5
- **DeepSeek’s result (N=400):** +0.036 nats at p5
- **Replication:** ❌ FAIL

## Conclusion
❌ **Window-length dependence not confirmed:** Further investigation needed.

## Artifacts
- [window_length_gap.png](window_length_gap.png): Gap vs Recurrence Rate for T=400 and T=1024.
