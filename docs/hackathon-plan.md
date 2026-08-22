# Hackathon implementation plan

## Thin vertical slice

1. Collect one authorized public source with Bright Data.
2. Normalize it into a small, versioned application model.
3. Instrument acquisition and processing with OpenTelemetry.
4. Verify traces, logs, and basic RED metrics in SigNoz.
5. Represent the application, owner, deployment, and data source in Port.
6. Add one Port scorecard rule and one safe workflow.
7. Demonstrate an agent answering a cross-system operational question.

## Suggested demo story

“Our service collects a changing public data source. Port shows who owns the service, what source it depends on, and whether it meets readiness standards. SigNoz shows every acquisition request and identifies a parsing regression. A governed Port workflow triggers remediation or reruns the job.”

## Minimal Port model

- `service`
- `dataSource`
- `deployment`
- Relations: service uses data source; deployment runs service.
- Scorecards: owner present, telemetry enabled, runbook present, recent successful collection.

## Minimal telemetry

- Trace: collection span and normalization/storage span.
- Metrics: request count, failure count, duration, records produced.
- Logs: event name, status, source identifier, record count, trace ID, sanitized error category.
- Resources: service name, environment, version, team, deployment identifier.

Do not use target URLs, request IDs, response bodies, or full exception text as metric labels.

## Demo checkpoints

- Deterministic acquisition with a sanitized fixture.
- Trace and logs visible in SigNoz.
- Entities and relations visible in Port.
- Controlled failure explained from telemetry.
- One governed action and agent-produced operational summary.
