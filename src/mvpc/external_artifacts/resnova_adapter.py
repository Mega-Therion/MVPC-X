"""Adapter for the Res-Nova Evidence Atlas / claim ledger v1.

Schema shape note (Phase 4 discrepancy record): the delivered reference
file at Res-Nova evidence/v1/claim-ledger.json uses a single top-level
"schema_version" string (e.g. "res-nova-claim-ledger-v1"), an "atlas_id",
and a "generation" block carrying source_commit_sha rather than a
top-level "document_provenance" object. It also has no document-level
"repo" field — only per-claim "provenance": {"repository", "commit_sha"}.
epistemic_status values actually observed there: derived, conditional,
open, refuted. "empirically_supported" and "proposal" appear in the
originally suggested status vocabulary but were not observed in the real
file; this adapter still supports them since the schema contract (per
issue #50 in Res-Nova) allows the full six-way vocabulary.

This adapter's fixtures (tests/fixtures/external_artifacts) synthesize a
document_provenance object explicitly (rather than only per-claim
provenance) because MVPC-X's document-level provenance gate (issue #8
Phase 4: "immutable document ... provenance") needs *some* document-level
repo/commit pair to check; where an atlas omits an explicit
document_provenance object, this adapter falls back to the "generation"
block's source_commit_sha and to majority per-claim provenance.repository,
and flags the fallback in the gate detail rather than silently upgrading
it to a full pass.

This adapter never assesses the substantive physics/derivation content.
It only checks declared-artifact completeness and internal consistency.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from mvpc.external_artifacts.models import Gate, GateStatus
from mvpc.external_artifacts.provenance_checks import (
    extract_repo_commit_path,
    is_valid_commit_sha,
)
from mvpc.external_artifacts.registry import AdapterPolicy, register_adapter

ARTIFACT_TYPE = "resnova-evidence-atlas"
SUPPORTED_IDENTITIES = {"res-nova-claim-ledger-v1"}

CONTROLLED_STATUSES = {
    "derived",
    "empirically_supported",
    "conditional",
    "proposal",
    "open",
    "refuted",
}


class ResNovaAtlasAdapter:
    artifact_type = ARTIFACT_TYPE
    supported_schema_identities = SUPPORTED_IDENTITIES

    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        return raw

    def _resolve_document_provenance(
        self, raw: dict[str, Any]
    ) -> tuple[dict[str, Any], bool]:
        """Return (provenance_dict, was_explicit)."""
        doc_prov = raw.get("document_provenance")
        if isinstance(doc_prov, dict):
            repo, commit, path = extract_repo_commit_path(doc_prov)
            return {"repo": repo, "commit": commit, "path": path}, True

        # Fallback: generation.source_commit_sha + majority claim repository.
        generation = (
            raw.get("generation") if isinstance(raw.get("generation"), dict) else {}
        )
        commit = generation.get("source_commit_sha")
        claims = raw.get("claims") if isinstance(raw.get("claims"), list) else []
        repos = [
            c.get("provenance", {}).get("repository")
            for c in claims
            if isinstance(c, dict) and isinstance(c.get("provenance"), dict)
        ]
        repo = Counter([r for r in repos if r]).most_common(1)
        repo_value = repo[0][0] if repo else None
        return {
            "repo": repo_value,
            "commit": commit,
            "path": generation.get("source"),
        }, False

    def document_provenance(self, raw: dict[str, Any]) -> dict[str, Any]:
        prov, _explicit = self._resolve_document_provenance(raw)
        return prov

    def run_gates(self, raw: dict[str, Any], *, policy: AdapterPolicy) -> list[Gate]:
        gates: list[Gate] = []

        claims = raw.get("claims")
        if not isinstance(claims, list):
            gates.append(
                Gate(
                    "schema_shape",
                    GateStatus.FAILED,
                    "top-level 'claims' array is missing or not a list",
                )
            )
            return gates
        gates.append(
            Gate(
                "schema_shape",
                GateStatus.PASSED,
                f"{len(claims)} claim record(s) found",
            )
        )

        gates.append(self._document_provenance_gate(raw, policy))
        gates.append(self._claim_ids_unique_gate(claims))
        gates.append(self._source_locator_gate(claims))
        gates.append(self._controlled_status_gate(claims))
        gates.append(self._claim_provenance_gate(raw, claims, policy))
        gates.append(self._derived_evidence_gate(claims))
        gates.append(self._empirically_supported_gate(claims))
        gates.append(self._conditional_gate(claims))
        gates.append(self._proposal_gate(claims))
        gates.append(self._open_gate(claims))
        gates.append(self._refuted_gate(claims))

        return gates

    # -- individual gates -------------------------------------------------

    def _document_provenance_gate(
        self, raw: dict[str, Any], policy: AdapterPolicy
    ) -> Gate:
        prov, explicit = self._resolve_document_provenance(raw)
        repo, commit = prov["repo"], prov["commit"]
        problems = []
        if not repo:
            problems.append(
                "no document-level or majority claim-level repo could be resolved"
            )
        expected_repo = policy.expected_repos.get(self.artifact_type)
        if expected_repo and repo and repo != expected_repo:
            problems.append(
                f"repo {repo!r} does not match policy-configured {expected_repo!r}"
            )
        if not is_valid_commit_sha(commit):
            problems.append(f"commit {commit!r} is not a 40-character hex SHA")
        if problems:
            return Gate("document_provenance", GateStatus.FAILED, "; ".join(problems))
        detail = f"repo={repo} commit={commit}"
        if not explicit:
            detail += " (resolved via generation/claim fallback, no explicit document_provenance object)"
        return Gate("document_provenance", GateStatus.PASSED, detail)

    def _claim_ids_unique_gate(self, claims: list[Any]) -> Gate:
        ids = [c.get("claim_id") for c in claims if isinstance(c, dict)]
        missing = sum(1 for i in ids if not i)
        dupes = {i for i in ids if ids.count(i) > 1 and i}
        if missing:
            return Gate(
                "claim_ids", GateStatus.FAILED, f"{missing} claim(s) missing claim_id"
            )
        if dupes:
            return Gate(
                "claim_ids",
                GateStatus.FAILED,
                f"duplicate claim_id(s): {sorted(dupes)}",
            )
        return Gate(
            "claim_ids", GateStatus.PASSED, f"{len(ids)} unique stable claim_id(s)"
        )

    def _source_locator_gate(self, claims: list[Any]) -> Gate:
        problems = []
        for c in claims:
            if not isinstance(c, dict):
                continue
            cid = c.get("claim_id", "<unknown>")
            locators = c.get("source_locators")
            if not isinstance(locators, list) or len(locators) == 0:
                problems.append(f"{cid}: no source_locators")
        if problems:
            return Gate(
                "source_locators_present", GateStatus.FAILED, "; ".join(problems)
            )
        return Gate(
            "source_locators_present",
            GateStatus.PASSED,
            "every claim carries one or more source locators",
        )

    def _controlled_status_gate(self, claims: list[Any]) -> Gate:
        problems = []
        for c in claims:
            if not isinstance(c, dict):
                continue
            cid = c.get("claim_id", "<unknown>")
            status = c.get("epistemic_status")
            if status not in CONTROLLED_STATUSES:
                problems.append(
                    f"{cid}: epistemic_status {status!r} is not a controlled status"
                )
        if problems:
            return Gate(
                "controlled_epistemic_status", GateStatus.FAILED, "; ".join(problems)
            )
        return Gate(
            "controlled_epistemic_status",
            GateStatus.PASSED,
            "every claim carries a controlled epistemic_status",
        )

    def _claim_provenance_gate(
        self, raw: dict[str, Any], claims: list[Any], policy: AdapterPolicy
    ) -> Gate:
        if not policy.require_claim_provenance_match:
            return Gate(
                "claim_provenance_agreement",
                GateStatus.NOT_APPLICABLE,
                "policy does not require claim-level/document-level provenance agreement",
            )
        doc_prov, _explicit = self._resolve_document_provenance(raw)
        doc_repo = doc_prov["repo"]
        problems = []
        for c in claims:
            if not isinstance(c, dict):
                continue
            cid = c.get("claim_id", "<unknown>")
            prov = c.get("provenance")
            if not isinstance(prov, dict):
                problems.append(f"{cid}: missing claim-level provenance")
                continue
            repo = prov.get("repository")
            commit = prov.get("commit_sha")
            if not is_valid_commit_sha(commit):
                problems.append(
                    f"{cid}: provenance.commit_sha {commit!r} is not a 40-char hex SHA"
                )
            if doc_repo and repo and repo != doc_repo:
                problems.append(
                    f"{cid}: provenance.repository {repo!r} disagrees with document repo {doc_repo!r}"
                )
        if problems:
            return Gate(
                "claim_provenance_agreement", GateStatus.FAILED, "; ".join(problems)
            )
        if not doc_repo:
            return Gate(
                "claim_provenance_agreement",
                GateStatus.NOT_APPLICABLE,
                "no document-level repo was resolvable to compare claim-level "
                "provenance.repository against; per-claim commit format was "
                "checked and found no issues",
            )
        return Gate(
            "claim_provenance_agreement",
            GateStatus.PASSED,
            "all claim-level provenance records agree with document provenance",
        )

    def _derived_evidence_gate(self, claims: list[Any]) -> Gate:
        relevant = [
            c
            for c in claims
            if isinstance(c, dict) and c.get("epistemic_status") == "derived"
        ]
        if not relevant:
            return Gate(
                "derived_requires_derivation_evidence",
                GateStatus.NOT_APPLICABLE,
                "no derived claims present",
            )
        problems = []
        for c in relevant:
            cid = c.get("claim_id", "<unknown>")
            evidence = c.get("evidence_references")
            has_derivation = isinstance(evidence, list) and any(
                isinstance(e, dict)
                and e.get("kind") in ("derivation", "calculation", "formal_proof")
                for e in evidence
            )
            if not has_derivation:
                problems.append(
                    f"{cid}: no identified derivation/calculation/formal-proof evidence"
                )
            if not c.get("assumptions"):
                problems.append(
                    f"{cid}: derived claim declares no assumptions/model choices"
                )
        if problems:
            return Gate(
                "derived_requires_derivation_evidence",
                GateStatus.FAILED,
                "; ".join(problems),
            )
        return Gate(
            "derived_requires_derivation_evidence",
            GateStatus.PASSED,
            f"{len(relevant)} derived claim(s) all carry derivation evidence and declared assumptions",
        )

    def _empirically_supported_gate(self, claims: list[Any]) -> Gate:
        relevant = [
            c
            for c in claims
            if isinstance(c, dict)
            and c.get("epistemic_status") == "empirically_supported"
        ]
        if not relevant:
            return Gate(
                "empirically_supported_requires_test_record",
                GateStatus.NOT_APPLICABLE,
                "no empirically_supported claims present",
            )
        problems = []
        for c in relevant:
            cid = c.get("claim_id", "<unknown>")
            evidence = c.get("evidence_references")
            has_observational = isinstance(evidence, list) and any(
                isinstance(e, dict)
                and e.get("kind") in ("observational_data", "reproduction_run")
                for e in evidence
            )
            if not has_observational:
                problems.append(f"{cid}: no identified observational/data evidence")
            fal = c.get("falsifiability")
            if not isinstance(fal, dict):
                problems.append(f"{cid}: missing falsifiability/test record")
                continue
            if not fal.get("scope"):
                problems.append(f"{cid}: falsifiability record has no scope")
            if fal.get("current_result") in (None, ""):
                problems.append(f"{cid}: falsifiability.current_result is null/empty")
        if problems:
            return Gate(
                "empirically_supported_requires_test_record",
                GateStatus.FAILED,
                "; ".join(problems),
            )
        return Gate(
            "empirically_supported_requires_test_record",
            GateStatus.PASSED,
            f"{len(relevant)} empirically_supported claim(s) all carry scope + non-null test result",
        )

    def _conditional_gate(self, claims: list[Any]) -> Gate:
        relevant = [
            c
            for c in claims
            if isinstance(c, dict) and c.get("epistemic_status") == "conditional"
        ]
        if not relevant:
            return Gate(
                "conditional_names_conditions",
                GateStatus.NOT_APPLICABLE,
                "no conditional claims present",
            )
        problems = [
            f"{c.get('claim_id', '<unknown>')}: no named conditions/assumptions"
            for c in relevant
            if not c.get("assumptions")
        ]
        if problems:
            return Gate(
                "conditional_names_conditions", GateStatus.FAILED, "; ".join(problems)
            )
        return Gate(
            "conditional_names_conditions",
            GateStatus.PASSED,
            f"{len(relevant)} conditional claim(s) all name their conditions/assumptions",
        )

    def _proposal_gate(self, claims: list[Any]) -> Gate:
        relevant = [
            c
            for c in claims
            if isinstance(c, dict) and c.get("epistemic_status") == "proposal"
        ]
        if not relevant:
            return Gate(
                "proposal_not_overclaimed",
                GateStatus.NOT_APPLICABLE,
                "no proposal claims present",
            )
        problems = []
        for c in relevant:
            cid = c.get("claim_id", "<unknown>")
            if not c.get("source_locators"):
                problems.append(f"{cid}: proposal retains no source locator")
        if problems:
            return Gate(
                "proposal_not_overclaimed", GateStatus.FAILED, "; ".join(problems)
            )
        return Gate(
            "proposal_not_overclaimed",
            GateStatus.PASSED,
            f"{len(relevant)} proposal claim(s) retain a source locator and are rendered as proposal only",
        )

    def _open_gate(self, claims: list[Any]) -> Gate:
        relevant = [
            c
            for c in claims
            if isinstance(c, dict) and c.get("epistemic_status") == "open"
        ]
        if not relevant:
            return Gate(
                "open_identifies_unresolved_problem",
                GateStatus.NOT_APPLICABLE,
                "no open claims present",
            )
        problems = []
        for c in relevant:
            cid = c.get("claim_id", "<unknown>")
            fal = c.get("falsifiability")
            limitation = c.get("limitations")
            names_problem = (isinstance(fal, dict) and fal.get("scope")) or limitation
            if not names_problem:
                problems.append(
                    f"{cid}: open claim does not identify the unresolved evidence/derivation/test problem"
                )
        if problems:
            return Gate(
                "open_identifies_unresolved_problem",
                GateStatus.FAILED,
                "; ".join(problems),
            )
        return Gate(
            "open_identifies_unresolved_problem",
            GateStatus.PASSED,
            f"{len(relevant)} open claim(s) retained (never promoted) and each names its unresolved problem",
        )

    def _refuted_gate(self, claims: list[Any]) -> Gate:
        relevant = [
            c
            for c in claims
            if isinstance(c, dict) and c.get("epistemic_status") == "refuted"
        ]
        if not relevant:
            return Gate(
                "refuted_retained_with_evidence",
                GateStatus.NOT_APPLICABLE,
                "no refuted claims present",
            )
        problems = []
        for c in relevant:
            cid = c.get("claim_id", "<unknown>")
            evidence = c.get("evidence_references")
            fal = c.get("falsifiability")
            has_contradiction = isinstance(fal, dict) and fal.get("current_result") in (
                "contradicted",
                "failed",
            )
            has_evidence = isinstance(evidence, list) and len(evidence) > 0
            if not (has_contradiction and has_evidence):
                problems.append(
                    f"{cid}: refuted claim lacks identified contradictory/failed evidence"
                )
        if problems:
            return Gate(
                "refuted_retained_with_evidence", GateStatus.FAILED, "; ".join(problems)
            )
        return Gate(
            "refuted_retained_with_evidence",
            GateStatus.PASSED,
            f"{len(relevant)} refuted claim(s) retained (never dropped) with identified contradictory evidence",
        )


register_adapter(ResNovaAtlasAdapter())
