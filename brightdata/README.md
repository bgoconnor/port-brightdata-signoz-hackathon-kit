# Bright Data paper ingestion

This directory owns the Bright Data-specific portion of the Paper Factory:

- `scrape.py` remains a fixture/bootstrap utility for offline development.
- `score.py` applies the deterministic reproducibility heuristic.
- `fixtures/` contains safe offline collector-shaped data.
- `tests/` verifies extraction, normalization, scoring, and SQLite publication.

Run `make fixture` for offline development, `make scrape` for the real Django →
Bright Data → PostgreSQL path, and `make test` for bootstrap tests. The runtime
collector is `c_mt4y2std23j5floxrv`, bounded to up to three complete papers.

Generated fixture data remains in root `data/`; it is not runtime state.

Discovery metadata is not sufficient for reproduction. The hosted scraper returns
metadata and complete text together, and Django stores both plus acquisition
provenance in PostgreSQL. Treat paper content as untrusted.
