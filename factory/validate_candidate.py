#!/usr/bin/env python3
"""Validate and execute a generated reproduction in a constrained container."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import tempfile
from pathlib import Path


ALLOWED_IMPORTS = {"collections", "functools", "itertools", "math", "random", "statistics"}
BLOCKED_CALLS = {"compile", "eval", "exec", "input", "open", "__import__"}
BLOCKED_ATTRIBUTES = {
    "connect", "fork", "popen", "remove", "rename", "replace", "rmdir",
    "socket", "spawn", "system", "unlink",
}


class PolicyError(ValueError):
    """Candidate violates the deliberately small reproduction policy."""


def validate_source(source: str) -> None:
    if len(source.splitlines()) > 100:
        raise PolicyError("candidate exceeds the 100-line limit")

    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise PolicyError(f"syntax error: {error}") from error

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = {alias.name.split(".", 1)[0] for alias in node.names}
            disallowed = names - ALLOWED_IMPORTS
            if disallowed:
                raise PolicyError(f"disallowed imports: {', '.join(sorted(disallowed))}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root not in ALLOWED_IMPORTS:
                raise PolicyError(f"disallowed import: {node.module or '<relative>'}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_CALLS:
                raise PolicyError(f"disallowed call: {node.func.id}")
        elif isinstance(node, ast.Attribute) and node.attr.lower() in BLOCKED_ATTRIBUTES:
            raise PolicyError(f"disallowed attribute: {node.attr}")


def execute(source: str) -> dict[str, object]:
    validate_source(source)
    with tempfile.TemporaryDirectory(prefix="paper-factory-") as directory:
        candidate = Path(directory) / "candidate.py"
        candidate.write_text(source)
        command = [
            "docker", "run", "--rm", "--network", "none", "--read-only",
            "--memory", "128m", "--cpus", "0.5", "--pids-limit", "64",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
            "--mount", f"type=bind,src={candidate},dst=/candidate.py,readonly",
            "python:3.12-slim", "python", "-I", "/candidate.py",
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=12)
        except subprocess.TimeoutExpired as error:
            return {"passed": False, "exit_code": 124, "stdout": error.stdout or "", "stderr": "execution exceeded 12 seconds"}
        return {
            "passed": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout[-8000:],
            "stderr": result.stderr[-8000:],
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()

    try:
        outcome = execute(args.candidate.read_text())
    except PolicyError as error:
        outcome = {"passed": False, "exit_code": 126, "stdout": "", "stderr": str(error)}

    rendered = json.dumps(outcome)
    if args.result:
        args.result.write_text(rendered + "\n")
    print(rendered)
    raise SystemExit(0 if outcome["passed"] else 1)


if __name__ == "__main__":
    main()
