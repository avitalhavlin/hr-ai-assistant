import pytest

from app.services.update_utils import apply_updates


class _Dummy:
    def __init__(self):
        self.name = "original"
        self.note = "original-note"


def test_apply_updates_sets_fields():
    obj = _Dummy()

    apply_updates(obj, {"name": "new"})

    assert obj.name == "new"
    assert obj.note == "original-note"


def test_apply_updates_rejects_null_by_default():
    obj = _Dummy()

    with pytest.raises(ValueError):
        apply_updates(obj, {"name": None})


def test_apply_updates_allows_null_for_nullable_fields():
    obj = _Dummy()

    apply_updates(obj, {"note": None}, nullable_fields=frozenset({"note"}))

    assert obj.note is None
