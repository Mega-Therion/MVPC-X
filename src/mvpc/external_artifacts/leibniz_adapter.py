"""Adapter for the 4Leibniz formal-claims catalog v1.

Schema ground truth: 4Leibniz issue #11 was not fetchable while this
adapter was written (a separate concurrent task owns that schema). Per
the issue-#8 brief, this adapter is built against the documented
convention: claim_id, module, declaration, status
(proved|conditional|informal|open_problem), proof_source
{repo, commit, path}, verification {lean_toolchain, project_check,
declaration_check, sorry_count, axiom_dependencies, checked_at}. This is
an ASSUMPTION, flagged here and in the final report, not a fetched fact.

This adapter never runs Lean. It only checks that the catalog *declares*
consistent, complete evidence for each claim's status.
"""

from __future__ import annotations

from typing import Any

from mvpc.external_artifacts.models import Gate, GateStatus
from mvpc.external_artifacts.provenance_checks import (
    extract_repo_commit_path,
    is_valid_commit_sha,
)
from mvpc.external_artifacts.registry import AdapterPolicy, register_adapter

ARTIFACT_TYPE = "4leibniz-formal-claims-catalog"
SUPPORTED_IDENTITIES = {"4leibniz-formal-claims-catalog-v1"}

CONTROLLED_STATUSES = {"proved", "conditional", "informal", "open_problem"}
CONTROLLED_CHECK_STATES = {"passed", "failed", "unavailable", "not_applicable"}


class LeibnizCatalogAdapter:
    artifact_type = ARTIFACT_TYPE
    supported_schema_identities = SUPPORTED_IDENTITIES

    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        return raw

    def document_provenance(self, raw: dict[str, Any]) -> dict[str, Any]:
        repo, commit, path = extract_repo_commit_path(raw.get("document_provenance"))
        return {"repo": repo, "commit": commit, "path": path}

    def run_gates(self, raw: dict[str, Any], *, policy: AdapterPolicy) -> list[Gate]:
        gates: list[Gate] = []

        # --- schema shape ---
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

        # --- document provenance ---
        doc_prov = raw.get("document_provenance")
        gates.append(self._document_provenance_gate(doc_prov, policy))

        # --- per-claim gates (aggregated, but every violation is named) ---
        gates.append(self._claim_ids_unique_gate(claims))
        gates.append(self._claim_shape_gate(claims))
        gates.append(self._claim_provenance_gate(claims, doc_prov, policy))
        gates.append(self._proved_verification_gate(claims))

        return gates

    # -- individual gates -------------------------------------------------

    def _document_provenance_gate(self, doc_prov: Any, policy: AdapterPolicy) -> Gate:
        if not isinstance(doc_prov, dict):
            return Gate(
                "document_provenance",
                GateStatus.FAILED,
                "document_provenance object is missing",
            )
        repo, commit, _path = extract_repo_commit_path(doc_prov)
        problems = []
        if not repo or not isinstance(repo, str):
            problems.append("repo is missing")
        expected_repo = policy.expected_repos.get(self.artifact_type)
        if expected_repo and repo != expected_repo:
            problems.append(
                f"repo {repo!r} does not match policy-configured {expected_repo!r}"
            )
        if not is_valid_commit_sha(commit):
            problems.append(f"commit {commit!r} is not a 40-character hex SHA")
        if problems:
            return Gate("document_provenance", GateStatus.FAILED, "; ".join(problems))
        return Gate(
            "document_provenance",
            GateStatus.PASSED,
            f"repo={repo} commit={commit}",
        )

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

    def _claim_shape_gate(self, claims: list[Any]) -> Gate:
        problems = []
        for c in claims:
            if not isinstance(c, dict):
                problems.append("claim entry is not an object")
                continue
            cid = c.get("claim_id", "<unknown>")
            for field_name in ("module", "declaration", "status"):
                if not c.get(field_name):
                    problems.append(f"{cid}: missing required field '{field_name}'")
            status = c.get("status")
            if status is not None and status not in CONTROLLED_STATUSES:
                problems.append(f"{cid}: status {status!r} is not a controlled status")
            if not isinstance(c.get("proof_source"), dict):
                problems.append(f"{cid}: missing claim-level provenance (proof_source)")
        if problems:
            return Gate("claim_required_fields", GateStatus.FAILED, "; ".join(problems))
        return Gate(
            "claim_required_fields",
            GateStatus.PASSED,
            "every claim has claim_id, module, declaration, controlled status, proof_source",
        )

    def _claim_provenance_gate(
        self, claims: list[Any], doc_prov: Any, policy: AdapterPolicy
    ) -> Gate:
        if not policy.require_claim_provenance_match:
            return Gate(
                "claim_provenance_agreement",
                GateStatus.NOT_APPLICABLE,
                "policy does not require claim-level/document-level provenance agreement",
            )
        doc_repo, _doc_commit, _doc_path = extract_repo_commit_path(
            doc_prov if isinstance(doc_prov, dict) else None
        )
        problems = []
        for c in claims:
            if not isinstance(c, dict):
                continue
            cid = c.get("claim_id", "<unknown>")
            src = c.get("proof_source")
            if not isinstance(src, dict):
                continue  # already flagged by claim_required_fields
            repo, commit, _path = extract_repo_commit_path(src)
            if not is_valid_commit_sha(commit):
                problems.append(
                    f"{cid}: proof_source.commit {commit!r} is not a 40-char hex SHA"
                )
            if doc_repo and repo and repo != doc_repo:
                problems.append(
                    f"{cid}: proof_source.repo {repo!r} disagrees with document repo {doc_repo!r}"
                )
        if problems:
            return Gate(
                "claim_provenance_agreement", GateStatus.FAILED, "; ".join(problems)
            )
        if not doc_repo:
            # Per-claim commit-format checks above ran and found nothing
            # wrong, but the repo-agreement half of this gate never had a
            # document repo to compare against — that half did not run,
            # so this must not be reported as a full PASSED (rule 5 /
            # COVENANT §1: a check that did not run must not imply it did).
            return Gate(
                "claim_provenance_agreement",
                GateStatus.NOT_APPLICABLE,
                "no document-level repo was available to compare claim-level "
                "proof_source.repo against (document_provenance is missing/invalid); "
                "per-claim commit format was checked and found no issues",
            )
        return Gate(
            "claim_provenance_agreement",
            GateStatus.PASSED,
            "all claim-level provenance records agree with document provenance",
        )

    def _proved_verification_gate(self, claims: list[Any]) -> Gate:
        problems = []
        proved_count = 0
        for c in claims:
            if not isinstance(c, dict) or c.get("status") != "proved":
                continue
            proved_count += 1
            cid = c.get("claim_id", "<unknown>")
            verification = c.get("verification")
            if not isinstance(verification, dict) or not verification:
                problems.append(
                    f"{cid}: status=proved but verification record is empty/missing"
                )
                continue
            for key in ("project_check", "declaration_check"):
                state = verification.get(key)
                if state not in CONTROLLED_CHECK_STATES:
                    problems.append(
                        f"{cid}: verification.{key}={state!r} is not a controlled check state"
                    )
                elif state in ("unavailable", "failed"):
                    problems.append(
                        f"{cid}: status=proved but verification.{key}={state} "
                        "(a proved claim requires passed/not_applicable checks)"
                    )
        if not proved_count:
            return Gate(
                "proved_claims_have_verification",
                GateStatus.NOT_APPLICABLE,
                "no claim in this catalog is labelled proved",
            )
        if problems:
            return Gate(
                "proved_claims_have_verification",
                GateStatus.FAILED,
                "; ".join(problems),
            )
        return Gate(
            "proved_claims_have_verification",
            GateStatus.PASSED,
            f"{proved_count} proved claim(s) all carry passing/not_applicable declared checks",
        )


register_adapter(LeibnizCatalogAdapter())
