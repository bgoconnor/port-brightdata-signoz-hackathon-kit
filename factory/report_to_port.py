#!/usr/bin/env python3
"""Report reproduction execution evidence back to its Port entity."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path
from typing import Any


def next_state(passed: bool, retry_count: int) -> tuple[str, str]:
    if passed:
        return "passed", "pending_review"
    if retry_count < 2:
        return "failed", "repairing"
    return "failed", "failed"


def request_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--entity", required=True)
    parser.add_argument("--retry-count", type=int, required=True)
    parser.add_argument("--api-base", default="https://api.port.io")
    args = parser.parse_args()

    client_id = os.environ["PORT_CLIENT_ID"]
    client_secret = os.environ["PORT_CLIENT_SECRET"]
    result = json.loads(args.result.read_text())
    run_status, factory_status = next_state(bool(result["passed"]), args.retry_count)

    auth = request_json(
        f"{args.api_base.rstrip('/')}/v1/auth/access_token",
        {"clientId": client_id, "clientSecret": client_secret},
    )
    evidence = (
        f"### Attempt {args.retry_count + 1}\n\n"
        f"Exit code: `{result['exit_code']}`\n\n"
        f"#### stdout\n```text\n{result['stdout']}\n```\n\n"
        f"#### stderr\n```text\n{result['stderr']}\n```"
    )
    request_json(
        f"{args.api_base.rstrip('/')}/v1/blueprints/reproduction/entities?upsert=true&merge=true",
        {
            "identifier": args.entity,
            "properties": {
                "run_status": run_status,
                "factory_status": factory_status,
                "retry_count": args.retry_count,
                "run_output": evidence,
            },
        },
        {"Authorization": f"Bearer {auth['accessToken']}"},
    )
    print(f"Reported {args.entity}: {run_status}/{factory_status}")


if __name__ == "__main__":
    main()
