from mvpc.traceability import (
    ArtifactKind,
    ProvenanceLabel,
    TraceLink,
    TraceabilityChain,
)


def test_ai_mapping_requires_approval():
    chain = TraceabilityChain()
    chain.add(
        TraceLink(
            artifact_id="S-1",
            kind=ArtifactKind.STRUCTURED_CLAIM,
            content_hash="h1",
            provenance=ProvenanceLabel.AI_PROPOSED,
        )
    )
    assert chain.unapproved_ai_mappings()
    chain.approve("S-1", approver="auditor", scope="mapping fidelity")
    assert not chain.unapproved_ai_mappings()


def test_complete_formal_chain():
    chain = TraceabilityChain()
    for i, kind in enumerate(
        [
            ArtifactKind.NATURAL_LANGUAGE_CLAIM,
            ArtifactKind.STRUCTURED_CLAIM,
            ArtifactKind.FORMAL_STATEMENT,
            ArtifactKind.PROOF_OR_CHECKER_RESULT,
        ]
    ):
        chain.add(
            TraceLink(
                artifact_id=f"A-{i}",
                kind=kind,
                content_hash=f"h{i}",
                provenance=ProvenanceLabel.HUMAN,
                human_approved=True,
            )
        )
    assert chain.is_complete_for_formal()
    assert "STRUCTURED_CLAIM" in chain.render_table()
