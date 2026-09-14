#!/usr/bin/env python3
"""Constellation health receipt — one command, fail-closed, cryptographically anchored.

Reads `constellation/invariants.json` from the repository root, runs every
declared invariant, and emits a machine-readable receipt to stdout.

Fail-closed by construction:
  * a declared invariant that errors, times out, or is missing counts as FAIL;
  * an empty or unreadable invariant set is itself a FAIL, not a pass;
  * exit status is non-zero unless every required invariant passed.

The receipt is content-addressed: `receipt_hash` covers the canonical JSON of
everything except itself, so a receipt cannot be edited without detection, and
`prev_receipt_hash` chains it to the last receipt in `constellation/receipts/`.

Invariants marked "slow": true are NOT run unless --all is passed. They are
recorded as status "SKIPPED", which is never counted as a pass: a required
invariant that was skipped still fails the receipt.

Usage:  python3 scripts/health_receipt.py [--write] [--quiet] [--all]
Spec:   constellation/SPEC.md   (schema_version below must match)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SCHEMA_VERSION = "1.0.0"
DEFAULT_TIMEOUT = 900


def repo_root(start: Path) -> Path:
    d = start.resolve()
    while True:
        if (d / ".git").exists():
            return d
        if d.parent == d:
            return start.resolve()
        d = d.parent


def git(root: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=60
        ).stdout.strip()
    except Exception:
        return ""


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_invariant(root: Path, inv: dict, run_slow: bool) -> dict:
    name = inv.get("id", "<unnamed>")
    if inv.get("slow") and not run_slow:
        return {
            "id": name, "required": bool(inv.get("required", True)),
            "status": "SKIPPED", "exit_code": None,
            "detail": "marked slow; re-run with --all to execute",
            "duration_s": 0.0,
        }
    cmd = inv.get("cmd")
    required = bool(inv.get("required", True))
    timeout = int(inv.get("timeout", DEFAULT_TIMEOUT))
    started = time.time()

    if not cmd:
        return {
            "id": name, "required": required, "status": "FAIL",
            "detail": "invariant declares no cmd", "exit_code": None,
            "duration_s": 0.0,
        }
    try:
        p = subprocess.run(
            cmd, cwd=root, shell=True, capture_output=True, text=True, timeout=timeout
        )
        ok = p.returncode == 0
        tail = (p.stdout or "")[-400:] + (p.stderr or "")[-400:]
        return {
            "id": name, "required": required,
            "status": "PASS" if ok else "FAIL",
            "exit_code": p.returncode,
            "detail": tail.strip()[-400:],
            "duration_s": round(time.time() - started, 2),
        }
    except subprocess.TimeoutExpired:
        return {
            "id": name, "required": required, "status": "FAIL",
            "exit_code": None, "detail": f"timed out after {timeout}s",
            "duration_s": round(time.time() - started, 2),
        }
    except Exception as exc:  # noqa: BLE001 - any failure is a FAIL, never a pass
        return {
            "id": name, "required": required, "status": "FAIL",
            "exit_code": None, "detail": f"{type(exc).__name__}: {exc}"[:400],
            "duration_s": round(time.time() - started, 2),
        }


def previous_hash(receipts_dir: Path) -> str | None:
    if not receipts_dir.is_dir():
        return None
    files = sorted(receipts_dir.glob("*.json"))
    if not files:
        return None
    try:
        return json.loads(files[-1].read_text())["receipt_hash"]
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="persist the receipt under constellation/receipts/")
    ap.add_argument("--quiet", action="store_true", help="suppress the human summary")
    ap.add_argument("--all", action="store_true",
                    help='also run invariants marked "slow" (release gates)')
    args = ap.parse_args()

    root = repo_root(Path(__file__).parent)
    spec_path = root / "constellation" / "invariants.json"

    # Fail-closed: no declaration is a failure, not a vacuous pass.
    if not spec_path.is_file():
        print(f"FAIL: {spec_path} not found; a repo with no declared invariants "
              f"cannot produce a passing receipt", file=sys.stderr)
        return 2
    try:
        spec = json.loads(spec_path.read_text())
    except Exception as exc:
        print(f"FAIL: cannot parse {spec_path}: {exc}", file=sys.stderr)
        return 2

    invariants = spec.get("invariants") or []
    if not invariants:
        print(f"FAIL: {spec_path} declares zero invariants", file=sys.stderr)
        return 2

    results = [run_invariant(root, inv, args.all) for inv in invariants]
    # A SKIPPED invariant is never a pass. A required one that was skipped
    # still fails the receipt -- that is the whole point of fail-closed.
    failed_required = [r for r in results if r["required"] and r["status"] != "PASS"]
    failed_optional = [r for r in results if not r["required"] and r["status"] == "FAIL"]

    body = {
        "schema_version": SCHEMA_VERSION,
        "repo": spec.get("repo") or root.name,
        "commit": git(root, "rev-parse", "HEAD"),
        "branch": git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "tree_dirty": bool(git(root, "status", "--porcelain")),
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "invariants_hash": sha256(canonical(invariants)),
        "results": results,
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r["status"] == "PASS"),
            "failed_required": len(failed_required),
            "failed_optional": len(failed_optional),
            "skipped": sum(1 for r in results if r["status"] == "SKIPPED"),
        },
        "verdict": "PASS" if not failed_required else "FAIL",
        "prev_receipt_hash": previous_hash(root / "constellation" / "receipts"),
    }
    body["receipt_hash"] = sha256(canonical(body))

    print(json.dumps(body, indent=2))

    if args.write:
        out_dir = root / "constellation" / "receipts"
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = body["generated_at_utc"].replace(":", "").replace("-", "")
        (out_dir / f"{stamp}-{body['receipt_hash'][:12]}.json").write_text(
            json.dumps(body, indent=2) + "\n"
        )

    if not args.quiet:
        print(f"\n  {body['repo']} @ {body['commit'][:8]} — {body['verdict']} "
              f"({body['summary']['passed']}/{body['summary']['total']} passed)",
              file=sys.stderr)
        for r in failed_required:
            print(f"    FAIL [required] {r['id']}: {r['detail'][:160]}", file=sys.stderr)
        for r in failed_optional:
            print(f"    fail [optional] {r['id']}: {r['detail'][:160]}", file=sys.stderr)
        for r in results:
            if r["status"] == "SKIPPED":
                print(f"    skipped {r['id']} — NOT a pass; --all to run", file=sys.stderr)

    return 0 if body["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
