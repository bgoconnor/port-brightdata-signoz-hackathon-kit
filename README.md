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

1. Read the [product field guide](docs/product-field-guide.md).
2. Follow the [team setup runbook](docs/setup.md).
3. Choose a thin vertical slice from the [hackathon plan](docs/hackathon-plan.md).
4. Install the vendors' official agent packages before writing custom replacements.
5. Use the project-local [`hackathon-platform-workflow`](skills/hackathon-platform-workflow/SKILL.md) skill for cross-product work.

## Repository contents

- `docs/product-field-guide.md` — concepts, product boundaries, and failure modes.
- `docs/setup.md` — agent packages, MCP setup, credentials, and smoke tests.
- `docs/port-mcp-setup.md` — Port MCP installation, OAuth workaround, and verification.
- `docs/hackathon-context.md` — event constraints, judging criteria, architecture, and scope.
- `docs/hackathon-plan.md` — recommended architecture and demo milestones.
- `src/README.md` — local Minikube deployment and management commands.
- `skills/hackathon-platform-workflow/` — project-local orchestration skill.
- `.env.example` — variable names only; never commit real secrets.

Use first-party skills and MCP servers for product-specific operations. Keep this repository focused on team conventions, integration decisions, reproducible checks, and the workflow spanning all three products.

## License

[MIT](LICENSE)
