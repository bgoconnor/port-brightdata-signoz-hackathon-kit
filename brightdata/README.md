# Bright Data paper ingestion

This directory owns the Bright Data-specific portion of the Paper Factory:

- `scrape.py` runs or loads collector output, validates and normalizes records,
  and publishes the shared paper contract.
- `score.py` applies the deterministic reproducibility heuristic.
- `fixtures/` contains safe offline collector-shaped data.
- `tests/` verifies extraction, normalization, scoring, and SQLite publication.

Run from the repository root with `make fixture`, `make scrape
COLLECTOR_ID=c_mt4qssufwcgso7ees`, and `make test`.

Generated normalized data intentionally remains in root `data/`, outside this
directory, because `data/papers.json` is the shared interface consumed by the
board and the Port/SigNoz integration work.
