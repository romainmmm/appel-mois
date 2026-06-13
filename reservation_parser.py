"""Parse the monthly reservation export (.xls) from the PMS into structured data."""

from dataclasses import dataclass
from datetime import date

import pandas as pd


# Column positions in the export (the headers contain accented characters that
# get mangled by some readers, so we rely on stable positions instead of names).
_COL_BOOKING_ID = 0
_COL_ROOM = 1
_COL_FLOOR = 3
_COL_STATUS = 4
_COL_CHECKIN = 8
_COL_CHECKOUT = 9
_COL_ROOM_TYPE = 28


@dataclass
class Reservation:
    booking_id: str
    room: int
    floor: int
    status: str
    checkin: date
    checkout: date
    room_type: str

    @property
    def nights(self) -> int:
        return (self.checkout - self.checkin).days


def parse_reservations(path: str, confirmed_only: bool = True) -> list[Reservation]:
    """
    Read the PMS reservation export.

    Args:
        path: path to the .xls/.xlsx export.
        confirmed_only: if True (default), drop cancelled reservations.

    Returns:
        list of Reservation, one per room-booking line.
    """
    df = pd.read_excel(path, sheet_name=0, header=0)

    reservations: list[Reservation] = []
    for _, row in df.iterrows():
        room_raw = row.iloc[_COL_ROOM]
        if pd.isna(room_raw):
            continue  # cancelled lines often have no room assigned

        try:
            room = int(room_raw)
        except (ValueError, TypeError):
            continue

        status = str(row.iloc[_COL_STATUS]).strip()
        if confirmed_only and "annul" in status.lower():
            continue

        checkin = pd.to_datetime(row.iloc[_COL_CHECKIN]).date()
        checkout = pd.to_datetime(row.iloc[_COL_CHECKOUT]).date()

        room_type = row.iloc[_COL_ROOM_TYPE]
        room_type = "" if pd.isna(room_type) else str(room_type).strip()

        reservations.append(
            Reservation(
                booking_id=str(row.iloc[_COL_BOOKING_ID]).strip(),
                room=room,
                floor=(room // 100) * 100,
                status=status,
                checkin=checkin,
                checkout=checkout,
                room_type=room_type,
            )
        )

    return reservations
