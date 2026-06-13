"""Staff timesheet: per-employee, per-day arrival/departure/break, persisted.

Stored as: { employee_name: { "YYYY-MM-DD": {"arrivee": "HH:MM",
                                              "depart": "HH:MM",
                                              "pause": <minutes int>} } }
Saved on every change so nothing is lost when the app closes.
"""

import json
from datetime import datetime, date, timedelta


def load_timesheet(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_timesheet(data: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_entry(data: dict, employee: str, iso: str) -> dict:
    """Return the entry for an employee/date, or a blank one."""
    return data.get(employee, {}).get(iso, {"arrivee": "", "depart": "", "pause": 0})


def set_entry(data: dict, employee: str, iso: str,
              arrivee: str, depart: str, pause: int) -> None:
    """Store an entry; remove it entirely if the day is empty."""
    if not arrivee and not depart and not pause:
        if employee in data and iso in data[employee]:
            del data[employee][iso]
        return
    data.setdefault(employee, {})[iso] = {
        "arrivee": arrivee or "",
        "depart": depart or "",
        "pause": int(pause or 0),
    }


def worked_hours(arrivee: str, depart: str, pause_min: int = 0) -> float:
    """Hours worked = (depart - arrivee) - break. Returns 0 if incomplete/invalid."""
    if not arrivee or not depart:
        return 0.0
    try:
        a = datetime.strptime(arrivee[:5], "%H:%M")
        d = datetime.strptime(depart[:5], "%H:%M")
    except (ValueError, TypeError):
        return 0.0
    minutes = (d - a).total_seconds() / 60 - (pause_min or 0)
    if minutes <= 0:
        return 0.0
    return round(minutes / 60, 2)


def period_total(data: dict, employee: str, dates: list[date]) -> float:
    """Total worked hours for an employee over the given dates."""
    total = 0.0
    for d in dates:
        e = get_entry(data, employee, d.isoformat())
        total += worked_hours(e["arrivee"], e["depart"], e.get("pause", 0))
    return round(total, 2)


def fortnight(start: date) -> list[date]:
    """The 14 dates of a two-week period beginning at `start`."""
    return [start + timedelta(days=i) for i in range(14)]


def monday_of(d: date) -> date:
    """The Monday of the week containing `d`."""
    return d - timedelta(days=d.weekday())
