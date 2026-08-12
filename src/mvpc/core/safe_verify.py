"""SafeVerify: scan sources for forbidden axioms and unsound markers."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from mvpc.canonical import hash_canonical
from mvpc.trust_verdicts import TrustVerdict

_RULES: list[tuple[str, re.Pattern[str], str]] = [
    ("sorry", re.compile(r"\bsorry\b"), "Lean sorry placeholder"),
    ("sorryAx", re.compile(r"\bsorryAx\b"), "Lean sorryAx axiom"),
    ("admit", re.compile(r"\badmit\b"), "Coq admit"),
    ("Admitted", re.compile(r"\bAdmitted\b"), "Coq Admitted"),
    ("unsafe", re.compile(r"\bunsafe\b"), "Unsafe declaration"),
    ("axiom ", re.compile(r"(?m)^\s*axiom\s+"), "Lean axiom declaration"),
    ("Axiom ", re.compile(r"(?m)^\s*Axiom\s+"), "Coq Axiom declaration"),
    ("sorry", re.compile(r"\bexpect\s+failure\b", re.I), "Expected-failure marker"),
    ("ofReduceBool", re.compile(r"\bofReduceBool\b"), "Lean ofReduceBool trust edge"),
    ("native_decide", re.compile(r"\bnative_decide\b"), "Lean native_decide"),
    ("unchecked", re.compile(r"\bunchecked\b"), "Unchecked construct"),
    ("assume false", re.compile(r"assume\s*\(\s*false\s*\)", re.I), "Vacuous false assumption"),
]


@dataclass
class Finding:
    rule: str
    message: str
    line: int
    excerpt: str


@dataclass
class SafeVerifyReport:
    clean: bool
    findings: list[Finding] = field(default_factory=list)
    source_hash: str = ""
    recommended_verdict_cap: str = TrustVerdict.FORMALLY_CHECKED.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def hash(self) -> str:
        return hash_canonical(self.to_dict())


def safe_verify_source(source: str, *, backend: str | None = None) -> SafeVerifyReport:
    findings: list[Finding] = []
    lines = source.splitlines()
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("--") or stripped.startswith("//") or stripped.startswith("*"):
            continue
        for rule, pat, msg in _RULES:
            if pat.search(line):
                findings.append(Finding(rule=rule, message=msg, line=i, excerpt=line.strip()[:200]))

    clean = not findings
    if any(f.rule in {"sorry", "sorryAx", "admit", "Admitted"} for f in findings):
        cap = TrustVerdict.EVIDENCE_SUPPORTED.value
    elif findings:
        cap = TrustVerdict.INCONCLUSIVE.value
    else:
        cap = TrustVerdict.FORMALLY_CHECKED.value

    return SafeVerifyReport(
        clean=clean,
        findings=findings,
        source_hash=hash_canonical({"source": source, "backend": backend}),
        recommended_verdict_cap=cap,
    )
