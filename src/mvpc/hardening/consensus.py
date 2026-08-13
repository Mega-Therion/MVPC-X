"""Layer 2a: multi-engine consensus voting."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List

from mvpc.trust_verdicts import TrustVerdict


@dataclass
class EngineBallot:
    engine: str
    trust_verdict: str
    pass_: bool
    detail: str = ""


@dataclass
class ConsensusResult:
    agreed: bool
    required: int
    pass_count: int
    fail_count: int
    ballots: List[EngineBallot] = field(default_factory=list)
    consensus_verdict: str = TrustVerdict.INCONCLUSIVE.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "agreed": self.agreed,
            "required": self.required,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "consensus_verdict": self.consensus_verdict,
            "ballots": [
                {
                    "engine": b.engine,
                    "trust_verdict": b.trust_verdict,
                    "pass": b.pass_,
                    "detail": b.detail,
                }
                for b in self.ballots
            ],
        }


def multi_engine_vote(
    claim_payload: dict[str, Any],
    engines: Dict[str, Callable[[dict[str, Any]], EngineBallot]],
    *,
    quorum: int | None = None,
) -> ConsensusResult:
    ballots: List[EngineBallot] = []
    for name, fn in engines.items():
        try:
            ballots.append(fn(claim_payload))
        except Exception as exc:
            ballots.append(
                EngineBallot(
                    engine=name,
                    trust_verdict=TrustVerdict.UNSAFE_TO_VERIFY.value,
                    pass_=False,
                    detail=str(exc),
                )
            )

    need = (len(ballots) // 2) + 1 if quorum is None else quorum
    passes = [b for b in ballots if b.pass_]
    fails = [b for b in ballots if not b.pass_]
    agreed = len(passes) >= need

    if agreed:
        verdict = TrustVerdict.EVIDENCE_SUPPORTED.value
        if all(b.trust_verdict == TrustVerdict.FORMALLY_CHECKED.value for b in passes):
            verdict = TrustVerdict.FORMALLY_CHECKED.value
        elif any(b.trust_verdict == TrustVerdict.COMPUTATION_VERIFIED.value for b in passes):
            verdict = TrustVerdict.COMPUTATION_VERIFIED.value
    elif len(passes) and len(fails):
        verdict = TrustVerdict.CONFLICTING_VERDICTS.value
    elif fails:
        verdict = fails[0].trust_verdict
    else:
        verdict = TrustVerdict.INCONCLUSIVE.value

    return ConsensusResult(
        agreed=agreed,
        required=need,
        pass_count=len(passes),
        fail_count=len(fails),
        ballots=ballots,
        consensus_verdict=verdict,
    )
