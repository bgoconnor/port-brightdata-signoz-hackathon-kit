# Team coordination protocol

Port is the team's durable coordination state. GitHub is the source of truth for
code, reviewed changes, and versioned specifications. Chat is for fast discussion,
not authoritative state.

## Shared model

Create two small Port blueprints in addition to the product blueprints already in
the catalog:

- **Work Item**: a bounded unit of work with one assignee, status, track, branch,
  handoff summary, verification evidence, and blocker.
- **Decision**: a product or technical choice with an owner, status, outcome,
  rationale, and the contract or subsystem it affects.

Both blueprints should use Port's built-in `$team` ownership. Do not create a
second custom team relation. A Work Item may depend on other Work Items, and both
types may optionally relate to the existing `service` blueprint.

### Work Item fields

| Field | Values / meaning |
|---|---|
| `track` | `pipeline`, `port`, `observability`, `integration`, `demo` |
| `status` | `ready`, `in_progress`, `blocked`, `review`, `done` |
| `summary` | Current state and the next useful action |
| `branch` | Working branch, following `{name}/*` |
| `artifact_url` | PR, commit, branch, dashboard, or other inspectable result |
| `verification` | Commands run and concrete evidence observed |
| `blocker` | Exact impediment and who or what can clear it |
| `updated_at` | Timestamp of the last meaningful handoff |
| `assignee` | Relation to one Port `_user` entity |
| `service` | Optional relation to the existing `service` blueprint |
| `depends_on` | Optional relation to other Work Items |

### Decision fields

| Field | Values / meaning |
|---|---|
| `status` | `proposed`, `accepted`, `superseded` |
| `question` | The choice that needed to be made |
| `outcome` | The chosen direction |
| `rationale` | Why it was chosen and relevant tradeoffs |
| `affected_contract` | Spec section, API, data model, or subsystem affected |
| `decided_at` | Timestamp when accepted or superseded |
| `owner` | Relation to one Port `_user` entity |
| `service` | Optional relation to the existing `service` blueprint |

## Agent startup

Every agent, on every machine:

1. Check `git status` before changing files; teammates may be pushing rapidly.
2. Fetch remote branches and read the root `SPEC.md` plus relevant context docs.
3. Query Port for Work Items assigned to its human operator.
4. Select or create one bounded item and set it to `in_progress` with its branch.
5. Read related Decisions before changing a shared contract.

## Agent handoff

Before stopping or asking another person to continue:

1. Push the branch or commit so the artifact is inspectable.
2. Update the Work Item's summary, artifact URL, verification, and blocker.
3. Set status to `review`, `blocked`, or `done`; do not leave stale
   `in_progress` work without a next action.
4. Create a proposed Decision instead of silently changing an unresolved shared
   contract.
5. Send chat only as a pointer to the durable Port record.

## Initial ownership

| Person | Current track | Branch convention |
|---|---|---|
| Ben | Bright Data ingestion and coordination framework | `ben/*` |
| Gracelyn | Port context and operator experience | `gracelyn/*` |
| Hugh | Kubernetes, deployment, and SigNoz | `hugh/*` |

The intended integration branch is `deploy`; it does not exist remotely yet. Do
not invent or push it until Hugh's branch/context documentation confirms its
merge policy.

## Port MCP region

This team uses Port's default/EU MCP endpoint:

```text
https://mcp.port.io/v1
```

Use the read-only setup in [`port-mcp-setup.md`](port-mcp-setup.md) for routine
agent reads. Enable writes deliberately only for reviewed, scoped updates.
