"""PDF versions of the deliverables (pure-Python via reportlab, no Excel needed).

  - build_month_pdf            : monthly dashboard table (one row per day).
  - build_day_pdf              : the fixed room-grid day sheet (monthly app).
  - build_housekeeping_day_pdf : the daily-PDF housekeeping sheet, as PDF.
"""

from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from cleaning_schedule import CleaningTask
from staff import Worker, WEEKDAYS_FR
from distribution import assign_day, DayAssignment
from room_layout import ROOM_LAYOUT
import palette

# Colours (sober palette)
_C_DEPART = colors.HexColor(palette.hx(palette.DEPART))
_C_SERVICE = colors.HexColor(palette.hx(palette.SERVICE))
_C_ARRIVEE = colors.HexColor(palette.hx(palette.ARRIVEE))
_C_TURNOVER = colors.HexColor(palette.hx(palette.TURNOVER))
_C_MANUAL = colors.HexColor(palette.hx(palette.MANUAL))
_C_MANAGER = colors.HexColor(palette.hx(palette.MANAGER))
_C_HEADER = colors.HexColor(palette.hx(palette.HEADER))
_C_WEEKEND = colors.HexColor(palette.hx(palette.WEEKEND))
_C_GRID = colors.HexColor(palette.hx(palette.GRID))

MANAGER_LABEL = "Gérants (à replanifier)"

_styles = getSampleStyleSheet()
_TITLE = ParagraphStyle("t", parent=_styles["Title"], fontSize=18, spaceAfter=8,
                        textColor=colors.HexColor(palette.hx(palette.HEADER)))
_CELL = ParagraphStyle("c", parent=_styles["Normal"], fontSize=9, leading=11)


# ── Generic room-grid PDF ───────────────────────────────────────────
def _grid_pdf(title, room_cell_fn, legend_items, output_path):
    """Render the fixed room grid. room_cell_fn(room) -> (text, color) or None."""
    pos_to_room = {(row, num_col): room for room, (row, num_col, _) in ROOM_LAYOUT.items()}
    excel_rows = sorted({row for (row, _, _) in ROOM_LAYOUT.values()})
    col_pairs = [("A", "B"), ("C", "D"), ("E", "F")]

    data, style_cmds = [], [
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, _C_GRID),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]
    for grid_r, er in enumerate(excel_rows):
        row_cells = []
        for ci, (num_col, _info) in enumerate(col_pairs):
            room = pos_to_room.get((er, num_col))
            num_idx = ci * 2
            if room is None:
                row_cells += ["", ""]
                continue
            row_cells.append(str(room))
            style_cmds.append(("FONTNAME", (num_idx, grid_r), (num_idx, grid_r), "Helvetica-Bold"))
            style_cmds.append(("ALIGN", (num_idx, grid_r), (num_idx, grid_r), "CENTER"))
            cell = room_cell_fn(room)
            if cell is not None:
                text, color = cell
                row_cells.append(Paragraph(text, _CELL))
                style_cmds.append(("BACKGROUND", (num_idx + 1, grid_r), (num_idx + 1, grid_r), color))
            else:
                row_cells.append("")
        data.append(row_cells)

    # Landscape so the three room columns fit comfortably on one page
    page_w = A4[1] - 20 * mm  # landscape width
    num_w = 14 * mm
    info_w = (page_w - 3 * num_w) / 3
    table = Table(data, colWidths=[num_w, info_w, num_w, info_w, num_w, info_w])
    table.setStyle(TableStyle(style_cmds))

    legend_cells = ["Légende :"] + [lbl for lbl, _ in legend_items]
    legend = Table([legend_cells],
                   colWidths=[26 * mm] + [32 * mm] * len(legend_items))
    leg_style = [
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, 0), "CENTER"),
        ("GRID", (1, 0), (-1, 0), 0.4, _C_GRID),
    ]
    for i, (_lbl, col) in enumerate(legend_items, start=1):
        leg_style.append(("BACKGROUND", (i, 0), (i, 0), col))
    legend.setStyle(TableStyle(leg_style))

    grid_title = ParagraphStyle(
        "gt", parent=_TITLE, fontSize=13, spaceAfter=4)
    doc = SimpleDocTemplate(
        output_path, pagesize=landscape(A4),
        leftMargin=8 * mm, rightMargin=8 * mm, topMargin=7 * mm, bottomMargin=6 * mm)
    doc.build([Paragraph(title, grid_title), table, Spacer(1, 2.5 * mm), legend])


# ── Monthly dashboard PDF ───────────────────────────────────────────
def build_month_pdf(schedule, workers, output_path):
    ordered = sorted(workers, key=lambda w: w.order)
    days = sorted(schedule.keys())

    doc = SimpleDocTemplate(
        output_path, pagesize=landscape(A4),
        leftMargin=10 * mm, rightMargin=10 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
    title = days[0].strftime("Calendrier des ménages — %m/%Y") if days else "Calendrier"

    header = ["Date", "Jour", "Total"] + [w.name for w in ordered] + ["Gérants"]
    data = [header]
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), _C_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, _C_GRID),
    ]
    for r, d in enumerate(days, start=1):
        da = assign_day(schedule[d], ordered, d)
        row = [d.strftime("%d/%m"), WEEKDAYS_FR[d.weekday()], len(schedule[d])]
        for w in ordered:
            row.append(len(da.assignments.get(w.name, [])) or "")
        nb = len(da.unassigned)
        row.append(nb or "")
        data.append(row)
        if d.weekday() >= 5:
            style_cmds.append(("BACKGROUND", (0, r), (-1, r), _C_WEEKEND))
        if nb:
            style_cmds.append(("BACKGROUND", (-1, r), (-1, r), _C_MANAGER))

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle(style_cmds))
    doc.build([Paragraph(title, _TITLE), table])


# ── Day grid PDF (monthly app) ──────────────────────────────────────
def build_day_pdf(day_assignment: DayAssignment, output_path: str) -> None:
    da = day_assignment
    d = da.day
    room_worker, room_tasks = {}, {}
    for name, tasks in da.assignments.items():
        for t in tasks:
            room_worker[t.room] = name
            room_tasks.setdefault(t.room, []).append(t)
    for t in da.unassigned:
        room_worker[t.room] = MANAGER_LABEL
        room_tasks.setdefault(t.room, []).append(t)

    def cell_fn(room):
        if room not in room_tasks:
            return None
        tasks = room_tasks[room]
        worker = room_worker[room]
        kinds = {t.kind for t in tasks}

        if kinds == {"manuel"}:
            label = " ; ".join(t.night_label for t in tasks if t.night_label) or "Manuel"
            color = _C_MANUAL
            text = f"{label} | {worker}"
            return (text, _C_MANAGER if worker == MANAGER_LABEL else color)

        if "depart" in kinds and "service" in kinds:
            label, color = "DÉP+SERV", _C_DEPART
        elif "depart" in kinds:
            label, color = "DÉPART", _C_DEPART
        elif "service" in kinds:
            label, color = "SERVICE", _C_SERVICE
        else:
            label, color = "Manuel", _C_MANUAL
        night = next((t.night_label for t in tasks if t.kind == "service" and t.night_label), "")
        text = f"{label} | {worker}" + (f" ({night})" if night else "")
        if "manuel" in kinds:
            extra = " ; ".join(t.night_label for t in tasks if t.kind == "manuel" and t.night_label)
            if extra:
                text += f" + {extra}"
        if worker == MANAGER_LABEL:
            color = _C_MANAGER
        return text, color

    title = f"Feuille du jour — {WEEKDAYS_FR[d.weekday()]} {d.strftime('%d/%m/%Y')}"
    legend = [("DÉPART", _C_DEPART), ("SERVICE", _C_SERVICE),
              ("Manuel", _C_MANUAL), ("Gérants", _C_MANAGER)]
    _grid_pdf(title, cell_fn, legend, output_path)


# ── Housekeeping day PDF (from the daily état-des-chambres PDF) ──────
def build_housekeeping_day_pdf(data: dict, output_path: str) -> None:
    """Same content/layout as the housekeeping Excel day sheet, as a PDF."""
    room_tasks: dict[int, list[tuple[str, object]]] = {}
    for entry in data.get("arrivees", []):
        room_tasks.setdefault(entry.room, []).append(("arrivee", entry))
    for entry in data.get("departs", []):
        room_tasks.setdefault(entry.room, []).append(("depart", entry))
    for entry in data.get("service", []):
        room_tasks.setdefault(entry.room, []).append(("service", entry))

    def cell_fn(room):
        if room not in room_tasks:
            return None
        tasks = room_tasks[room]
        types = [t for t, _ in tasks]
        if "depart" in types and "arrivee" in types:
            names = " / ".join({e.name for _, e in tasks})
            return f"DÉP+ARR | {names}", _C_TURNOVER
        if "depart" in types:
            e = [e for t, e in tasks if t == "depart"][0]
            return f"DÉPART | {e.name}", _C_DEPART
        if "arrivee" in types:
            e = [e for t, e in tasks if t == "arrivee"][0]
            return f"ARRIVÉE | {e.name}", _C_ARRIVEE
        e = [e for t, e in tasks if t == "service"][0]
        extra = f" ({e.extra})" if e.extra else ""
        return f"SERVICE | {e.name}{extra}", _C_SERVICE

    title = f"Feuille du jour — {data.get('date') or ''}".strip(" —")
    legend = [("ARRIVÉE", _C_ARRIVEE), ("DÉPART", _C_DEPART),
              ("SERVICE", _C_SERVICE), ("DÉP+ARR", _C_TURNOVER)]
    _grid_pdf(title or "Feuille du jour", cell_fn, legend, output_path)
