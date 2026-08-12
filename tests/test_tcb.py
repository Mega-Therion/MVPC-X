from mvpc.tcb import BackendTCB, TCBDeclaration, TrustPolicy


def test_default_limitations_present():
    tcb = TCBDeclaration(mvpc_version="8.0.0-dev")
    assert tcb.limitations
    assert tcb.hash()


def test_backend_and_policy_allow():
    tcb = TCBDeclaration(
        mvpc_version="8.0.0-dev",
        backends=[BackendTCB(name="lean", version="4.0.0", binary_hash="abc")],
    )
    assert tcb.to_dict()["backends"][0]["name"] == "lean"
    policy = TrustPolicy(policy_id="t1", accepted_backend_hashes={"lean": "abc"})
    assert policy.allows_backend("lean", "abc")
    assert not policy.allows_backend("lean", "nope")
