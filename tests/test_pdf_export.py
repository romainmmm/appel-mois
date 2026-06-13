import os
import tempfile
from datetime import date

from cleaning_schedule import CleaningTask
from staff import Worker
from distribution import assign_day
from pdf_export import build_month_pdf, build_day_pdf


def _task(room, kind="depart"):
    return CleaningTask(room=room, floor=(room // 100) * 100, kind=kind, booking_id="b")


def _everyday(n):
    return {wd: n for wd in range(7)}


def _workers():
    return [
        Worker("Anna", 1, home_floor=100, floor_strict=True, weekly_max=_everyday(5)),
        Worker("Oumar", 3, weekly_max=_everyday(10)),
    ]


def _schedule():
    return {
        date(2026, 7, 6): [_task(101), _task(102), _task(301)],
        date(2026, 7, 7): [_task(103, "service")],
    }


def _is_pdf(path):
    with open(path, "rb") as f:
        return f.read(5) == b"%PDF-"


class TestMonthPdf:
    def test_creates_valid_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            build_month_pdf(_schedule(), _workers(), path)
            assert os.path.getsize(path) > 0
            assert _is_pdf(path)
        finally:
            os.unlink(path)


class TestDayPdf:
    def test_creates_valid_pdf(self):
        day = date(2026, 7, 6)
        da = assign_day(_schedule()[day], _workers(), day)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            build_day_pdf(da, path)
            assert os.path.getsize(path) > 0
            assert _is_pdf(path)
        finally:
            os.unlink(path)
