"""Compute which rooms need cleaning on which day, from a list of reservations.

Two kinds of cleaning:
  - "depart"  : on the checkout day of a reservation (room turnover).
  - "service" : during a long stay, every `freq_days` nights (default 3),
                e.g. on stay-nights 3, 6, 9... but never on the checkout day.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from reservation_parser import Reservation


@dataclass
class CleaningTask:
    room: int
    floor: int
    kind: str          # "depart" or "service"
    booking_id: str
    night_label: str = ""   # e.g. "Nuit 3" for a service cleaning


def compute_cleanings(
    reservations: list[Reservation],
    freq_days: int = 3,
    start: date | None = None,
    end: date | None = None,
) -> dict[date, list[CleaningTask]]:
    """
    Build the cleaning schedule.

    Args:
        reservations: confirmed reservations.
        freq_days: service-cleaning cadence in nights (default 3).
        start, end: optional inclusive date range to restrict the output.

    Returns:
        dict mapping a date to the list of CleaningTask due that day.
    """
    schedule: dict[date, list[CleaningTask]] = {}

    def _in_range(d: date) -> bool:
        if start is not None and d < start:
            return False
        if end is not None and d > end:
            return False
        return True

    def _add(d: date, task: CleaningTask) -> None:
        if _in_range(d):
            schedule.setdefault(d, []).append(task)

    for r in reservations:
        # Departure cleaning on checkout day
        _add(r.checkout, CleaningTask(
            room=r.room, floor=r.floor, kind="depart", booking_id=r.booking_id,
        ))

        # Service cleanings every freq_days nights, before checkout
        if freq_days and freq_days > 0:
            k = 1
            while True:
                service_day = r.checkin + timedelta(days=k * freq_days)
                if service_day >= r.checkout:
                    break
                _add(service_day, CleaningTask(
                    room=r.room, floor=r.floor, kind="service",
                    booking_id=r.booking_id,
                    night_label=f"Nuit {k * freq_days}",
                ))
                k += 1

    # Sort each day's tasks by room number for stable output
    for d in schedule:
        schedule[d].sort(key=lambda t: t.room)

    return schedule
