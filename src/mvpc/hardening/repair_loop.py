"""Layer 5a: AEON-style bounded proof repair within EVOLVE zones."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, List

from mvpc.core.lexical_zones import LexicalZoneError, apply_zoned_edit, validate_zones
from mvpc.core.safe_verify import safe_verify_source


@dataclass
class RepairAttempt:
    attempt: int
    accepted: bool
    message: str
    candidate_hash: str = ""


@dataclass
class RepairOutcome:
    success: bool
    final_source: str
    attempts: List[RepairAttempt] = field(default_factory=list)
    stop_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PatchGenerator = Callable[[str, str, int], str]


def _default_patcher(original: str, error_trace: str, attempt: int) -> str:
    marker = "EVOLVE-BLOCK-BEGIN"
    if marker not in original:
        return original
    inject = f"\n-- auto repair attempt {attempt}\nhave _repair{attempt} : True := by trivial\n"
    return original.replace(marker, marker + inject, 1)


class RepairLoop:
    def __init__(
        self,
        *,
        max_depth: int = 3,
        patcher: PatchGenerator | None = None,
    ) -> None:
        self.max_depth = max_depth
        self.patcher = patcher or _default_patcher

    def run(self, source: str, error_trace: str = "") -> RepairOutcome:
        try:
            if "EVOLVE-BLOCK-BEGIN" in source or "EVOLVE-VALUE-BEGIN" in source:
                validate_zones(source)
        except LexicalZoneError as exc:
            return RepairOutcome(
                success=False, final_source=source, stop_reason=f"invalid zones: {exc}"
            )

        current = source
        attempts: list[RepairAttempt] = []

        for i in range(1, self.max_depth + 1):
            sv = safe_verify_source(current)
            if sv.clean:
                attempts.append(RepairAttempt(attempt=i, accepted=True, message="already clean"))
                return RepairOutcome(
                    success=True, final_source=current, attempts=attempts, stop_reason="clean"
                )

            proposed = self.patcher(current, error_trace or sv.findings[0].message, i)
            try:
                if "EVOLVE-BLOCK-BEGIN" in source:
                    proposed = apply_zoned_edit(current if i > 1 else source, proposed)
                elif proposed != source and "EVOLVE" not in source:
                    attempts.append(
                        RepairAttempt(
                            attempt=i,
                            accepted=False,
                            message="refusing unzoned full rewrite",
                        )
                    )
                    return RepairOutcome(
                        success=False,
                        final_source=current,
                        attempts=attempts,
                        stop_reason="no evolve zones",
                    )
            except LexicalZoneError as exc:
                attempts.append(RepairAttempt(attempt=i, accepted=False, message=str(exc)))
                continue

            sv2 = safe_verify_source(proposed)
            ok = sv2.clean
            attempts.append(
                RepairAttempt(
                    attempt=i,
                    accepted=ok,
                    message="safe_verify clean" if ok else f"still dirty: {[f.rule for f in sv2.findings]}",
                    candidate_hash=sv2.source_hash[:16],
                )
            )
            current = proposed
            if ok:
                return RepairOutcome(
                    success=True,
                    final_source=current,
                    attempts=attempts,
                    stop_reason="repaired",
                )

        return RepairOutcome(
            success=False,
            final_source=current,
            attempts=attempts,
            stop_reason="max_depth",
        )
