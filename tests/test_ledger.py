import pytest

from mvpc.ledger import EvidenceLedger


def test_ledger_chain():
    led = EvidenceLedger()
    e1 = led.append_witness({"verdict": "FORMALLY_CHECKED", "h": "a"})
    e2 = led.append_witness({"verdict": "FORMALLY_CHECKED", "h": "b"})
    assert e2.previous_hash == e1.entry_hash
    assert led.verify_chain() == []


def test_fork_rejected():
    led = EvidenceLedger()
    e1 = led.append_witness({"h": 1})
    tip = e1.entry_hash
    led.append("witness", {"h": 2})
    with pytest.raises(ValueError, match="fork detected"):
        led2 = EvidenceLedger()
        led2.entries = list(led.entries[:1])
        led2._by_prev = {tip: ["existing_child"]}
        led2.append("witness", {"h": 3})
