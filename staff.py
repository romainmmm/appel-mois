"""Worker profiles: weekly availability, home floor, daily room caps, persistence."""

import json
from dataclasses import dataclass, field, asdict
from datetime import date


# weekday index: 0=Monday ... 6=Sunday
WEEKDAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


@dataclass
class Worker:
    name: str
    order: int                       # selection order (1 = picks first)
    home_floor: int | None = None    # e.g. 100 for Anna, 200 for Isabelle, None if flexible
    floor_strict: bool = False       # True = can ONLY work the home floor (Anna)
    # max rooms per weekday; a weekday absent or 0 means day off
    weekly_max: dict[int, int] = field(default_factory=dict)
    # specific dates off (ISO strings), overrides weekly availability
    days_off: list[str] = field(default_factory=list)

    def max_on(self, day: date) -> int:
        """Room capacity for a given date (0 = unavailable)."""
        if day.isoformat() in self.days_off:
            return 0
        return self.weekly_max.get(day.weekday(), 0)

    def available_on(self, day: date) -> bool:
        return self.max_on(day) > 0


def default_workers() -> list[Worker]:
    """Seed the team described by the manager (editable afterwards in the app)."""
    everyday = lambda n: {wd: n for wd in range(7)}
    return [
        Worker(
            name="Anna", order=1, home_floor=100, floor_strict=True,
            # congé mardi (1); Lun/Mer/Ven = 5 ; Jeu/Sam/Dim = 8
            weekly_max={0: 5, 2: 5, 4: 5, 3: 8, 5: 8, 6: 8},
        ),
        Worker(name="Isabelle", order=2, home_floor=200, floor_strict=False,
               weekly_max=everyday(13)),
        Worker(name="Oumar", order=3, weekly_max=everyday(10)),
        Worker(name="Morgann", order=4, weekly_max=everyday(6)),
        Worker(name="Estrella", order=5, weekly_max=everyday(6)),
        Worker(name="Fatoumata", order=6, weekly_max=everyday(8)),
        Worker(name="Chantale", order=7, weekly_max=everyday(10)),
    ]


def save_workers(workers: list[Worker], path: str) -> None:
    data = [asdict(w) for w in workers]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_workers(path: str) -> list[Worker]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    workers = []
    for d in data:
        # JSON keys are strings; convert weekly_max keys back to int
        d["weekly_max"] = {int(k): v for k, v in d.get("weekly_max", {}).items()}
        workers.append(Worker(**d))
    return workers
