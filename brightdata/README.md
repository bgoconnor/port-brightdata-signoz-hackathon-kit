# Bright Data paper ingestion

This directory owns the Bright Data-specific portion of the Paper Factory:

- `scrape.py` runs or loads collector output, validates and normalizes records,
  and publishes the shared paper contract.
- `score.py` applies the deterministic reproducibility heuristic.
- `enrich.py` acquires the full arXiv HTML for a selected candidate through Bright
  Data Web Unlocker and records immutable provenance alongside it.
- `fixtures/` contains safe offline collector-shaped data.
- `tests/` verifies extraction, normalization, scoring, and SQLite publication.

Run from the repository root with `make fixture`, `make scrape
COLLECTOR_ID=c_mt4qssufwcgso7ees`, `make enrich ARXIV_ID=2608.12345`, and
`make test`.

Generated normalized data intentionally remains in root `data/`, outside this
directory, because `data/papers.json` is the shared interface consumed by the
board and the Port/SigNoz integration work.

Discovery metadata is not sufficient for reproduction. Before creating an
experiment, enrich the selected paper and retain `artifacts/papers/{arxiv_id}/paper.md`
plus `provenance.json`. Treat the full text and every linked artifact as untrusted.
