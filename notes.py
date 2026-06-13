"""Manual notes & tasks added by the manager, persisted to notes.json.

  - Type "Ménage" / "Serviette" : a manual cleaning task for a specific room
    and date; it is merged into that day's plan and appears on the day sheet.
  - Type "Autre" : a free-text note (saved for reference, NOT shown on the
    day sheet).

Saved on every change so nothing is lost when the app closes.
"""

import json
from dataclasses import dataclass, asdict
from datetime import date

from cleaning_schedule import CleaningTask

TYPES = ["Ménage", "Serviette", "Autre"]
_SHEET_TYPES = {"Ménage", "Serviette"}   # types that appear on the day sheet


@dataclass
class ManualTask:
    date: str            # ISO date (YYYY-MM-DD)
    type: str            # "Ménage" | "Serviette" | "Autre"
    room: int | None = None
    comment: str = ""


def load_notes(path: str) -> list[ManualTask]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [ManualTask(**d) for d in data]


def save_notes(notes: list[ManualTask], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(n) for n in notes], f, ensure_ascii=False, indent=2)


def manual_cleaning_tasks(notes: list[ManualTask]) -> dict[date, list[CleaningTask]]:
    """Convert sheet-visible manual tasks (Ménage/Serviette) into CleaningTasks."""
    result: dict[date, list[CleaningTask]] = {}
    for n in notes:
        if n.type not in _SHEET_TYPES or not n.room:
            continue
        d = date.fromisoformat(n.date)
        label = n.type + (f": {n.comment}" if n.comment else "")
        task = CleaningTask(
            room=int(n.room), floor=(int(n.room) // 100) * 100,
            kind="manuel", booking_id="manuel", night_label=label,
        )
        result.setdefault(d, []).append(task)
    return result


def merge_into_schedule(
    schedule: dict[date, list[CleaningTask]],
    notes: list[ManualTask],
) -> dict[date, list[CleaningTask]]:
    """Return a new schedule with manual cleaning tasks merged in."""
    merged = {d: list(tasks) for d, tasks in schedule.items()}
    for d, tasks in manual_cleaning_tasks(notes).items():
        merged.setdefault(d, []).extend(tasks)
    for d in merged:
        merged[d].sort(key=lambda t: t.room)
    return merged
