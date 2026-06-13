import os
import tempfile
from datetime import date

from notes import (
    ManualTask, load_notes, save_notes, manual_cleaning_tasks, merge_into_schedule,
)
from cleaning_schedule import CleaningTask


def _tmp():
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    f.close()
    return f.name


class TestPersistence:
    def test_save_and_load_roundtrip(self):
        path = _tmp()
        try:
            notes = [
                ManualTask("2026-07-15", "Ménage", 305, "tapis taché"),
                ManualTask("2026-07-16", "Autre", None, "appeler fournisseur"),
            ]
            save_notes(notes, path)
            loaded = load_notes(path)
            assert loaded == notes
        finally:
            os.unlink(path)

    def test_load_missing_file_returns_empty(self):
        assert load_notes("does_not_exist_xyz.json") == []


class TestManualCleaningTasks:
    def test_menage_and_serviette_become_tasks(self):
        notes = [
            ManualTask("2026-07-15", "Ménage", 305, "tapis"),
            ManualTask("2026-07-15", "Serviette", 207, ""),
        ]
        tasks = manual_cleaning_tasks(notes)
        d = date(2026, 7, 15)
        assert d in tasks
        rooms = sorted(t.room for t in tasks[d])
        assert rooms == [207, 305]
        assert all(t.kind == "manuel" for t in tasks[d])

    def test_autre_is_excluded(self):
        notes = [ManualTask("2026-07-15", "Autre", None, "note libre")]
        assert manual_cleaning_tasks(notes) == {}

    def test_chien_appears_on_sheet(self):
        notes = [ManualTask("2026-07-15", "Chien", 210, "petit chien")]
        tasks = manual_cleaning_tasks(notes)
        d = date(2026, 7, 15)
        assert d in tasks
        assert tasks[d][0].room == 210
        assert "Chien" in tasks[d][0].night_label

    def test_menage_without_room_excluded(self):
        notes = [ManualTask("2026-07-15", "Ménage", None, "oops")]
        assert manual_cleaning_tasks(notes) == {}

    def test_label_includes_comment(self):
        notes = [ManualTask("2026-07-15", "Ménage", 305, "tapis taché")]
        task = manual_cleaning_tasks(notes)[date(2026, 7, 15)][0]
        assert "Ménage" in task.night_label
        assert "tapis taché" in task.night_label


class TestMerge:
    def test_merge_adds_to_existing_day(self):
        d = date(2026, 7, 15)
        sched = {d: [CleaningTask(101, 100, "depart", "b")]}
        notes = [ManualTask("2026-07-15", "Ménage", 305, "")]
        merged = merge_into_schedule(sched, notes)
        rooms = sorted(t.room for t in merged[d])
        assert rooms == [101, 305]

    def test_merge_creates_new_day(self):
        sched = {}
        notes = [ManualTask("2026-07-20", "Serviette", 210, "")]
        merged = merge_into_schedule(sched, notes)
        assert date(2026, 7, 20) in merged

    def test_merge_does_not_mutate_input(self):
        d = date(2026, 7, 15)
        sched = {d: [CleaningTask(101, 100, "depart", "b")]}
        notes = [ManualTask("2026-07-15", "Ménage", 305, "")]
        merge_into_schedule(sched, notes)
        assert len(sched[d]) == 1  # original untouched
