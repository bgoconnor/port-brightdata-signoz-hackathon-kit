# Port + Bright Data + SigNoz Hackathon Kit

A shared, agent-ready field guide for building with [Port](https://www.port.io/), [Bright Data](https://brightdata.com/), and [SigNoz](https://signoz.io/) at a hackathon.

```text
Bright Data -> external web data acquisition
      |
      v
Your application and services
      |
      v  OpenTelemetry
SigNoz -> logs, metrics, traces, dashboards, and alerts
      |
      v  operational and ownership context
Port -> catalog, governance, scorecards, and workflows
```

## Start here

1. Read the authoritative [Paper Factory spec](SPEC.md).
2. Read the [product field guide](docs/product-field-guide.md).
3. Follow the [team setup runbook](docs/setup.md).
4. Install the vendors' official agent packages before writing custom replacements.
5. Use the project-local [`hackathon-platform-workflow`](skills/hackathon-platform-workflow/SKILL.md) skill for cross-product work.

## Run the paper spine

The deterministic fixture path requires only Python 3:

```bash
make fixture
make test
python3 -m http.server 8000
```

Open `http://localhost:8000/board.html`. For live acquisition through the existing
Bright Data collector:

```bash
make scrape COLLECTOR_ID=c_mt4qssufwcgso7ees
```

Both paths publish the stable team contract to `data/papers.json` and SQLite to
`data/papers.db`.

## Repository contents

- `SPEC.md` — current, authoritative product and implementation specification.
- `brightdata/` — Bright Data acquisition, scoring, fixture, and pipeline tests.
- `data/papers.json` — shared normalized paper contract consumed by the application and integrations.
- `docs/specs/` — immutable source drafts and superseded specification history.
- `docs/product-field-guide.md` — concepts, product boundaries, and failure modes.
- `docs/setup.md` — agent packages, MCP setup, credentials, and smoke tests.
- `docs/port-mcp-setup.md` — Port MCP installation, OAuth workaround, and verification.
- `docs/hackathon-context.md` — pre-kickoff research and historical planning context.
- `docs/hackathon-plan.md` — generic baseline retained for reference; superseded by `SPEC.md` where they conflict.
- `src/README.md` — local Minikube deployment and management commands.
- `skills/hackathon-platform-workflow/` — project-local orchestration skill.
- `.env.example` — variable names only; never commit real secrets.

Use first-party skills and MCP servers for product-specific operations. Keep this repository focused on team conventions, integration decisions, reproducible checks, and the workflow spanning all three products.

## License

[MIT](LICENSE)
