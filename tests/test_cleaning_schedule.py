from datetime import date

import pytest

from reservation_parser import Reservation
from cleaning_schedule import compute_cleanings, CleaningTask


def _res(room, checkin, checkout, booking="b1"):
    return Reservation(
        booking_id=booking, room=room, floor=(room // 100) * 100,
        status="Confirmation ferme", checkin=checkin, checkout=checkout,
        room_type="Standard",
    )


class TestDepartureCleaning:
    def test_departure_on_checkout_day(self):
        res = [_res(101, date(2026, 7, 1), date(2026, 7, 3))]
        sched = compute_cleanings(res, freq_days=3)
        assert date(2026, 7, 3) in sched
        tasks = sched[date(2026, 7, 3)]
        assert len(tasks) == 1
        assert tasks[0].room == 101
        assert tasks[0].kind == "depart"

    def test_short_stay_has_no_service(self):
        res = [_res(101, date(2026, 7, 1), date(2026, 7, 3))]
        sched = compute_cleanings(res, freq_days=3)
        # only the checkout day appears
        assert list(sched.keys()) == [date(2026, 7, 3)]


class TestServiceCleaning:
    def test_long_stay_service_every_3_nights(self):
        # check-in Jul 1, checkout Jul 10 (9 nights), freq 3
        res = [_res(101, date(2026, 7, 1), date(2026, 7, 10))]
        sched = compute_cleanings(res, freq_days=3)
        # service on Jul 4 and Jul 7, departure on Jul 10
        assert date(2026, 7, 4) in sched
        assert date(2026, 7, 7) in sched
        assert sched[date(2026, 7, 4)][0].kind == "service"
        assert sched[date(2026, 7, 7)][0].kind == "service"
        assert sched[date(2026, 7, 10)][0].kind == "depart"

    def test_service_not_on_checkout_day(self):
        # 6-night stay, freq 3: service Jul 4 only, departure Jul 7
        res = [_res(101, date(2026, 7, 1), date(2026, 7, 7))]
        sched = compute_cleanings(res, freq_days=3)
        assert date(2026, 7, 4) in sched
        assert sched[date(2026, 7, 4)][0].kind == "service"
        assert sched[date(2026, 7, 7)][0].kind == "depart"
        # Jul 7 should not also have a service task
        kinds = [t.kind for t in sched[date(2026, 7, 7)]]
        assert "service" not in kinds

    def test_frequency_configurable(self):
        res = [_res(101, date(2026, 7, 1), date(2026, 7, 10))]
        sched = compute_cleanings(res, freq_days=2)
        # every 2 nights: Jul 3, 5, 7, 9 service; Jul 10 departure
        for d in (3, 5, 7, 9):
            assert date(2026, 7, d) in sched
            assert sched[date(2026, 7, d)][0].kind == "service"


class TestMultipleRooms:
    def test_two_departures_same_day(self):
        res = [
            _res(101, date(2026, 7, 1), date(2026, 7, 5), "b1"),
            _res(202, date(2026, 7, 2), date(2026, 7, 5), "b2"),
        ]
        sched = compute_cleanings(res, freq_days=3)
        rooms = sorted(t.room for t in sched[date(2026, 7, 5)])
        assert rooms == [101, 202]

    def test_floor_propagated(self):
        res = [_res(305, date(2026, 7, 1), date(2026, 7, 3))]
        sched = compute_cleanings(res, freq_days=3)
        assert sched[date(2026, 7, 3)][0].floor == 300


class TestDateFiltering:
    def test_restrict_to_range(self):
        res = [_res(101, date(2026, 7, 1), date(2026, 7, 10))]
        sched = compute_cleanings(
            res, freq_days=3,
            start=date(2026, 7, 5), end=date(2026, 7, 8),
        )
        # only Jul 7 service falls in [5, 8]
        assert set(sched.keys()) == {date(2026, 7, 7)}
