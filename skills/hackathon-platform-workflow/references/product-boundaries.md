# Product boundaries

## Bright Data

- Prefer an existing dataset or scraper for a supported structured source.
- Use Web Unlocker for retrieval without interaction.
- Use Browser API for rendering, navigation, or interaction.
- Use raw proxies only for justified low-level control.

Bright Data acquires external data. It is not the source of application ownership or the observability backend.

## SigNoz

Use SigNoz for runtime telemetry. Instrument with OpenTelemetry and correlate signals through stable service, environment, version, and deployment attributes. Do not encode ownership and governance solely in dashboard labels.

## Port

Use Port for durable engineering context: services, sources, owners, deployments, relations, standards, scorecards, and governed workflows. Reference observability systems and runbooks instead of copying high-volume telemetry into catalog properties.

## Cross-system identifiers

Choose one stable service identifier. Reuse it as the Port entity identifier and OpenTelemetry `service.name` when constraints permit. Store vendor IDs explicitly rather than deriving them from display names.
