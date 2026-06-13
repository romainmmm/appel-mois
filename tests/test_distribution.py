from datetime import date

import pytest

from cleaning_schedule import CleaningTask
from staff import Worker
from distribution import assign_day


def _task(room, kind="depart"):
    return CleaningTask(room=room, floor=(room // 100) * 100, kind=kind, booking_id="b")


# A Monday (2026-07-06 is a Monday)
MONDAY = date(2026, 7, 6)
TUESDAY = date(2026, 7, 7)


def _everyday(n):
    return {wd: n for wd in range(7)}


class TestBasicAssignment:
    def test_home_floor_assigned_first(self):
        anna = Worker("Anna", 1, home_floor=100, floor_strict=True, weekly_max=_everyday(5))
        isa = Worker("Isabelle", 2, home_floor=200, weekly_max=_everyday(13))
        tasks = [_task(101), _task(102), _task(201)]
        result = assign_day(tasks, [anna, isa], MONDAY)
        assert {t.room for t in result.assignments["Anna"]} == {101, 102}
        assert {t.room for t in result.assignments["Isabelle"]} == {201}
        assert result.unassigned == []

    def test_respects_daily_cap(self):
        anna = Worker("Anna", 1, home_floor=100, floor_strict=True, weekly_max=_everyday(2))
        oumar = Worker("Oumar", 3, weekly_max=_everyday(10))
        tasks = [_task(101), _task(102), _task(103), _task(104)]
        result = assign_day(tasks, [anna, oumar], MONDAY)
        # Anna capped at 2 (floor 100 only), Oumar (flexible) takes the rest
        assert len(result.assignments["Anna"]) == 2
        assert {t.room for t in result.assignments["Oumar"]} == {103, 104}


class TestFloorStrict:
    def test_strict_worker_never_leaves_home_floor(self):
        anna = Worker("Anna", 1, home_floor=100, floor_strict=True, weekly_max=_everyday(8))
        tasks = [_task(201), _task(202)]  # no floor-100 rooms
        result = assign_day(tasks, [anna], MONDAY)
        assert result.assignments["Anna"] == []
        assert {t.room for t in result.unassigned} == {201, 202}

    def test_flexible_home_worker_can_overflow(self):
        isa = Worker("Isabelle", 2, home_floor=200, floor_strict=False, weekly_max=_everyday(13))
        tasks = [_task(201), _task(301), _task(401)]
        result = assign_day(tasks, [isa], MONDAY)
        # Isabelle takes her floor 200 plus overflow to 300/400 since flexible
        assert {t.room for t in result.assignments["Isabelle"]} == {201, 301, 401}


class TestSelectionOrder:
    def test_fills_in_selection_order(self):
        # two flexible workers, order decides who fills first
        w1 = Worker("First", 1, weekly_max=_everyday(2))
        w2 = Worker("Second", 2, weekly_max=_everyday(10))
        tasks = [_task(301), _task(302), _task(304), _task(305)]
        result = assign_day(tasks, [w1, w2], MONDAY)
        assert len(result.assignments["First"]) == 2
        assert len(result.assignments["Second"]) == 2


class TestAvailability:
    def test_unavailable_worker_skipped(self):
        # Anna off on Tuesday
        anna = Worker("Anna", 1, home_floor=100, floor_strict=True,
                      weekly_max={0: 5, 2: 5, 4: 5, 3: 8, 5: 8, 6: 8})  # no Tuesday(1)
        oumar = Worker("Oumar", 3, weekly_max=_everyday(10))
        tasks = [_task(101), _task(102)]
        result = assign_day(tasks, [anna, oumar], TUESDAY)
        assert "Anna" not in result.assignments or result.assignments["Anna"] == []
        # Oumar (flexible) covers floor 100 rooms in Anna's absence
        assert {t.room for t in result.assignments["Oumar"]} == {101, 102}

    def test_day_off_override(self):
        anna = Worker("Anna", 1, home_floor=100, floor_strict=True,
                      weekly_max=_everyday(5), days_off=[MONDAY.isoformat()])
        oumar = Worker("Oumar", 3, weekly_max=_everyday(10))
        tasks = [_task(101)]
        result = assign_day(tasks, [anna, oumar], MONDAY)
        assert result.assignments.get("Anna", []) == []
        assert {t.room for t in result.assignments["Oumar"]} == {101}


class TestOverflowToManagers:
    def test_leftover_rooms_unassigned(self):
        anna = Worker("Anna", 1, home_floor=100, floor_strict=True, weekly_max=_everyday(1))
        tasks = [_task(101), _task(102), _task(103)]
        result = assign_day(tasks, [anna], MONDAY)
        assert len(result.assignments["Anna"]) == 1
        assert len(result.unassigned) == 2
