import os
import tempfile

from extra_staff import ExtraEmployee, load_extra_staff, save_extra_staff


def _tmp():
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    f.close()
    return f.name


def test_roundtrip():
    path = _tmp()
    try:
        staff = [ExtraEmployee("Sophie", "Accueil"), ExtraEmployee("Marc", "Maintenance")]
        save_extra_staff(staff, path)
        assert load_extra_staff(path) == staff
    finally:
        os.unlink(path)


def test_missing_file_returns_empty():
    assert load_extra_staff("nope_extra_xyz.json") == []


def test_role_optional():
    path = _tmp()
    try:
        save_extra_staff([ExtraEmployee("Sophie")], path)
        loaded = load_extra_staff(path)
        assert loaded[0].name == "Sophie"
        assert loaded[0].role == ""
    finally:
        os.unlink(path)
