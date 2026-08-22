#!/usr/bin/env python3
"""Deterministically score whether a paper has a toy-reproducible core claim."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SIGNALS = {
    "algorithm": 0.22,
    "we propose": 0.22,
    "toy": 0.18,
    "synthetic": 0.18,
    "complexity": 0.10,
    "experiment": 0.10,
}


def score_paper(paper: dict[str, Any]) -> float:
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    return round(min(1.0, sum(weight for term, weight in SIGNALS.items() if term in text)), 2)


def score_records(records: list[dict[str, Any]], threshold: float = 0.5) -> list[dict[str, Any]]:
    scored = []
    for record in records:
        paper = dict(record)
        paper["score"] = score_paper(paper)
        paper["reproducible"] = paper["score"] >= threshold
        scored.append(paper)
    return scored


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()
    records = json.loads(args.path.read_text())
    args.path.write_text(json.dumps(score_records(records, args.threshold), indent=2) + "\n")
    print(f"Scored {len(records)} papers in {args.path}")


if __name__ == "__main__":
    main()
