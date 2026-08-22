# Reproduction factory contract

`factory/` contains shared scientific-reproduction contracts. It is not a
standalone runner and it is not the Port workflow implementation.

The retained `experiment-manifest.schema.json` defines the evidence an execution
attempt must declare: selected claim, source provenance, environment, command,
reported result, and comparison rule.

## Runtime ownership

- PostgreSQL is canonical for papers and full text.
- Port owns request, lifecycle, review, retry policy, and evidence metadata.
- The Kubernetes execution integration loads the paper from PostgreSQL, prepares
  and executes the experiment, stores large artifacts in the configured object
  store, and reports a result to the same Port `Reproduction` entity.
- SigNoz receives correlated traces from the application and execution path.

The Port boundary is versioned under [`../port/contracts`](../port/contracts).
The execution request embeds or references an experiment manifest only after
claim selection and feasibility assessment are complete.

## Retired prototype

The former `validate_candidate.py`, `report_to_port.py`, fixture, tests, and
GitHub Actions workflow implemented a standard-library-only, single-file,
12-second toy validator. They were removed because they contradicted the current
evidence-backed design and the Kubernetes execution architecture. Git history
retains them if their implementation is ever useful as a reference.
