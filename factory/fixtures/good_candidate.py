"""Deterministic smoke-test candidate for the isolated validation runner."""

import math

values = [1, 4, 9, 16]
root_mean = sum(math.sqrt(value) for value in values) / len(values)
print(f"root_mean={root_mean:.2f}")
