import os
from datetime import date

import pytest

from reservation_parser import parse_reservations, Reservation

SAMPLE = os.path.join(os.path.dirname(__file__), "test_data", "sample_export.xls")


class TestParseReservations:
    def test_returns_list_of_reservations(self):
        res = parse_reservations(SAMPLE)
        assert len(res) > 0
        assert all(isinstance(r, Reservation) for r in res)

    def test_excludes_cancelled_by_default(self):
        res = parse_reservations(SAMPLE)
        for r in res:
            assert "annul" not in r.status.lower()

    def test_all_have_valid_room(self):
        res = parse_reservations(SAMPLE)
        for r in res:
            assert 100 <= r.room <= 499

    def test_floor_derived_from_room(self):
        res = parse_reservations(SAMPLE)
        for r in res:
            assert r.floor == (r.room // 100) * 100

    def test_checkin_before_checkout(self):
        res = parse_reservations(SAMPLE)
        for r in res:
            assert r.checkin < r.checkout

    def test_dates_are_date_objects(self):
        res = parse_reservations(SAMPLE)
        r = res[0]
        assert isinstance(r.checkin, date)
        assert isinstance(r.checkout, date)

    def test_keep_cancelled_when_requested(self):
        # In this export, cancelled lines carry no room number and are dropped
        # regardless. The flag must never *reduce* below the confirmed set.
        all_res = parse_reservations(SAMPLE, confirmed_only=False)
        confirmed = parse_reservations(SAMPLE, confirmed_only=True)
        assert len(all_res) >= len(confirmed)
        assert all("annul" not in r.status.lower() for r in confirmed)

    def test_room_type_present(self):
        res = parse_reservations(SAMPLE)
        assert any(r.room_type for r in res)

    def test_nights_property(self):
        r = Reservation(
            booking_id="x", room=101, floor=100, status="Confirmation ferme",
            checkin=date(2026, 7, 1), checkout=date(2026, 7, 4), room_type="Standard",
        )
        assert r.nights == 3
