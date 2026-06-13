"""Employees who are NOT part of the housekeeping team but still log hours
(e.g. front-desk / reception). They appear in the timesheet only, never in the
room distribution. Persisted to extra_employees.json.
"""

import json
from dataclasses import dataclass, asdict


@dataclass
class ExtraEmployee:
    name: str
    role: str = ""


def load_extra_staff(path: str) -> list[ExtraEmployee]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [ExtraEmployee(**d) for d in data]


def save_extra_staff(staff: list[ExtraEmployee], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(s) for s in staff], f, ensure_ascii=False, indent=2)
