# Port MCP setup for Codex

Validated on 2026-08-22 with Codex CLI 0.149.0. Port and Codex can change independently, so check the linked first-party documentation if the behavior differs.

## What this connection does

Port's remote MCP server exposes catalog, ownership, scorecard, and workflow tools to Codex. Start with read-only tools. A configured server is not necessarily authenticated or available to the current Codex session.

## Prerequisites

- A Port account with access to the intended organization.
- Codex CLI and Node.js/npm installed.
- A browser logged into the intended Port organization for OAuth approval.
- The organization's Port region:
  - US: the Port app URL contains `us`.
  - EU: otherwise use the EU endpoint.

Verify the local tools:

```bash
codex --version
node --version
npx --version
```

## Recommended setup: compatibility bridge

Codex's direct HTTP OAuth flow may reject Port with an authorization-server issuer mismatch. The `mcp-remote` bridge avoids that direct-flow incompatibility and is also used in Port's documented client configurations.

Use one command for the correct region:

```bash
# US
codex mcp add port-us -- \
  npx -y mcp-remote \
  https://mcp.us.port.io/v1 \
  --header "x-read-only-mode: 1"

# EU
codex mcp add port-eu -- \
  npx -y mcp-remote \
  https://mcp.port.io/v1 \
  --header "x-read-only-mode: 1"
```

If the name already exists, inspect it before replacing it:

```bash
codex mcp get port-us --json
# or: codex mcp get port-eu --json
```

Remove only the stale Port entry, then repeat the matching add command:

```bash
codex mcp remove port-us
# or: codex mcp remove port-eu
```

Start a new Codex session after adding the server:

```bash
codex
```

On first startup, `mcp-remote` may download through npm and open a browser for Port OAuth. Approve access while logged into the intended Port organization.

Do not run `codex mcp login port-us` or `codex mcp login port-eu` for this bridge configuration. Those commands apply to Codex-managed OAuth for direct HTTP servers; the bridge manages its own OAuth flow.

## Verify the connection

First confirm that the server is configured and enabled:

```bash
codex mcp list
codex mcp get port-us --json
# Substitute port-eu when applicable.
```

This proves configuration only. To prove an authenticated end-to-end connection:

1. Start a fresh Codex session.
2. Run `/mcp` and open the `port-us` or `port-eu` entry.
3. Confirm that Port tools are listed.
4. Ask a bounded read-only question, such as: `List up to five service entities in Port, including identifiers and owners. Do not change anything.`

Record the result as live verification only after a Port tool returns catalog data.

## The issuer-mismatch error

The direct setup documented by Port is:

```bash
codex mcp add port-us --url https://mcp.us.port.io/v1
codex mcp login port-us
```

With Codex CLI 0.149.0, the login failed before browser authentication with:

```text
Authorization server issuer mismatch:
expected https://mcp.us.port.io/v1,
received https://auth.us.getport.io
```

This means the MCP resource URL and the issuer reported by Port's authorization metadata differ, and Codex's strict OAuth validation rejected the flow. It does not mean the Port username, password, client ID, or secret was wrong. Do not disable issuer validation or paste tokens into configuration to bypass it. Use the compatibility bridge above, or retry the direct setup after Port or Codex documents a compatible fix.

## Read-only and write access

`x-read-only-mode: 1` hides Port write tools. Keep it enabled for discovery, diagnosis, and demo preparation.

Enable writes only after reviewing the exact intended changes, the Port organization and region, and the authenticated user's permissions. Replace the server configuration with `x-read-only-mode: 0` only when writes are deliberately required. Port also supports `x-allowed-actions-to-run` for restricting executable actions by identifier.

## Credentials and automation

Interactive Codex use relies on browser OAuth and does not require `PORT_CLIENT_ID` or `PORT_CLIENT_SECRET`. Those credentials are for machine authentication, such as CI/CD. Never commit credentials, bearer tokens, OAuth state, or generated authentication caches.

## Troubleshooting checklist

- **No Port entry in `codex mcp list`:** repeat the matching `codex mcp add` command.
- **Configured but no tools in the current conversation:** fully start a new Codex session; MCP tools are discovered at session startup.
- **Browser opens the wrong Port organization:** log into the intended organization before approving OAuth, remove the Port entry, and configure it again under a distinct name if necessary.
- **Direct login reports issuer mismatch:** switch to the compatibility bridge; changing credentials will not resolve metadata validation.
- **`npx` or `mcp-remote` fails:** verify Node.js/npm and network access, then run `npx -y mcp-remote --help`.
- **Corporate VPN or firewall:** verify outbound HTTPS access to the Port MCP and authorization domains.
- **SSO fails during OAuth:** Port documents that some SSO connections require domain-level authentication; contact Port support if the organization is affected.

## References

- [Port MCP installation guide](https://docs.port.io/agent-management/port-mcp-server/installation/)
- [Port MCP overview](https://docs.port.io/agent-management/port-mcp-server/overview/)
- [OpenAI Codex issuer-mismatch tracking issue](https://github.com/openai/codex/issues/38944)
