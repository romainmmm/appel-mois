"""Shared sober colour palette (muted, professional tones).

Stored as hex strings without '#'. openpyxl uses them as-is; reportlab needs
'#' prefixed (see hx()).
"""

HEADER = "44546A"     # slate blue-grey (table headers)
DEPART = "E2C9C4"     # dusty rose      (checkout / departure)
SERVICE = "CBD5DC"    # soft blue-grey  (service cleaning)
ARRIVEE = "D3DAC4"    # sage green      (arrival — housekeeping sheet)
TURNOVER = "EAD9B0"   # warm sand       (departure + arrival same day)
MANAGER = "D9CFC0"    # taupe           (unassigned -> managers)
MANUAL = "C9DCD4"     # soft teal       (manually-added task)
WEEKEND = "EEF0F2"    # very light grey (weekend rows)
GRID = "C9CCD1"       # grid lines
HEADER_TEXT = "FFFFFF"


def hx(color: str) -> str:
    """Return the colour with a leading '#', for reportlab."""
    return "#" + color
