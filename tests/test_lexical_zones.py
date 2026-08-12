import pytest

from mvpc.core.lexical_zones import LexicalZoneError, apply_zoned_edit

ORIG = """theorem t : True := by
EVOLVE-BLOCK-BEGIN helpers
have h : True := by trivial
EVOLVE-BLOCK-END
exact h
"""


def test_zoned_edit_ok():
    proposed = ORIG.replace("trivial", "apply True.intro")
    out = apply_zoned_edit(ORIG, proposed)
    assert "True.intro" in out


def test_zoned_edit_rejects_outside():
    proposed = ORIG.replace("theorem t : True", "theorem t : False")
    with pytest.raises(LexicalZoneError):
        apply_zoned_edit(ORIG, proposed)
