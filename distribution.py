"""Assign the day's cleaning tasks to workers.

Model (no load-balancing — purely rule-driven):
  1. Workers are processed in selection order (order = 1 picks first).
  2. Each worker first takes tasks on their home floor (up to their daily cap).
  3. Remaining tasks are offered to workers with spare capacity, again in
     selection order, grouping by floor to keep each worker compact.
     A "strict" worker (Anna) only ever receives their home floor.
  4. Any task nobody can take is left unassigned -> handled by the managers.
"""

from dataclasses import dataclass, field
from datetime import date

from cleaning_schedule import CleaningTask
from staff import Worker


@dataclass
class DayAssignment:
    day: date
    assignments: dict[str, list[CleaningTask]]   # worker name -> tasks
    unassigned: list[CleaningTask] = field(default_factory=list)


def assign_day(
    tasks: list[CleaningTask],
    workers: list[Worker],
    day: date,
) -> DayAssignment:
    """Distribute `tasks` among `workers` for a single `day`."""
    ordered = sorted(workers, key=lambda w: w.order)

    assignments: dict[str, list[CleaningTask]] = {w.name: [] for w in ordered}
    capacity: dict[str, int] = {w.name: w.max_on(day) for w in ordered}

    remaining = list(tasks)

    def _take(worker: Worker, task: CleaningTask) -> None:
        assignments[worker.name].append(task)
        capacity[worker.name] -= 1
        remaining.remove(task)

    # ── Pass 1: home-floor tasks ────────────────────────────────────
    for w in ordered:
        if capacity[w.name] <= 0 or w.home_floor is None:
            continue
        for task in [t for t in remaining if t.floor == w.home_floor]:
            if capacity[w.name] <= 0:
                break
            _take(w, task)

    # ── Pass 2: remaining tasks, in selection order, grouped by floor ─
    for w in ordered:
        if capacity[w.name] <= 0:
            continue
        # candidate tasks this worker is allowed to take
        if w.floor_strict:
            allowed = [t for t in remaining if t.floor == w.home_floor]
        else:
            allowed = list(remaining)
        # group by floor to keep the worker on as few floors as possible
        allowed.sort(key=lambda t: (t.floor, t.room))
        for task in allowed:
            if capacity[w.name] <= 0:
                break
            _take(w, task)

    return DayAssignment(day=day, assignments=assignments, unassigned=remaining)
