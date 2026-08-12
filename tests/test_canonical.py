from mvpc.canonical import HashBuilder, canonical_json, hash_canonical


def test_canonical_json_sorts_keys():
    a = canonical_json({"b": 1, "a": {"d": 2, "c": 3}})
    b = canonical_json({"a": {"c": 3, "d": 2}, "b": 1})
    assert a == b
    assert a == '{"a":{"c":3,"d":2},"b":1}'


def test_hash_stable():
    assert hash_canonical({"x": [1, 2]}) == hash_canonical({"x": [1, 2]})


def test_hash_builder_order_independent_by_name():
    left = HashBuilder().add("a", "11").add("b", "22").digest()
    right = HashBuilder().add("b", "22").add("a", "11").digest()
    assert left == right
