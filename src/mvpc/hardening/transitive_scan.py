"""Layer 5b: recursive/transitive sorry/admit/unsafe scans over imports."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Set

from mvpc.core.safe_verify import safe_verify_source

_IMPORT_PATTERNS = [
    re.compile(r"(?m)^\s*import\s+([A-Za-z0-9_.]+)"),
    re.compile(r"(?m)^\s*from\s+([A-Za-z0-9_.]+)\s+import"),
    re.compile(r"(?m)^\s*Require\s+Import\s+([A-Za-z0-9_.]+)"),
]


@dataclass
class TransitiveScanReport:
    clean: bool
    files_scanned: list[str] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    missing_imports: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _extract_imports(text: str) -> list[str]:
    found: list[str] = []
    for pat in _IMPORT_PATTERNS:
        found.extend(pat.findall(text))
    return found


def _resolve_import(name: str, search_roots: Iterable[Path]) -> Path | None:
    rel = Path(*name.split("."))
    candidates = [
        rel.with_suffix(".lean"),
        rel.with_suffix(".v"),
        rel.with_suffix(".thy"),
        rel.with_suffix(".dfy"),
        rel / "default.lean",
    ]
    for root in search_roots:
        for c in candidates:
            p = root / c
            if p.is_file():
                return p
    return None


def transitive_axiom_scan(
    entry_source: str,
    *,
    entry_path: str | Path | None = None,
    search_roots: list[str | Path] | None = None,
    max_files: int = 50,
) -> TransitiveScanReport:
    roots = [Path(r) for r in (search_roots or [])]
    if entry_path is not None:
        roots.insert(0, Path(entry_path).resolve().parent)

    report = TransitiveScanReport(clean=True)
    queue: list[tuple[str, str]] = [("<entry>", entry_source)]
    seen: Set[str] = set()

    while queue and len(report.files_scanned) < max_files:
        label, text = queue.pop(0)
        if label in seen:
            continue
        seen.add(label)
        report.files_scanned.append(label)

        sv = safe_verify_source(text)
        if not sv.clean:
            report.clean = False
            for f in sv.findings:
                report.findings.append(
                    {"file": label, "rule": f.rule, "line": f.line, "excerpt": f.excerpt}
                )

        for imp in _extract_imports(text):
            resolved = _resolve_import(imp, roots)
            if resolved is None:
                report.missing_imports.append(imp)
                continue
            key = str(resolved)
            if key not in seen:
                try:
                    queue.append((key, resolved.read_text(encoding="utf-8")))
                except OSError:
                    report.missing_imports.append(imp)

    return report
