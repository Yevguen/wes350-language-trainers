from types import SimpleNamespace

import pytest

from access_utils import ACCESS_MARGIN, canon, user_has_access


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ES350", "es350"),
        ("eng200", "en200"),
        ("EN200", "en200"),
        ("all4", "all"),
        ("all_trainers", "all"),
        ("Fr200", "fr200"),
    ],
)
def test_canon_normalizes_plan_codes(raw, expected):
    assert canon(raw) == expected


def test_access_margin_is_24_hours():
    assert ACCESS_MARGIN.total_seconds() == 24 * 60 * 60


def test_superuser_bypasses_database_lookup():
    user = SimpleNamespace(is_superuser=True)

    # Session is deliberately None. An administrator should return True
    # before any database access is attempted.
    assert user_has_access(None, user, "es350") is True
