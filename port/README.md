# Port factory configuration

This directory is the versioned source for the live Port factory contract.

## Current flow

1. A user runs `Start reproduction` on a `Paper` entity.
2. Port creates a related `Reproduction` in `assessing` state and records the
   Port action run ID.
3. The Kubernetes execution integration loads full text from PostgreSQL and
   performs claim selection, feasibility, package generation, and execution.
4. The execution component updates the same `Reproduction` with correlated
   request/result data, evidence, status, and trace identifiers.
5. Port governs retry, review, and approval state.

The Port contract is transport-neutral: Hugh's Kubernetes integration implements
the dispatch and callback adapter without changing the lifecycle contract. Do not
publish the legacy `paper_to_reproduction` workflow: its abstract-only, toy-code
AI node does not satisfy the reproduction contract.

Papers without full text remain valid catalog records, but are not eligible for
the reproduction action until their PostgreSQL-backed content is available.

## Files

- `blueprints/reproduction.patch.json`: additive lifecycle and execution seam.
- `actions/start-reproduction.json`: Paper day-2 action that opens a request.
- `contracts/`: versioned, transport-neutral Kubernetes request/result schemas.

Machine credentials belong in `.env` and must not be committed.

## Demo-site MVP workflow

`workflows/article-to-demo-site.json` is the versioned definition of the live
`article_to_demo_site` workflow. Its self-service trigger accepts complete article
text plus feedback from a prior runtime attempt. Port AI returns one self-contained
HTML document and a short summary. The Kubernetes job—not Port—validates, persists,
and serves the generated site; if validation fails, it starts another Port run with
the observed failure attached as `observability_feedback`.
