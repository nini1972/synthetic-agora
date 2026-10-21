# Dirichlet MGF Verification (HYP-124)

## Test Cases
- **Small α (Uniform)**: α=[0.5, 0.5, 0.5], λ=[2.0, 1.0, 0.5]
- **Large α (Skewed)**: α=[5.0, 2.0, 0.5], λ=[0.3, 0.8, 1.2]
- **Medium α (Anchor Case)**: α=[2.0, 3.0, 1.5], λ=[0.5, 1.0, 0.7]

## Results
| Case | MC Mean | MC SE | Series Value | |Diff| |
|------|---------|--------|--------------|--------|
| Small α (Uniform) | 0.335158 | 0.000017 | 0.335168 | 0.000010 |
| Large α (Skewed) | 0.613519 | 0.000008 | 0.613521 | 0.000002 |
| Medium α (Anchor Case) | 0.461292 | 0.000005 | 0.461294 | 0.000002 |

## Verdict
- **HYP-124**: **Endorsed** if all |Diff| < 3σ.
- **Refuted** otherwise.
