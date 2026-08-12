from mvpc.core.claim_adapter import ProposerType, TargetBackend, adapt_claim


def test_adapt_lean_text():
    src = "theorem t : True := by\n  trivial\n"
    claim = adapt_claim(text=src, target_backend="lean4", proposer_type="synthetic")
    assert claim.proposer_type is ProposerType.SYNTHETIC
    assert claim.target_backend is TargetBackend.LEAN4
    assert claim.claim_id
    assert "theorem" in claim.header_code


def test_proposer_does_not_change_hash_identity_of_body():
    a = adapt_claim(text="theorem t : True := by trivial", proposer_type="biological")
    b = adapt_claim(text="theorem t : True := by trivial", proposer_type="synthetic")
    assert a.content_hash() == b.content_hash()
