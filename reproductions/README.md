# Reproduction evidence packages

Each directory represents one claim-level attempt, not an automatic claim of
success:

```text
reproductions/{arxiv_id}/
  manifest.json       selected claim, provenance, environment, and comparison rule
  README.md           human-readable scope, instructions, and limitations
  requirements.lock   exact dependencies (or an equivalent lock file)
  src/                experiment implementation
  results/result.json machine-readable observed result
```

Execution logs and larger outputs may remain as GitHub Actions artifacts, but their
URLs and digests must be recorded in Port. A package is labeled `reproduced` only
when its observed result satisfies the comparison rule declared in `manifest.json`
before execution. Otherwise its honest outcome is `not_reproduced`, `inconclusive`,
or `blocked`. A `mechanism_demo` illustrates an idea and is never counted as a
reproduction.
