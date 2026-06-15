"""Streamlit app — Motel Panoramique.

Deux sections :
  • Feuille du mois : à partir de l'extraction de réservations (.xls), génère le
    calendrier mensuel des ménages et la répartition par préposée.
  • Feuille du jour : à partir du PDF « état des chambres », génère la feuille de
    jour (comportement identique au projet housekeeping).

Les fichiers Excel sont écrits directement dans le dossier Téléchargements du PC
(détecté automatiquement) — le chemin exact est affiché après génération.
"""

import base64
import os
import tempfile
from datetime import date, datetime, time
from pathlib import Path

import pandas as pd
import streamlit as st

# Feuille du mois
from reservation_parser import parse_reservations
from cleaning_schedule import compute_cleanings
from distribution import assign_day
from staff import Worker, WEEKDAYS_FR, default_workers, load_workers, save_workers
from notes import ManualTask, TYPES, load_notes, save_notes, merge_into_schedule
from timesheet import (
    load_timesheet, save_timesheet, get_entry, set_entry,
    worked_hours, period_total, period_tips, fortnight, monday_of,
)
from extra_staff import ExtraEmployee, load_extra_staff, save_extra_staff
from room_layout import ALL_ROOMS
from excel_export import build_month_workbook, build_day_sheet, build_timesheet_workbook
from pdf_export import build_month_pdf, build_day_pdf, build_housekeeping_day_pdf
# Feuille du jour (housekeeping, inchangé)
from pdf_parser import parse_pdf
from excel_generator import generate_excel

st.set_page_config(page_title="Ménages — Motel Panoramique", page_icon="🧹", layout="wide")

HERE = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(HERE, "staff_config.json")
NOTES_PATH = os.path.join(HERE, "notes.json")
TIMESHEET_PATH = os.path.join(HERE, "timesheet.json")
EXTRA_PATH = os.path.join(HERE, "extra_employees.json")
SETTINGS_PATH = os.path.join(HERE, "app_config.json")
LOGO_PATH = os.path.join(HERE, "assets", "logo_motel.png")
DEFAULT_SETTINGS = {"delete_password": "motel"}
FLOOR_OPTIONS = {"Aucun (flexible)": None, "100": 100, "200": 200, "300": 300, "400": 400}
FLOOR_LABELS = {v: k for k, v in FLOOR_OPTIONS.items()}

# Brand colours (from the Motel Panoramique site)
GOLD = "#C8941A"
GOLD_DARK = "#A87714"
CHARCOAL = "#2B2B2B"


def _inject_style():
    st.markdown(
        f"""
        <style>
        /* App feel: hide Streamlit chrome */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        [data-testid="stToolbar"] {{display: none;}}
        .block-container {{padding-top: 1.4rem;}}

        /* Brand header banner */
        .brand {{
            display: flex; align-items: center; gap: 16px;
            padding: 10px 4px 14px 4px;
            border-bottom: 3px solid {GOLD};
            margin-bottom: 14px;
        }}
        .brand img {{height: 54px; width: auto;}}
        .brand .titles {{line-height: 1.15;}}
        .brand .t1 {{font-size: 1.5rem; font-weight: 700; color: {CHARCOAL};
                     letter-spacing: .5px;}}
        .brand .t2 {{font-size: .95rem; color: {GOLD_DARK}; font-weight: 600;}}

        /* Buttons */
        .stButton > button {{
            background: {GOLD}; color: white; border: none;
            border-radius: 8px; font-weight: 600; padding: .45rem 1rem;
        }}
        .stButton > button:hover {{background: {GOLD_DARK}; color: white;}}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{gap: 4px;}}
        .stTabs [aria-selected="true"] {{color: {GOLD_DARK} !important;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header():
    logo_html = ""
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{b64}" alt="logo"/>'
    st.markdown(
        f"""
        <div class="brand">
            {logo_html}
            <div class="titles">
                <div class="t1">MOTEL PANORAMIQUE</div>
                <div class="t2">Gestion des ménages · Saguenay, Qc</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def downloads_dir() -> Path:
    """The current PC's Downloads folder (resolved at runtime — never hardcoded)."""
    d = Path.home() / "Downloads"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_and_report(build_fn, filename: str):
    """Run build_fn(path) writing into the chosen folder, then show the path."""
    dest = Path(st.session_state.get("dest_dir", str(downloads_dir())))
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except Exception:
        st.error(f"Dossier de destination invalide : {dest}")
        return
    target = dest / filename
    build_fn(str(target))
    st.success("✅ Fichier enregistré ici :")
    st.code(str(target), language=None)


def _init_workers():
    if "workers" not in st.session_state:
        st.session_state.workers = (
            load_workers(CONFIG_PATH) if os.path.exists(CONFIG_PATH) else default_workers()
        )


def _init_notes():
    if "notes" not in st.session_state:
        st.session_state.notes = load_notes(NOTES_PATH)


def _init_timesheet():
    if "timesheet" not in st.session_state:
        st.session_state.timesheet = load_timesheet(TIMESHEET_PATH)


def _init_extra():
    if "extra" not in st.session_state:
        st.session_state.extra = load_extra_staff(EXTRA_PATH)


def _load_settings() -> dict:
    import json
    s = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            s.update(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return s


def _save_settings(s: dict) -> None:
    import json
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)


def _init_settings():
    if "settings" not in st.session_state:
        st.session_state.settings = _load_settings()


def request_delete(kind: str, ident: str, label: str) -> None:
    """Flag an item for deletion; the confirmation box will ask for the password."""
    st.session_state.pending_delete = {"kind": kind, "ident": ident, "label": label}


def _perform_delete(pend: dict) -> None:
    if pend["kind"] == "worker":
        st.session_state.workers = [
            w for w in st.session_state.workers if w.name != pend["ident"]]
        save_workers(st.session_state.workers, CONFIG_PATH)
    elif pend["kind"] == "extra":
        st.session_state.extra = [
            x for x in st.session_state.extra if x.name != pend["ident"]]
        save_extra_staff(st.session_state.extra, EXTRA_PATH)


def render_delete_confirm() -> None:
    pend = st.session_state.get("pending_delete")
    if not pend:
        return
    st.warning(f"⚠️ Supprimer **{pend['label']}** ? Cette action est définitive.")
    c1, c2, c3 = st.columns([3, 1.2, 1])
    pw = c1.text_input("Mot de passe pour confirmer", type="password", key="del_pw")
    if c2.button("Confirmer la suppression"):
        if pw == st.session_state.settings.get("delete_password", "motel"):
            _perform_delete(pend)
            st.session_state.pending_delete = None
            st.session_state.pop("del_pw", None)
            st.rerun()
        else:
            st.error("Mot de passe incorrect — suppression annulée.")
    if c3.button("Annuler"):
        st.session_state.pending_delete = None
        st.rerun()


_init_workers()
_init_notes()
_init_timesheet()
_init_extra()
_init_settings()

_inject_style()
_render_header()

st.text_input(
    "📁 Dossier où enregistrer les fichiers générés",
    value=st.session_state.get("dest_dir", str(downloads_dir())),
    key="dest_dir",
    help="Par défaut, votre dossier Téléchargements. Vous pouvez coller un autre chemin.",
)

render_delete_confirm()

tab_mois, tab_jour, tab_notes, tab_perso = st.tabs([
    "📅 Feuille du mois (réservations)",
    "📋 Feuille du jour (PDF état des chambres)",
    "📝 Notes / tâches manuelles",
    "🗓️ Feuille du personnel",
])


# ════════════════════════════════════════════════════════════════════
#  ONGLET 1 — FEUILLE DU MOIS
# ════════════════════════════════════════════════════════════════════
with tab_mois:
    with st.expander("👥 Gérer l'équipe (préposées, étages, plafonds, congés)", expanded=False):
        st.caption(
            "La disponibilité hebdomadaire se répète chaque semaine. Mettez 0 sur "
            "un jour de congé récurrent. Pour un congé ponctuel, ajoutez la date "
            "dans « Ajouter un congé ponctuel »."
        )
        workers = st.session_state.workers

        for idx, w in enumerate(sorted(workers, key=lambda x: x.order)):
            with st.container(border=True):
                cols = st.columns([2, 1, 2, 2])
                w.name = cols[0].text_input("Nom", w.name, key=f"name_{idx}")
                w.order = cols[1].number_input("Ordre", 1, 99, w.order, key=f"order_{idx}")
                floor_label = cols[2].selectbox(
                    "Étage assigné", list(FLOOR_OPTIONS.keys()),
                    index=list(FLOOR_OPTIONS.keys()).index(
                        FLOOR_LABELS.get(w.home_floor, "Aucun (flexible)")),
                    key=f"floor_{idx}",
                )
                w.home_floor = FLOOR_OPTIONS[floor_label]
                w.floor_strict = cols[3].checkbox(
                    "Étage strict", w.floor_strict, key=f"strict_{idx}")

                st.write("**Nombre maximum de chambres par jour :**")
                day_cols = st.columns(7)
                new_max = {}
                for wd in range(7):
                    val = day_cols[wd].number_input(
                        WEEKDAYS_FR[wd][:3], 0, 30, w.weekly_max.get(wd, 0),
                        key=f"max_{idx}_{wd}")
                    if val > 0:
                        new_max[wd] = val
                w.weekly_max = new_max

                c1, c2 = st.columns([3, 1])
                congue = c1.date_input("Ajouter un congé ponctuel", value=None, key=f"off_{idx}")
                if congue and congue.isoformat() not in w.days_off:
                    w.days_off.append(congue.isoformat())
                if w.days_off:
                    c1.write("Congés : " + ", ".join(sorted(w.days_off)))
                    if c1.button("Effacer les congés", key=f"clroff_{idx}"):
                        w.days_off = []
                if c2.button("🗑 Supprimer", key=f"del_{idx}"):
                    request_delete("worker", w.name, f"la préposée « {w.name} »")
                    st.rerun()

        b1, b2 = st.columns(2)
        if b1.button("➕ Ajouter une préposée"):
            nxt = max((w.order for w in workers), default=0) + 1
            st.session_state.workers.append(
                Worker(name="Nouvelle", order=nxt, weekly_max={wd: 6 for wd in range(7)}))
            st.rerun()
        if b2.button("💾 Enregistrer l'équipe"):
            save_workers(st.session_state.workers, CONFIG_PATH)
            st.success("Équipe enregistrée.")

        st.markdown("---")
        st.markdown("**🔒 Mot de passe de suppression** (par défaut : `motel`)")
        pc = st.columns([2, 2, 1.4])
        cur_pw = pc[0].text_input("Mot de passe actuel", type="password", key="pw_cur")
        new_pw = pc[1].text_input("Nouveau mot de passe", type="password", key="pw_new")
        if pc[2].button("Changer"):
            if cur_pw == st.session_state.settings.get("delete_password", "motel"):
                if new_pw:
                    st.session_state.settings["delete_password"] = new_pw
                    _save_settings(st.session_state.settings)
                    st.success("Mot de passe modifié.")
                else:
                    st.warning("Le nouveau mot de passe ne peut pas être vide.")
            else:
                st.error("Mot de passe actuel incorrect.")

    st.divider()
    col_a, col_b = st.columns([3, 1])
    uploaded = col_a.file_uploader(
        "Extraction de réservations (.xls / .xlsx)", type=["xls", "xlsx"], key="up_mois")
    freq = col_b.number_input("Ménage de service tous les … jours", 1, 14, 3)

    if uploaded:
        with tempfile.NamedTemporaryFile(
            suffix=os.path.splitext(uploaded.name)[1], delete=False) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name
        try:
            res = parse_reservations(tmp_path)
            sched = compute_cleanings(res, freq_days=int(freq))
            # Merge manually-added cleaning tasks (Ménage/Serviette) from the Notes tab
            sched = merge_into_schedule(sched, st.session_state.notes)
            workers = st.session_state.workers

            if not sched:
                st.warning("Aucun ménage détecté dans cette extraction.")
            else:
                days = sorted(sched.keys())
                total = sum(len(v) for v in sched.values())
                st.success(
                    f"✅ {len(res)} réservations confirmées · {total} ménages "
                    f"du {days[0].strftime('%d/%m/%Y')} au {days[-1].strftime('%d/%m/%Y')}")

                fmt_mois = st.radio(
                    "Format du calendrier mensuel", ["Excel", "PDF"],
                    horizontal=True, key="fmt_mois")
                if st.button("📥 Enregistrer le calendrier mensuel complet"):
                    base = f"Calendrier_menages_{days[0].strftime('%Y_%m')}"
                    if fmt_mois == "Excel":
                        save_and_report(
                            lambda p: build_month_workbook(sched, workers, p), base + ".xlsx")
                    else:
                        save_and_report(
                            lambda p: build_month_pdf(sched, workers, p), base + ".pdf")

                st.divider()
                st.subheader("Aperçu d'une journée")
                chosen = st.selectbox(
                    "Choisir une date", days,
                    format_func=lambda d: f"{WEEKDAYS_FR[d.weekday()]} {d.strftime('%d/%m/%Y')} "
                                          f"({len(sched[d])} ménages)")
                da = assign_day(sched[chosen], workers, chosen)

                active = [n for n, t in da.assignments.items() if t]
                ncols = max(1, len(active) + (1 if da.unassigned else 0))
                cols = st.columns(ncols)
                i = 0
                for name, tasks in da.assignments.items():
                    if not tasks:
                        continue
                    with cols[i]:
                        st.markdown(f"**{name}** ({len(tasks)})")
                        for t in sorted(tasks, key=lambda x: x.room):
                            icon = {"depart": "🔴", "service": "🔵", "manuel": "🟩"}.get(t.kind, "⚪")
                            st.write(f"{icon} {t.room} · ét.{t.floor} {t.night_label}")
                    i += 1
                if da.unassigned:
                    with cols[i]:
                        st.markdown("**🟡 Gérants (à replanifier)**")
                        for t in sorted(da.unassigned, key=lambda x: x.room):
                            st.write(f"⚠️ {t.room} · ét.{t.floor}")

                fmt_jour = st.radio(
                    "Format de la feuille du jour", ["Excel", "PDF"],
                    horizontal=True, key="fmt_jour_mois")
                if st.button("📥 Enregistrer la feuille de ce jour"):
                    base = f"Feuille_{chosen.strftime('%Y_%m_%d')}"
                    if fmt_jour == "Excel":
                        save_and_report(lambda p: build_day_sheet(da, p), base + ".xlsx")
                    else:
                        save_and_report(lambda p: build_day_pdf(da, p), base + ".pdf")
        except Exception as e:
            st.error(f"Erreur lors du traitement : {e}")
        finally:
            os.unlink(tmp_path)


# ════════════════════════════════════════════════════════════════════
#  ONGLET 2 — FEUILLE DU JOUR (PDF, identique au projet housekeeping)
# ════════════════════════════════════════════════════════════════════
with tab_jour:
    st.caption(
        "Déposez le PDF « état des chambres » d'une journée. La feuille de jour "
        "générée est identique à celle du projet housekeeping.")
    pdf_file = st.file_uploader("État des chambres (PDF)", type=["pdf"], key="up_jour")

    if pdf_file:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_file.read())
            pdf_path = tmp.name
        try:
            data = parse_pdf(pdf_path)
            st.success(
                f"📅 {data['date'] or 'Date non détectée'} — "
                f"{len(data['arrivees'])} arrivée(s), {len(data['departs'])} départ(s), "
                f"{len(data['service'])} service(s)")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**Arrivées**")
                for r in data["arrivees"]:
                    st.write(f"🟢 {r.room} — {r.name}")
            with c2:
                st.markdown("**Départs**")
                for r in data["departs"]:
                    st.write(f"🔴 {r.room} — {r.name}")
            with c3:
                st.markdown("**Service**")
                for r in data["service"]:
                    extra = f" ({r.extra})" if r.extra else ""
                    st.write(f"🔵 {r.room} — {r.name}{extra}")

            fmt_hk = st.radio(
                "Format de la feuille du jour", ["Excel", "PDF"],
                horizontal=True, key="fmt_jour_hk")
            if st.button("📥 Enregistrer la feuille du jour"):
                slug = (data["date"] or "feuille_du_jour").replace(" ", "_")[:30]
                base = f"Feuille_de_jour_{slug}"
                if fmt_hk == "Excel":
                    save_and_report(lambda p: generate_excel(data, p), base + ".xlsx")
                else:
                    save_and_report(lambda p: build_housekeeping_day_pdf(data, p), base + ".pdf")
        except Exception as e:
            st.error(f"Erreur lors du traitement : {e}")
        finally:
            os.unlink(pdf_path)


# ════════════════════════════════════════════════════════════════════
#  ONGLET 3 — NOTES / TÂCHES MANUELLES
# ════════════════════════════════════════════════════════════════════
with tab_notes:
    st.caption(
        "Ajoutez des tâches à la main. « Ménage » et « Serviette » apparaissent "
        "sur la feuille du jour de la date choisie (onglet Feuille du mois). "
        "« Autre » est une note libre, conservée mais non affichée sur la feuille. "
        "Tout est enregistré automatiquement."
    )

    with st.form("add_note", clear_on_submit=True):
        cols = st.columns([2, 2, 1.3, 3])
        n_date = cols[0].date_input("Date")
        n_type = cols[1].selectbox("Type", TYPES)
        room_choices = ["—"] + [str(r) for r in ALL_ROOMS]
        n_room = cols[2].selectbox(
            "N° de chambre", room_choices,
            help="Le numéro exact de la chambre (ex. 204). « — » = aucune, pour une note « Autre ».")
        n_comment = cols[3].text_input("Commentaire / note")
        if st.form_submit_button("➕ Ajouter"):
            room = int(n_room) if n_room != "—" else None
            if n_type in ("Ménage", "Serviette", "Chien") and not room:
                st.warning("Choisissez un numéro de chambre pour une tâche Ménage / Serviette / Chien.")
            else:
                st.session_state.notes.append(ManualTask(
                    date=n_date.isoformat(), type=n_type, room=room, comment=n_comment))
                save_notes(st.session_state.notes, NOTES_PATH)
                st.rerun()

    st.divider()
    if not st.session_state.notes:
        st.info("Aucune note pour le moment.")
    else:
        h = st.columns([2, 2, 1, 4, 1])
        for col, lbl in zip(h, ["Date", "Type", "Chambre", "Commentaire", ""]):
            col.markdown(f"**{lbl}**")
        for i, n in enumerate(sorted(st.session_state.notes, key=lambda x: (x.date, x.type))):
            c = st.columns([2, 2, 1, 4, 1])
            c[0].write(n.date)
            c[1].write(n.type)
            c[2].write(str(n.room) if n.room else "—")
            c[3].write(n.comment or "")
            if c[4].button("🗑", key=f"delnote_{i}"):
                st.session_state.notes.remove(n)
                save_notes(st.session_state.notes, NOTES_PATH)
                st.rerun()


# ════════════════════════════════════════════════════════════════════
#  ONGLET 4 — FEUILLE DU PERSONNEL (temps de travail)
# ════════════════════════════════════════════════════════════════════
def _to_time(s):
    if not s:
        return None
    hh, mm = s.split(":")
    return time(int(hh), int(mm))


def _from_time(t):
    # st.data_editor may return a str ("HH:MM[:SS]"), a datetime.time,
    # a pandas Timestamp/NaT, or None — normalise all to "HH:MM".
    if isinstance(t, str):
        return t.strip()[:5]
    if t is None or pd.isna(t):
        return ""
    try:
        return t.strftime("%H:%M")
    except Exception:
        return ""


with tab_perso:
    st.caption(
        "Suivi des heures par employé sur deux semaines : pour chaque jour, "
        "heure d'arrivée, heure de départ et pause (en minutes). Les heures "
        "travaillées sont calculées automatiquement. Tout est enregistré."
    )

    # Manage employees who are NOT in the cleaning team (reception, etc.)
    with st.expander("👤 Employés hors équipe ménage (accueil, maintenance…)"):
        st.caption("Ces employés comptent leurs heures ici mais n'apparaissent "
                   "jamais dans la répartition des chambres.")
        with st.form("add_extra", clear_on_submit=True):
            ec = st.columns([3, 3, 1])
            x_name = ec[0].text_input("Nom")
            x_role = ec[1].text_input("Rôle (ex. Accueil)")
            if ec[2].form_submit_button("➕") and x_name.strip():
                st.session_state.extra.append(
                    ExtraEmployee(name=x_name.strip(), role=x_role.strip()))
                save_extra_staff(st.session_state.extra, EXTRA_PATH)
                st.rerun()
        for i, x in enumerate(st.session_state.extra):
            rc = st.columns([3, 3, 1])
            rc[0].write(x.name)
            rc[1].write(x.role or "—")
            if rc[2].button("🗑", key=f"delextra_{i}"):
                request_delete("extra", x.name, f"l'employé « {x.name} »")
                st.rerun()

    cleaning_names = [w.name for w in sorted(st.session_state.workers, key=lambda x: x.order)]
    extra_names = [x.name for x in st.session_state.extra]
    role_of = {w.name: "Équipe ménage"
               for w in st.session_state.workers}
    role_of.update({x.name: (x.role or "Hors ménage") for x in st.session_state.extra})
    names = cleaning_names + [n for n in extra_names if n not in cleaning_names]

    if not names:
        st.info("Ajoutez d'abord des préposées (onglet « Feuille du mois ») "
                "ou un employé hors équipe ci-dessus.")
    else:
        c1, c2 = st.columns([2, 2])
        emp = c1.selectbox("Employé", names, key="ts_emp")
        start = c2.date_input(
            "Début de la quinzaine", value=monday_of(date.today()), key="ts_start")
        dates = fortnight(start)
        ts = st.session_state.timesheet

        st.write(
            f"Période : **{dates[0].strftime('%d/%m/%Y')} → {dates[-1].strftime('%d/%m/%Y')}**")

        # Build the editor's base table ONCE per employee/period and keep it
        # stable in session_state. Rebuilding it on every rerun conflicts with
        # the editor's own edit-tracking and drops the first keystroke.
        df_key = f"ts_df_{emp}_{start.isoformat()}"
        if df_key not in st.session_state:
            rows = []
            for d in dates:
                e = get_entry(ts, emp, d.isoformat())
                rows.append({
                    "Jour": f"{WEEKDAYS_FR[d.weekday()][:3]} {d.strftime('%d/%m')}",
                    "Arrivée": _to_time(e["arrivee"]),
                    "Départ": _to_time(e["depart"]),
                    "Pause (min)": int(e.get("pause", 0)),
                    "Pourboires ($)": float(e.get("tips", 0)),
                })
            st.session_state[df_key] = pd.DataFrame(rows)

        st.caption("Saisissez l'heure puis appuyez sur **Entrée** (ou cliquez ailleurs) pour valider.")
        edited = st.data_editor(
            st.session_state[df_key],
            key=f"ts_editor_{emp}_{start.isoformat()}",
            hide_index=True, use_container_width=True,
            column_config={
                "Jour": st.column_config.TextColumn("Jour", disabled=True),
                "Arrivée": st.column_config.TimeColumn("Arrivée", format="HH:mm", step=60),
                "Départ": st.column_config.TimeColumn("Départ", format="HH:mm", step=60),
                "Pause (min)": st.column_config.NumberColumn("Pause (min)", min_value=0, step=5),
                "Pourboires ($)": st.column_config.NumberColumn(
                    "Pourboires ($)", min_value=0, step=1, format="%.2f"),
            },
        )

        # Compute hours directly from what was typed, persist, and total it.
        total = 0.0
        total_tips = 0.0
        hours_per_day = []
        tips_per_day = []
        for i, d in enumerate(dates):
            arr = _from_time(edited.iloc[i]["Arrivée"])
            dep = _from_time(edited.iloc[i]["Départ"])
            pv = edited.iloc[i]["Pause (min)"]
            pause = int(pv) if pd.notna(pv) else 0
            tv = edited.iloc[i]["Pourboires ($)"]
            tips = float(tv) if pd.notna(tv) else 0.0
            set_entry(ts, emp, d.isoformat(), arr, dep, pause, tips)
            h = worked_hours(arr, dep, pause)
            hours_per_day.append(h)
            tips_per_day.append(round(tips, 2))
            total += h
            total_tips += tips
        save_timesheet(ts, TIMESHEET_PATH)

        # Per-day recap (read-only)
        recap_df = pd.DataFrame({
            "Jour": edited["Jour"],
            "Heures travaillées": hours_per_day,
            "Pourboires ($)": tips_per_day,
        })
        st.dataframe(
            recap_df, hide_index=True, use_container_width=True,
            column_config={
                "Heures travaillées": st.column_config.NumberColumn(format="%.2f h"),
                "Pourboires ($)": st.column_config.NumberColumn(format="%.2f $"),
            },
        )

        m1, m2 = st.columns(2)
        m1.metric(f"Total des heures — {emp}", f"{round(total, 2)} h")
        m2.metric(f"Total pourboires — {emp}", f"{round(total_tips, 2)} $")

        st.divider()
        st.markdown("**Totaux de la quinzaine (tout le personnel)**")
        summary = pd.DataFrame(
            [{"Employé": n, "Rôle": role_of.get(n, ""),
              "Heures": period_total(ts, n, dates),
              "Pourboires ($)": period_tips(ts, n, dates)} for n in names])
        st.dataframe(
            summary, hide_index=True, use_container_width=True,
            column_config={"Pourboires ($)": st.column_config.NumberColumn(format="%.2f $")},
        )

        if st.button("📥 Télécharger l'Excel de la quinzaine (pour les paies)"):
            employees = [(n, role_of.get(n, "")) for n in names]
            save_and_report(
                lambda p: build_timesheet_workbook(dates, employees, ts, p),
                f"Paie_{dates[0].strftime('%Y_%m_%d')}_au_{dates[-1].strftime('%Y_%m_%d')}.xlsx")
