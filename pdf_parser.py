"""Parse hotel room status PDF into structured data."""

import re
import unicodedata
from dataclasses import dataclass

import pdfplumber


@dataclass
class RoomEntry:
    room: int
    name: str
    extra: str


# Matches lines starting with a 3-digit room number
_ROOM_LINE_RE = re.compile(
    r"^\s*(\d{3})\s+(.+)$"
)

# Sections that signal end of parsing
_STOP_KEYWORDS = ("notes", "options")


def _strip_accents(s: str) -> str:
    """Remove all accents/diacritics from a string."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _detect_section(line: str) -> str | None:
    """Detect section header, tolerant to encoding issues with accents."""
    cleaned = _strip_accents(line.lower().strip())
    # Also handle cases where pdfplumber replaces accents with garbage
    cleaned = re.sub(r"[^a-z]", "", cleaned)
    if cleaned in ("arrivees", "arrivees", "arrives"):
        return "arrivees"
    if cleaned in ("departs", "dparts", "depart"):
        return "departs"
    if cleaned == "service":
        return "service"
    return None


def _detect_stop(line: str) -> bool:
    """Detect if line is a stop section (Notes, Options)."""
    cleaned = _strip_accents(line.lower().strip())
    cleaned = re.sub(r"[^a-z]", "", cleaned)
    return cleaned in _STOP_KEYWORDS


def parse_pdf(pdf_path: str) -> dict:
    """
    Parse a hotel daily status PDF.

    Returns:
        {
            "date": str,
            "arrivees": [RoomEntry, ...],
            "departs": [RoomEntry, ...],
            "service": [RoomEntry, ...],
        }
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    lines = text.strip().split("\n")

    result = {
        "date": "",
        "arrivees": [],
        "departs": [],
        "service": [],
    }

    current_section = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Detect date (first non-empty line with a weekday)
        if not result["date"] and _looks_like_date(stripped):
            result["date"] = stripped
            continue

        # Detect section headers
        section = _detect_section(stripped)
        if section:
            current_section = section
            continue

        # Detect stop sections
        if _detect_stop(stripped):
            current_section = None
            continue

        # Skip booking reference lines (format: 58-XXXXXX-XXXXX)
        if re.match(r"^\s*\d{2}-\d{6}-\d{5}", stripped):
            continue

        # Parse room lines
        if current_section:
            match = _ROOM_LINE_RE.match(stripped)
            if match:
                room_num = int(match.group(1))
                rest = match.group(2).strip()
                name, extra = _split_name_extra(rest)
                result[current_section].append(
                    RoomEntry(room=room_num, name=name, extra=extra)
                )

    return result


def _looks_like_date(s: str) -> bool:
    weekdays = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")
    lower = _strip_accents(s.lower())
    if lower.startswith(weekdays):
        return True
    months = ("janvier", "fevrier", "mars", "avril", "mai", "juin",
              "juillet", "aout", "septembre", "octobre", "novembre", "decembre")
    return any(m in lower for m in months) and re.search(r"\d{4}", s) is not None


def _split_name_extra(text: str) -> tuple[str, str]:
    """Split 'nom-test prenom-test Nuit 1 sur 3' into name and extra info."""
    nuit_match = re.search(r"(Nuit \d+ sur \d+)", text)
    if nuit_match:
        extra = nuit_match.group(1)
        name = text[: nuit_match.start()].strip()
        return name, extra
    return text, ""
