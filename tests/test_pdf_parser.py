import os
import pytest
from pdf_parser import parse_pdf, RoomEntry

SAMPLE_PDF = os.path.join(os.path.dirname(__file__), "test_data", "sample.pdf")


class TestParsePdf:
    def test_returns_date(self):
        result = parse_pdf(SAMPLE_PDF)
        assert result["date"] == "Mercredi 16 décembre 2026"

    def test_arrivees_rooms(self):
        result = parse_pdf(SAMPLE_PDF)
        room_numbers = [r.room for r in result["arrivees"]]
        assert sorted(room_numbers) == [101, 102, 210, 401]

    def test_departs_rooms(self):
        result = parse_pdf(SAMPLE_PDF)
        room_numbers = [r.room for r in result["departs"]]
        assert room_numbers == [210]

    def test_service_rooms(self):
        result = parse_pdf(SAMPLE_PDF)
        room_numbers = [r.room for r in result["service"]]
        assert sorted(room_numbers) == [201, 211]

    def test_arrivee_has_name(self):
        result = parse_pdf(SAMPLE_PDF)
        room_102 = [r for r in result["arrivees"] if r.room == 102][0]
        assert "nom-test" in room_102.name.lower()

    def test_service_has_night_info(self):
        result = parse_pdf(SAMPLE_PDF)
        room_201 = [r for r in result["service"] if r.room == 201][0]
        assert "Nuit 1 sur 3" in room_201.extra

    def test_room_entry_fields(self):
        entry = RoomEntry(room=102, name="Doe John", extra="")
        assert entry.room == 102
        assert entry.name == "Doe John"
        assert entry.extra == ""


class TestParsePdfEdgeCases:
    def test_ignores_booking_references(self):
        """Booking refs like 58-253531-23771 should not appear as rooms."""
        result = parse_pdf(SAMPLE_PDF)
        all_rooms = (
            result["arrivees"] + result["departs"] + result["service"]
        )
        for r in all_rooms:
            assert r.room < 1000, f"Unexpected room number {r.room}"

    def test_room_in_both_arrivee_and_depart(self):
        """Room 210 is both a departure and an arrival (turnover)."""
        result = parse_pdf(SAMPLE_PDF)
        arr_rooms = [r.room for r in result["arrivees"]]
        dep_rooms = [r.room for r in result["departs"]]
        assert 210 in arr_rooms
        assert 210 in dep_rooms
