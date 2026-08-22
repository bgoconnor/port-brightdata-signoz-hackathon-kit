# Paper Factory agent instructions

These instructions apply to every agent working anywhere in this repository.

## Required shared context

- `SPEC.md` is the authoritative product and data-contract specification.
- `docs/team-coordination.md` is the authoritative cross-machine coordination
  protocol. Read it before selecting or changing work.
- Port is the durable source of truth for work ownership, current status,
  blockers, verification evidence, and team decisions.
- GitHub is the durable source of truth for code, diffs, commits, and versioned
  specifications. Chat is notification only.

## Mandatory startup loop

Before editing files:

1. Run `git status` and fetch current remote branch state.
2. Read `SPEC.md` and `docs/team-coordination.md`.
3. Query Port's `workItem` entities for the human operator's assignment.
4. Read relevant `decision` entities before changing any shared contract.
5. Claim one bounded Work Item by setting it to `in_progress` and recording the
   working `{name}/*` branch.

If Port is unavailable, do not invent shared state. Continue only with clearly
local, non-conflicting work and record the missing Port handoff as a blocker once
the connection returns. The team uses the default/EU MCP endpoint:
`https://mcp.port.io/v1`.

## Mandatory handoff loop

Before stopping, switching agents, or requesting review:

1. Verify the work in proportion to its risk.
2. Push an inspectable branch, commit, or PR.
3. Update the Port Work Item with summary, artifact URL, verification evidence,
   exact blocker, and `updated_at`.
4. Set the Work Item to `review`, `blocked`, or `done`. Never leave stale
   `in_progress` state.
5. Record unresolved shared choices as proposed Port Decisions; do not silently
   change `SPEC.md`, APIs, schemas, branch policy, or deployment contracts.

## Team identity

Port team identifier: `default_team` (title: **Paper Factory Team**).

- Ben: `ben@archway-labs.com`, branches `ben/*`
- Gracelyn: `newhouse.oconnor@gmail.com`, branches `gracelyn/*`
- Hugh: `hugh.hoford@gmail.com`, branches `hugh/*`

Current Port ownership: Ben owns live workflow implementation and verification;
Gracelyn owns the context lake, catalog, and operator experience. Preserve and
extend Gracelyn's existing workflows rather than recreating them.

See `docs/team-coordination.md` for the Port field definitions and complete
workflow. See `docs/port-mcp-setup.md` for connection setup.
