# Port factory configuration

This directory is the versioned source for the live Port factory contract.

## Current flow

1. A user runs `Start reproduction` on a `Paper` entity.
2. Port creates a related `Reproduction` in `assessing` state and records the
   Port action run ID.
3. Full-text claim selection, feasibility, package generation, and execution
   occur behind the Kubernetes execution boundary.
4. The execution component updates the same `Reproduction` with correlated
   request/result data, evidence, status, and trace identifiers.
5. Port governs retry, review, and approval state.

The Kubernetes transport and CRD are intentionally not specified here yet.
They will be connected after the operator design is finalized. Do not publish
the legacy `paper_to_reproduction` workflow: its abstract-only, toy-code AI
node does not satisfy the reproduction contract.

## Files

- `blueprints/reproduction.patch.json`: additive lifecycle and execution seam.
- `actions/start-reproduction.json`: Paper day-2 action that opens a request.
- `contracts/`: versioned, transport-neutral Kubernetes request/result schemas.

Machine credentials belong in `.env` and must not be committed.
