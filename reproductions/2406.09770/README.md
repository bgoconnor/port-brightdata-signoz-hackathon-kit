# Partial reproduction: PWEMoE router parameter counts

This package tests one quantitative architectural claim from arXiv:2406.09770v2,
not the paper's GPU-heavy accuracy or Pareto-front benchmarks.

Section 4 defines each router as an MLP with input width `T`, hidden width `2T`,
and output width `T`. Including biases, one router has:

```text
(T × 2T) + 2T + (2T × T) + T = 4T² + 3T parameters
```

CLIP-ViT-B/32 has 12 MLP blocks. The experiment calculates the total for 2, 3,
and 8 tasks and compares it exactly with Table 10: 264, 540, and 3.36K.

Run:

```bash
python3 -I reproductions/2406.09770/src/reproduce.py
```

The experiment writes `results/result.json` and exits non-zero if any reported
count differs. This is labeled `partial_claim`; it does not reproduce model quality,
memory consumption, or training time.
