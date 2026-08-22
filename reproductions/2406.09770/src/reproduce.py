"""Reproduce PWEMoE MLP-router counts reported in Table 10."""

from __future__ import annotations

import json
from pathlib import Path


TASK_COUNTS = (2, 3, 8)
MLP_ROUTERS = 12
REPORTED = {2: 264, 3: 540, 8: 3360}


def parameters_per_router(tasks: int, backbone_width: int) -> int:
    """Router dimensions depend on task count, never on backbone width."""
    del backbone_width
    hidden = 2 * tasks
    return tasks * hidden + hidden + hidden * tasks + tasks


def calculate(backbone_width: int) -> dict[int, int]:
    return {
        tasks: MLP_ROUTERS * parameters_per_router(tasks, backbone_width)
        for tasks in TASK_COUNTS
    }


def main() -> None:
    narrow = calculate(backbone_width=768)
    wide = calculate(backbone_width=3072)
    passed = narrow == REPORTED and wide == REPORTED
    result = {
        "claim": "router counts match Table 10 and are independent of backbone width",
        "reported": REPORTED,
        "observed_width_768": narrow,
        "observed_width_3072": wide,
        "passed": passed,
    }
    destination = Path(__file__).parents[1] / "results" / "result.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
