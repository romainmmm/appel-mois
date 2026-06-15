import os
import tempfile
from datetime import date

from timesheet import (
    load_timesheet, save_timesheet, get_entry, set_entry,
    worked_hours, period_total, period_tips, fortnight, monday_of,
)


def _tmp():
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    f.close()
    return f.name


class TestWorkedHours:
    def test_basic(self):
        assert worked_hours("08:00", "16:00", 30) == 7.5

    def test_no_break(self):
        assert worked_hours("09:00", "17:00", 0) == 8.0

    def test_incomplete_returns_zero(self):
        assert worked_hours("", "16:00", 0) == 0.0
        assert worked_hours("08:00", "", 0) == 0.0

    def test_negative_clamped(self):
        assert worked_hours("16:00", "08:00", 0) == 0.0

    def test_fractional(self):
        assert worked_hours("08:15", "12:45", 15) == 4.25


class TestEntries:
    def test_set_and_get(self):
        data = {}
        set_entry(data, "Anna", "2026-06-15", "08:00", "16:00", 30)
        e = get_entry(data, "Anna", "2026-06-15")
        assert e == {"arrivee": "08:00", "depart": "16:00", "pause": 30, "tips": 0.0}

    def test_get_missing_is_blank(self):
        assert get_entry({}, "Bob", "2026-06-15") == {
            "arrivee": "", "depart": "", "pause": 0, "tips": 0.0}

    def test_tips_stored_and_totalled(self):
        data = {}
        set_entry(data, "Anna", "2026-06-15", "08:00", "16:00", 0, tips=25.50)
        set_entry(data, "Anna", "2026-06-16", "08:00", "16:00", 0, tips=10)
        assert get_entry(data, "Anna", "2026-06-15")["tips"] == 25.50
        days = fortnight(date(2026, 6, 15))
        assert period_tips(data, "Anna", days) == 35.5

    def test_tips_only_day_is_kept(self):
        data = {}
        set_entry(data, "Anna", "2026-06-15", "", "", 0, tips=12)
        assert get_entry(data, "Anna", "2026-06-15")["tips"] == 12.0

    def test_empty_entry_removed(self):
        data = {"Anna": {"2026-06-15": {"arrivee": "08:00", "depart": "16:00", "pause": 0}}}
        set_entry(data, "Anna", "2026-06-15", "", "", 0)
        assert "2026-06-15" not in data.get("Anna", {})


class TestPersistence:
    def test_roundtrip(self):
        path = _tmp()
        try:
            data = {}
            set_entry(data, "Anna", "2026-06-15", "08:00", "16:00", 30)
            save_timesheet(data, path)
            assert load_timesheet(path) == data
        finally:
            os.unlink(path)

    def test_missing_file(self):
        assert load_timesheet("nope_xyz.json") == {}


class TestPeriod:
    def test_fortnight_has_14_days(self):
        days = fortnight(date(2026, 6, 15))
        assert len(days) == 14
        assert days[0] == date(2026, 6, 15)
        assert days[-1] == date(2026, 6, 28)

    def test_monday_of(self):
        # 2026-06-17 is a Wednesday
        assert monday_of(date(2026, 6, 17)) == date(2026, 6, 15)

    def test_period_total(self):
        data = {}
        set_entry(data, "Anna", "2026-06-15", "08:00", "16:00", 30)  # 7.5
        set_entry(data, "Anna", "2026-06-16", "09:00", "17:00", 0)   # 8.0
        days = fortnight(date(2026, 6, 15))
        assert period_total(data, "Anna", days) == 15.5
