#!/usr/bin/env python3
"""Acquire or load Bright Data output, normalize it, and publish Paper records."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from score import score_records

ARXIV_URL = "https://arxiv.org/list/cs.AI/new"
REQUIRED_FIELDS = ("arxiv_id", "title", "authors", "abstract", "subjects")


def extract_records(payload: Any) -> list[dict[str, Any]]:
    """Accept common CLI envelopes while keeping the application model stable."""
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise ValueError("Bright Data output must be a JSON object or array")
    for key in ("data", "results", "records", "items", "snapshot"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            try:
                return extract_records(value)
            except ValueError:
                pass
    raise ValueError("Could not find a record array in Bright Data output")


def string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def normalize_record(raw: dict[str, Any], scraped_at: str) -> dict[str, Any]:
    arxiv_id = str(raw.get("arxiv_id") or raw.get("id") or "").strip()
    if arxiv_id.lower().startswith("arxiv:"):
        arxiv_id = arxiv_id.split(":", 1)[1].strip()
    paper = {
        "arxiv_id": arxiv_id,
        "title": str(raw.get("title") or "").strip(),
        "authors": string_list(raw.get("authors")),
        "abstract": str(raw.get("abstract") or raw.get("summary") or "").strip(),
        "subjects": string_list(raw.get("subjects") or raw.get("categories")),
        "scraped_at": scraped_at,
    }
    missing = [field for field in REQUIRED_FIELDS if not paper[field]]
    if missing:
        raise ValueError(f"Paper is missing required fields {missing}: {paper['arxiv_id'] or paper['title'] or '<unknown>'}")
    return paper


def acquire(collector_id: str, output: Path) -> Any:
    command = [
        "brightdata", "scraper", "run", collector_id, ARXIV_URL,
        "--pretty", "--output", str(output),
    ]
    subprocess.run(command, check=True)
    return json.loads(output.read_text())


def write_sqlite(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS papers (
                arxiv_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors TEXT NOT NULL,
                abstract TEXT NOT NULL,
                subjects TEXT NOT NULL,
                score REAL NOT NULL,
                reproducible INTEGER NOT NULL,
                scraped_at TEXT NOT NULL
            )"""
        )
        connection.executemany(
            """INSERT OR REPLACE INTO papers VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    paper["arxiv_id"], paper["title"], json.dumps(paper["authors"]),
                    paper["abstract"], json.dumps(paper["subjects"]), paper["score"],
                    int(paper["reproducible"]), paper["scraped_at"],
                )
                for paper in records
            ],
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="Existing Bright Data JSON or fixture")
    source.add_argument("--collector-id", help="Run this Bright Data collector")
    parser.add_argument("--raw-output", type=Path, default=Path("artifacts/brightdata-papers.json"))
    parser.add_argument("--json-output", type=Path, default=Path("data/papers.json"))
    parser.add_argument("--db", type=Path, default=Path("data/papers.db"))
    args = parser.parse_args()

    if args.collector_id:
        args.raw_output.parent.mkdir(parents=True, exist_ok=True)
        payload = acquire(args.collector_id, args.raw_output)
    else:
        payload = json.loads(args.input.read_text())

    scraped_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    normalized = [normalize_record(record, scraped_at) for record in extract_records(payload)]
    records = score_records(normalized)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(records, indent=2) + "\n")
    write_sqlite(records, args.db)
    print(f"Published {len(records)} papers to {args.json_output} and {args.db}")


if __name__ == "__main__":
    main()
