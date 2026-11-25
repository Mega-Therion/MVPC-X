"""Mechanical witness feed: MVPC-X witnesses as the ``V_mech`` input.

SAMO integration (S.A.M.O. v2.0 spec, Mega-Therion/Chyren
``THE_OMEGARITHM_SAMO_MASTER_SPEC_2026-11-24.md`` §4 and §8; Block directive
BLK-1615): the multi-objective artifact selection function

    F(x) = V_hard(x) * V_mech(x) * B_bridge(x) * H_local(x)

takes ``V_mech(x) in [0, 1]`` — the deterministic verification yield — from
*mechanical witnesses*: the ratio and rigor of independent deterministic
checks passed, with zero hidden ``checks_unavailable``.  MVPC-X is the
deterministic verification kernel of that function (spec §5.1, role 3), and
this module is its feed: it projects a set of sealed :class:`Witness` records
into the JSON feed document that a selection function consumes (the reference
consumer is Nova-Conscientia ``core/artifact_selection.py``).

Yield semantics (fail closed, per COVENANT.md principles 1–3):

* A witness earns passed checks only if its self-hash verifies
  (``verify_integrity``) and it carries no VIOLATION finding.  A tampered or
  violated witness contributes its checks to the denominator and none to the
  numerator.
* A check that could not run (``coverage["checks_unavailable"]``) never
  counts as passed; it counts in the denominator and its name is surfaced at
  the top level of the feed — unavailable checks are never hidden.
* No witnesses, or no checks at all, yields ``V_mech = 0.0``: absence of
  mechanical evidence is not mechanical assurance.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict, List, Sequence

from mvpc.witness import Witness

#: Schema identifier of the feed document (versioned; consumers pin it).
FEED_SCHEMA = "mvpc-x/samo-v-mech-feed/1"


def _severity_name(finding: Dict[str, Any]) -> str:
    """Normalize a finding's severity to its enum name string."""
    sev = finding.get("severity", "")
    if isinstance(sev, Enum):
        return sev.name
    return str(sev)


def _witness_entry(witness: Witness) -> Dict[str, Any]:
    """Project one witness into its feed entry (see module docstring)."""
    integrity_ok = witness.verify_integrity()
    performed = list(witness.checks_performed)
    unavailable = list(witness.coverage.get("checks_unavailable", []) or [])
    violation_count = sum(
        1 for f in witness.findings if _severity_name(f) == "VIOLATION"
    )
    passed = bool(integrity_ok and violation_count == 0)
    checks_passed = len(performed) if passed else 0
    return {
        "witness_id": witness.witness_id,
        "witness_hash": witness.witness_hash,
        "claim_id": witness.claim_id,
        "artifact_hash": witness.artifact_hash,
        "attestation_state": witness.attestation_state,
        "integrity_ok": integrity_ok,
        "checks_performed": performed,
        "checks_unavailable": unavailable,
        "violation_count": violation_count,
        "checks_passed": checks_passed,
        "checks_total": len(performed) + len(unavailable),
    }


def mechanical_witness_feed(witnesses: Sequence[Witness]) -> Dict[str, Any]:
    """Build the V_mech feed document for a set of MVPC-X witnesses.

    Args:
        witnesses: the independent mechanical witnesses for one artifact (or
            one batch scored together).  Each witness is one deterministic
            verification run; independence across runs is the caller's
            provenance claim and is recorded per witness in the feed.

    Returns:
        A JSON-serializable dict with the aggregate ``v_mech`` in [0, 1],
        the passed/total check counts, every unavailable check name (never
        hidden), and the per-witness entries the aggregate was computed
        from, so any consumer can recompute the yield and audit it.
    """
    entries = [_witness_entry(w) for w in witnesses]
    checks_passed = sum(e["checks_passed"] for e in entries)
    checks_total = sum(e["checks_total"] for e in entries)
    unavailable_names: List[str] = []
    for e in entries:
        for name in e["checks_unavailable"]:
            if name not in unavailable_names:
                unavailable_names.append(name)
    v_mech = (checks_passed / checks_total) if checks_total > 0 else 0.0
    return {
        "schema": FEED_SCHEMA,
        "v_mech": v_mech,
        "checks_passed": checks_passed,
        "checks_total": checks_total,
        "checks_unavailable": unavailable_names,
        "witnesses": entries,
    }


def mechanical_witness_feed_json(witnesses: Sequence[Witness]) -> str:
    """The feed document as a JSON string (the cross-repo wire form)."""
    return json.dumps(mechanical_witness_feed(witnesses), indent=2)
