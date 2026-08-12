from mvpc.core.fingerprint import FingerprintSession


def test_verify_twice_stable():
    s = FingerprintSession()
    assert s.verify_twice()
    assert not s.voided
    assert s.pre and s.post
    assert s.pre.mvpc_package_hash == s.post.mvpc_package_hash
