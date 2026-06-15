"""SQLite storage layer for the online version.

All app data (workers, notes, timesheet, extra staff, settings, auth users) is
kept in a single SQLite file as JSON documents in an `app_data(key, value)`
table. This gives a single, transactional, easy-to-back-up file and safer
concurrent access than raw JSON files.

On first run, existing JSON files (from the local version) are imported so no
data is lost during the migration.
"""

import json
import os
import sqlite3
from dataclasses import asdict

from staff import Worker, default_workers
from notes import ManualTask
from extra_staff import ExtraEmployee

DEFAULT_SETTINGS = {"delete_password": "motel"}


def db_path(base_dir: str) -> str:
    """Resolve the SQLite file path (override with the MOTEL_DB env var)."""
    return os.environ.get("MOTEL_DB", os.path.join(base_dir, "data", "motel.db"))


def get_conn(path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS app_data (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    return conn


def _get(conn, key, default=None):
    row = conn.execute("SELECT value FROM app_data WHERE key=?", (key,)).fetchone()
    return json.loads(row[0]) if row else default


def _set(conn, key, obj):
    conn.execute(
        "INSERT INTO app_data(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, json.dumps(obj, ensure_ascii=False)),
    )
    conn.commit()


# ── Workers ─────────────────────────────────────────────────────────
def load_workers(conn) -> list[Worker]:
    data = _get(conn, "workers")
    if data is None:
        return default_workers()
    out = []
    for d in data:
        d = dict(d)
        d["weekly_max"] = {int(k): v for k, v in d.get("weekly_max", {}).items()}
        out.append(Worker(**d))
    return out


def save_workers(conn, workers: list[Worker]) -> None:
    _set(conn, "workers", [asdict(w) for w in workers])


# ── Notes (manual tasks) ────────────────────────────────────────────
def load_notes(conn) -> list[ManualTask]:
    data = _get(conn, "notes", [])
    return [ManualTask(**d) for d in data]


def save_notes(conn, notes: list[ManualTask]) -> None:
    _set(conn, "notes", [asdict(n) for n in notes])


# ── Extra staff ─────────────────────────────────────────────────────
def load_extra_staff(conn) -> list[ExtraEmployee]:
    data = _get(conn, "extra", [])
    return [ExtraEmployee(**d) for d in data]


def save_extra_staff(conn, staff: list[ExtraEmployee]) -> None:
    _set(conn, "extra", [asdict(s) for s in staff])


# ── Timesheet ───────────────────────────────────────────────────────
def load_timesheet(conn) -> dict:
    return _get(conn, "timesheet", {})


def save_timesheet(conn, data: dict) -> None:
    _set(conn, "timesheet", data)


# ── Settings ────────────────────────────────────────────────────────
def load_settings(conn) -> dict:
    s = dict(DEFAULT_SETTINGS)
    s.update(_get(conn, "settings", {}) or {})
    return s


def save_settings(conn, settings: dict) -> None:
    _set(conn, "settings", settings)


# ── Auth users ──────────────────────────────────────────────────────
def load_users(conn) -> dict:
    return _get(conn, "auth_users", {}) or {}


def save_users(conn, users: dict) -> None:
    _set(conn, "auth_users", users)


# ── One-time migration from JSON files ──────────────────────────────
def migrate_from_json(conn, base_dir: str) -> None:
    """Import legacy JSON files into the DB for keys not yet present."""
    mapping = {
        "workers": "staff_config.json",
        "notes": "notes.json",
        "timesheet": "timesheet.json",
        "extra": "extra_employees.json",
        "settings": "app_config.json",
    }
    for key, filename in mapping.items():
        if _get(conn, key) is not None:
            continue  # already in DB
        path = os.path.join(base_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    _set(conn, key, json.load(f))
            except (json.JSONDecodeError, OSError):
                pass
