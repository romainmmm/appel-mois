"""PDF versions of the deliverables (pure-Python via reportlab, no Excel needed).

  - build_month_pdf : monthly dashboard table (one row per day).
  - build_day_pdf   : the fixed room-grid day sheet, mirroring the Excel layout.
"""

from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from cleaning_schedule import CleaningTask
from staff import Worker, WEEKDAYS_FR
from distribution import assign_day, DayAssignment
from room_layout import ROOM_LAYOUT

# Colors (match the Excel fills)
_C_DEPART = colors.HexColor("#FFC7CE")
_C_SERVICE = colors.HexColor("#BDD7EE")
_C_MANAGER = colors.HexColor("#FFD966")
_C_HEADER = colors.HexColor("#305496")
_C_WEEKEND = colors.HexColor("#F2F2F2")
_C_GRID = colors.HexColor("#BFBFBF")

MANAGER_LABEL = "Gérants (à replanifier)"

_styles = getSampleStyleSheet()
_TITLE = ParagraphStyle("t", parent=_styles["Title"], fontSize=18, spaceAfter=8)
_CELL = ParagraphStyle("c", parent=_styles["Normal"], fontSize=9, leading=11)


def _room_label(tasks: list[CleaningTask], worker: str):
    kinds = {t.kind for t in tasks}
    if "depart" in kinds and "service" in kinds:
        label, color = "DÉP+SERV", _C_DEPART
    elif "depart" in kinds:
        label, color = "DÉPART", _C_DEPART
    else:
        label, color = "SERVICE", _C_SERVICE
    night = next((t.night_label for t in tasks if t.night_label), "")
    text = f"{label} | {worker}" + (f" ({night})" if night else "")
    if worker == MANAGER_LABEL:
        color = _C_MANAGER
    return text, color


# ── Monthly dashboard PDF ───────────────────────────────────────────
def build_month_pdf(
    schedule: dict[date, list[CleaningTask]],
    workers: list[Worker],
    output_path: str,
) -> None:
    ordered = sorted(workers, key=lambda w: w.order)
    days = sorted(schedule.keys())

    doc = SimpleDocTemplate(
        output_path, pagesize=landscape(A4),
        leftMargin=10 * mm, rightMargin=10 * mm, topMargin=10 * mm, bottomMargin=10 * mm,
    )
    title = days[0].strftime("Calendrier des ménages — %m/%Y") if days else "Calendrier"
    elements = [Paragraph(title, _TITLE)]

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
        nb_unassigned = len(da.unassigned)
        row.append(nb_unassigned or "")
        data.append(row)
        if d.weekday() >= 5:
            style_cmds.append(("BACKGROUND", (0, r), (-1, r), _C_WEEKEND))
        if nb_unassigned:
            style_cmds.append(("BACKGROUND", (-1, r), (-1, r), _C_MANAGER))

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle(style_cmds))
    elements.append(table)
    doc.build(elements)


# ── Day grid PDF ────────────────────────────────────────────────────
def build_day_pdf(day_assignment: DayAssignment, output_path: str) -> None:
    da = day_assignment
    d = da.day

    # room -> (tasks, worker)
    room_worker, room_tasks = {}, {}
    for name, tasks in da.assignments.items():
        for t in tasks:
            room_worker[t.room] = name
            room_tasks.setdefault(t.room, []).append(t)
    for t in da.unassigned:
        room_worker[t.room] = MANAGER_LABEL
        room_tasks.setdefault(t.room, []).append(t)

    # reverse lookup: (excel_row, num_col) -> room
    pos_to_room = {(row, num_col): room for room, (row, num_col, _) in ROOM_LAYOUT.items()}
    excel_rows = sorted({row for (row, _, _) in ROOM_LAYOUT.values()})

    col_pairs = [("A", "B"), ("C", "D"), ("E", "F")]
    data, style_cmds = [], [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, _C_GRID),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]

    for grid_r, er in enumerate(excel_rows):
        row_cells = []
        for ci, (num_col, _info_col) in enumerate(col_pairs):
            room = pos_to_room.get((er, num_col))
            num_idx = ci * 2
            if room is None:
                row_cells += ["", ""]
            else:
                row_cells.append(str(room))
                style_cmds.append(("FONTNAME", (num_idx, grid_r), (num_idx, grid_r), "Helvetica-Bold"))
                style_cmds.append(("ALIGN", (num_idx, grid_r), (num_idx, grid_r), "CENTER"))
                if room in room_tasks:
                    text, color = _room_label(room_tasks[room], room_worker[room])
                    row_cells.append(Paragraph(text, _CELL))
                    style_cmds.append(("BACKGROUND", (num_idx + 1, grid_r), (num_idx + 1, grid_r), color))
                else:
                    row_cells.append("")
        data.append(row_cells)

    doc = SimpleDocTemplate(
        output_path, pagesize=portrait(A4),
        leftMargin=10 * mm, rightMargin=10 * mm, topMargin=10 * mm, bottomMargin=10 * mm,
    )
    title = f"Feuille du jour — {WEEKDAYS_FR[d.weekday()]} {d.strftime('%d/%m/%Y')}"
    # column widths: narrow number cols, wide info cols
    page_w = A4[0] - 20 * mm
    num_w = 14 * mm
    info_w = (page_w - 3 * num_w) / 3
    col_widths = [num_w, info_w, num_w, info_w, num_w, info_w]

    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle(style_cmds))

    legend = Table(
        [["Légende :", "DÉPART", "SERVICE", "Gérants"]],
        colWidths=[28 * mm, 30 * mm, 30 * mm, 40 * mm],
    )
    legend.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (1, 0), (1, 0), _C_DEPART),
        ("BACKGROUND", (2, 0), (2, 0), _C_SERVICE),
        ("BACKGROUND", (3, 0), (3, 0), _C_MANAGER),
        ("GRID", (1, 0), (-1, 0), 0.4, _C_GRID),
        ("ALIGN", (1, 0), (-1, 0), "CENTER"),
    ]))

    doc.build([Paragraph(title, _TITLE), table, Spacer(1, 6 * mm), legend])
