# Team setup runbook

## Prerequisites

- Git and a supported coding agent.
- Node.js/npm for `npx skills` and Bright Data's CLI workflow.
- Least-privilege vendor credentials supplied outside Git.
- An application that can emit OpenTelemetry, or a plan to instrument one.

Copy `.env.example` to a local `.env` only if needed. `.env` is ignored by Git.

## Install official agent skills

Inspect each upstream package before installation.

### Port

```bash
npx skills add port-labs/port-skills --skill port-getting-started
npx skills add port-labs/port-skills --skill port-blueprints
npx skills add port-labs/port-skills --skill port-integrations
npx skills add port-labs/port-skills --skill port-workflows
```

Also consider `port-context-lake`, `port-terraform`, `port-dashboards`, and `port-permissions`.

For live Port catalog access, follow the [Port MCP setup for Codex](port-mcp-setup.md). It includes the read-only default, end-to-end verification, and the OAuth issuer-mismatch workaround validated during this hackathon setup.

### Bright Data

```bash
brightdata skill list
brightdata skill add scrape
brightdata skill add search
brightdata add mcp --agent codex --global
```

Also consider `data-feeds`, `bright-data-mcp`, and `bright-data-best-practices`.

### SigNoz

For Codex, add the official marketplace, install `signoz` through `/plugins`, then configure and authenticate:

```bash
codex plugin marketplace add SigNoz/agent-skills
signoz-mcp-setup <region-or-self-hosted-mcp-url>
codex mcp login signoz
codex mcp list
```

See the [official setup guide](https://signoz.io/docs/ai/agent-skills/) for current regions and clients.

## Team decisions

- Port region, blueprint identifiers, entity identifier rules, and write permissions.
- Bright Data targets, permitted scope, method, geography, rate limits, and budget.
- SigNoz deployment type, region, OTLP protocol, service names, and environments.

Never commit tokens, ingestion keys, `.env`, authenticated MCP headers, captured private data, or proxy credentials.

## Smoke tests

1. **Bright Data:** retrieve one permitted public test page and validate expected fields.
2. **Application:** process it and emit a structured success log and trace.
3. **SigNoz:** find the service, trace, and log; verify environment and version attributes.
4. **Port:** create or ingest one service and relate it to one data source.
5. **Agent:** use read-only MCP tools to retrieve the same facts.
6. **Failure drill:** cause a controlled parsing failure and locate it from the trace and logs.

## Safe defaults

- Start with read-only tools and preview mutations.
- Require confirmation for a new collection domain, broad query, workflow execution, permission change, or deletion.
- Redact secrets from logs and prompts.
- Put time and result limits on telemetry queries and scrapes.
