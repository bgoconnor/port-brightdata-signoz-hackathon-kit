#!/usr/bin/env python3
"""Acquire full arXiv HTML through Bright Data for a selected paper."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ARXIV_ID = re.compile(r"^[0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?$")


def enrich(arxiv_id: str, output_root: Path, zone: str | None = None) -> Path:
    if not ARXIV_ID.fullmatch(arxiv_id):
        raise ValueError(f"invalid arXiv identifier: {arxiv_id}")

    destination = output_root / arxiv_id
    destination.mkdir(parents=True, exist_ok=True)
    full_text = destination / "paper.md"
    url = f"https://arxiv.org/html/{arxiv_id}"
    command = ["brightdata", "scrape", url, "--format", "markdown", "--output", str(full_text)]
    if zone:
        command.extend(["--zone", zone])
    subprocess.run(command, check=True)

    content = full_text.read_bytes()
    if len(content) < 1000:
        raise ValueError("full-text acquisition returned too little content")
    provenance = {
        "arxiv_id": arxiv_id,
        "paper_version": arxiv_id.rsplit("v", 1)[1] if "v" in arxiv_id else "latest-at-fetch",
        "source_url": url,
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
        "acquired_via": "brightdata-web-unlocker",
        "acquired_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }
    (destination / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("arxiv_id")
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/papers"))
    parser.add_argument("--zone")
    args = parser.parse_args()
    destination = enrich(args.arxiv_id, args.output_root, args.zone)
    print(f"Published full-text evidence to {destination}")


if __name__ == "__main__":
    main()
