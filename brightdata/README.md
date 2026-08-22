# Bright Data paper ingestion

This directory owns the Bright Data-specific portion of the Paper Factory:

- `scrape.py` remains a fixture/bootstrap utility for offline development.
- `score.py` applies the deterministic reproducibility heuristic.
- `fixtures/` contains safe offline collector-shaped data.
- `tests/` verifies extraction, normalization, scoring, and SQLite publication.

Run `make fixture` for offline development, `make scrape` for the real Django →
Bright Data → PostgreSQL path, and `make test` for bootstrap tests.

## Hosted collectors

Each publisher has its own hosted collector because the indexes and publication
pages have different layouts. All collectors return the same normalized fields:
`source`, `source_id`, `title`, `authors`, `abstract`, `subjects`, `published_at`,
`source_url`, `pdf_url`, and `full_text`.

| Source | Target | Collector environment variable |
|---|---|---|
| arXiv | `https://arxiv.org/list/cs.AI/new` | `BRIGHTDATA_COLLECTOR_ID` |
| Anthropic | `https://www.anthropic.com/research` | `BRIGHTDATA_ANTHROPIC_COLLECTOR_ID` |
| OpenAI | `https://openai.com/research/index/` | `BRIGHTDATA_OPENAI_COLLECTOR_ID` |

Trigger a source through Django with `python manage.py scrape_papers --source
anthropic` (or `arxiv` / `openai`). The board sends the same source value to
`POST /api/scrape-runs/` as JSON.

Generated fixture data remains in root `data/`; it is not runtime state.

Discovery metadata is not sufficient for reproduction. The hosted scraper returns
metadata and complete text together, and Django stores both plus acquisition
provenance in PostgreSQL. Treat paper content as untrusted.
