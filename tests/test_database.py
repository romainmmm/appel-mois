import os
import tempfile

import database as db
from staff import Worker, default_workers
from notes import ManualTask
from extra_staff import ExtraEmployee


def _conn():
    path = tempfile.mktemp(suffix=".db")
    return db.get_conn(path), path


class TestWorkers:
    def test_default_when_empty(self):
        conn, p = _conn()
        try:
            assert len(db.load_workers(conn)) == len(default_workers())
        finally:
            conn.close()
            os.unlink(p)

    def test_roundtrip_preserves_weekly_max_int_keys(self):
        conn, p = _conn()
        try:
            ws = [Worker("Anna", 1, home_floor=100, floor_strict=True,
                         weekly_max={0: 5, 2: 5})]
            db.save_workers(conn, ws)
            loaded = db.load_workers(conn)
            assert loaded[0].name == "Anna"
            assert loaded[0].weekly_max == {0: 5, 2: 5}  # keys are ints, not "0"
        finally:
            conn.close()
            os.unlink(p)


class TestOtherEntities:
    def test_notes_roundtrip(self):
        conn, p = _conn()
        try:
            db.save_notes(conn, [ManualTask("2026-07-15", "Chien", 210, "x")])
            assert db.load_notes(conn)[0].room == 210
        finally:
            conn.close()
            os.unlink(p)

    def test_extra_roundtrip(self):
        conn, p = _conn()
        try:
            db.save_extra_staff(conn, [ExtraEmployee("Sophie", "Accueil")])
            assert db.load_extra_staff(conn)[0].role == "Accueil"
        finally:
            conn.close()
            os.unlink(p)

    def test_timesheet_roundtrip(self):
        conn, p = _conn()
        try:
            db.save_timesheet(conn, {"Anna": {"2026-07-15": {"arrivee": "08:00"}}})
            assert db.load_timesheet(conn)["Anna"]["2026-07-15"]["arrivee"] == "08:00"
        finally:
            conn.close()
            os.unlink(p)

    def test_settings_default_and_save(self):
        conn, p = _conn()
        try:
            assert db.load_settings(conn)["delete_password"] == "motel"
            db.save_settings(conn, {"delete_password": "x"})
            assert db.load_settings(conn)["delete_password"] == "x"
        finally:
            conn.close()
            os.unlink(p)

    def test_users_roundtrip(self):
        conn, p = _conn()
        try:
            assert db.load_users(conn) == {}
            db.save_users(conn, {"gerant": {"hash": "h", "role": "gerant"}})
            assert db.load_users(conn)["gerant"]["role"] == "gerant"
        finally:
            conn.close()
            os.unlink(p)


class TestMigration:
    def test_imports_existing_json(self):
        conn, p = _conn()
        d = tempfile.mkdtemp()
        try:
            import json
            with open(os.path.join(d, "notes.json"), "w", encoding="utf-8") as f:
                json.dump([{"date": "2026-07-15", "type": "Ménage", "room": 101, "comment": ""}], f)
            db.migrate_from_json(conn, d)
            assert db.load_notes(conn)[0].room == 101
        finally:
            conn.close()
            os.unlink(p)
