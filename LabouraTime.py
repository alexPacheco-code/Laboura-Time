# app_timer_hist.py
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QInputDialog, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QFileDialog, QTabWidget, QTableWidget, QTableWidgetItem, QDateEdit,
    QDialog, QFormLayout, QLineEdit, QDateTimeEdit, QDialogButtonBox, QCheckBox
)
from PySide6.QtCore import QTimer, Qt, QDate, QDateTime
import sys, time, json, csv, uuid
from datetime import datetime, date, time as dtime
from pathlib import Path
from collections import defaultdict

DATA_FILE = Path("data.json")


# ============== utils ==============
def fmt_hms(seconds: int | float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def ts_to_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts).isoformat(sep=" ", timespec="seconds")


def recalc_totals_from_sessions(sessions):
    sections = defaultdict(lambda: defaultdict(int))
    for s in sessions:
        sections[s["section"]][s["sub"]] += int(s["seconds"])
    return sections


def load_data():
    if DATA_FILE.exists():
        try:
            raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            sessions = raw.get("sessions", [])
            for s in sessions:
                if "id" not in s:
                    s["id"] = str(uuid.uuid4())
            sections = recalc_totals_from_sessions(sessions)
            current = raw.get("current", None)
            return sections, current, sessions
        except Exception as e:
            print("WARN load_data:", e)
    return defaultdict(lambda: defaultdict(int)), None, []


def save_data(sections, current, sessions):
    payload = {
        "sections": {s: dict(subs) for s, subs in sections.items()},
        "current": current,
        "sessions": sessions,
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ============== diálogo de edición ==============
class EditSessionDialog(QDialog):
    def __init__(self, parent, session):
        super().__init__(parent)
        self.setWindowTitle("Editar sesión")
        self.session = dict(session)

        lay = QFormLayout(self)
        self.le_section = QLineEdit(self.session["section"])
        self.le_sub = QLineEdit(self.session["sub"])

        self.dt_start = QDateTimeEdit(self)
        self.dt_start.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dt_start.setCalendarPopup(True)
        self.dt_end = QDateTimeEdit(self)
        self.dt_end.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dt_end.setCalendarPopup(True)

        self.dt_start.setDateTime(QDateTime.fromSecsSinceEpoch(int(self.session["start_ts"])))
        self.dt_end.setDateTime(QDateTime.fromSecsSinceEpoch(int(self.session["end_ts"])))

        lay.addRow("Sección:", self.le_section)
        lay.addRow("Subdivisión:", self.le_sub)
        lay.addRow("Inicio:", self.dt_start)
        lay.addRow("Fin:", self.dt_end)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addRow(buttons)

    def get_result(self):
        section = (self.le_section.text() or "").strip()
        sub = (self.le_sub.text() or "").strip()
        if not section or not sub:
            QMessageBox.warning(self, "Validación", "Sección y Subdivisión no pueden estar vacías.")
            return None
        t0 = self.dt_start.dateTime().toSecsSinceEpoch()
        t1 = self.dt_end.dateTime().toSecsSinceEpoch()
        if t1 <= t0:
            QMessageBox.warning(self, "Validación", "Fin debe ser posterior a Inicio.")
            return None
        seconds = int(t1 - t0)
        out = dict(self.session)
        out.update({
            "section": section, "sub": sub,
            "start_ts": float(t0), "end_ts": float(t1),
            "start_iso": ts_to_iso(t0), "end_iso": ts_to_iso(t1),
            "seconds": seconds
        })
        return out

# ============== tema / estilos ==============
from PySide6.QtGui import QPalette, QColor

QSS = """
* { font-family: "Segoe UI","Inter","Helvetica Neue", Arial; font-size: 12.5pt; }

QWidget { background: #111418; color: #E6E6E6; }
QToolTip { background: #2B323B; color: #E6E6E6; border: 1px solid #2A2F36; }

QLabel#elapsedLCD {
  font-family: "JetBrains Mono","Consolas", monospace;
  font-weight: 600; font-size: 28pt;
  padding: 8px 12px; border-radius: 14px;
  background: #0B0E11; border: 1px solid #2A2F36;
}

QPushButton {
  padding: 8px 14px; border-radius: 10px;
  border: 1px solid #2A2F36; background: #1A1F24;
}
QPushButton:hover { background: #232A31; }
QPushButton:pressed { background: #0F1419; }
QPushButton:disabled { color: #7A828E; background: #151A1F; border-color: #2A2F36; }

QPushButton#btnStart {
  border-color: #3D7DFF;
  box-shadow: none;
}
QPushButton#btnStop {
  border-color: #E35D5B;
}

QComboBox, QDateEdit, QLineEdit, QDateTimeEdit {
  background: #0F1419; color: #E6E6E6;
  border: 1px solid #2A2F36; border-radius: 8px; padding: 6px 8px;
}
QComboBox::drop-down { width: 24px; border: none; }
QComboBox QAbstractItemView {
  background: #0F1419; color: #E6E6E6;
  selection-background-color: #2B323B; outline: 0;
}

QTabWidget::pane { border: 1px solid #2A2F36; border-radius: 12px; padding: 6px; }
QTabBar::tab {
  background: #151A1F; padding: 8px 14px; margin: 2px; border-radius: 10px;
}
QTabBar::tab:selected { background: #1F252B; }

QTreeWidget, QTableWidget {
  background: #0F1419; color: #E6E6E6;
  border: 1px solid #2A2F36; border-radius: 12px;
  gridline-color: #2A2F36;
}
QHeaderView::section {
  background: #151A1F; color: #E6E6E6;
  padding: 6px 8px; border: 0px;
  border-right: 1px solid #2A2F36; border-bottom: 1px solid #2A2F36;
}
QTableWidget::item:selected, QTreeView::item:selected { background: #2B323B; }
QCheckBox { spacing: 8px; }
"""

def apply_theme(app, dark=True):
    # Estilo base moderno (Fusion)
    app.setStyle("Fusion")
    if dark:
        pal = QPalette()
        pal.setColor(QPalette.Window, QColor("#111418"))
        pal.setColor(QPalette.WindowText, QColor("#E6E6E6"))
        pal.setColor(QPalette.Base, QColor("#0F1419"))
        pal.setColor(QPalette.AlternateBase, QColor("#151A1F"))
        pal.setColor(QPalette.Text, QColor("#E6E6E6"))
        pal.setColor(QPalette.Button, QColor("#1A1F24"))
        pal.setColor(QPalette.ButtonText, QColor("#E6E6E6"))
        pal.setColor(QPalette.ToolTipBase, QColor("#2B323B"))
        pal.setColor(QPalette.ToolTipText, QColor("#E6E6E6"))
        pal.setColor(QPalette.Highlight, QColor("#3D7DFF"))
        pal.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        app.setPalette(pal)
    app.setStyleSheet(QSS)


# ============== app principal ==============
class SectionTimerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laboura Time")
        self.sections, self.current, self.sessions = load_data()
        self._running = False
        self._t0 = None

        self.tabs = QTabWidget()
        self.timer_tab = QWidget()
        self.history_tab = QWidget()
        self._build_timer_tab(self.timer_tab)
        self._build_history_tab(self.history_tab)
        self.tabs.addTab(self.timer_tab, "Timer")
        self.tabs.addTab(self.history_tab, "Histórico")

        root = QVBoxLayout(self)
        root.addWidget(self.tabs)

        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(200)
        self.ui_timer.timeout.connect(self._update_label)

        # init
        self._refresh_sections()
        self._refresh_subs()
        self._rebuild_tree()
        self._refresh_history_filters()
        self.apply_history_filters()

    # ---------- pestaña Timer ----------
    def _build_timer_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)

        sel_row = QHBoxLayout()
        self.cmb_section = QComboBox()
        self.cmb_sub = QComboBox()
        self.btn_add_section = QPushButton("+ Sección")
        self.btn_add_sub = QPushButton("+ Subdivisión")
        self.btn_rename_section = QPushButton("Renombrar sección")
        self.btn_rename_sub = QPushButton("Renombrar subdivisión")

        sel_row.addWidget(self.cmb_section)
        sel_row.addWidget(self.btn_add_section)
        sel_row.addWidget(self.btn_rename_section)
        sel_row.addWidget(self.cmb_sub)
        sel_row.addWidget(self.btn_add_sub)
        sel_row.addWidget(self.btn_rename_sub)

        self.elapsed_label = QLabel("00:00:00", alignment=Qt.AlignCenter)
        ctrl_row = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        self.btn_export_totals = QPushButton("Export Totals CSV")
        ctrl_row.addWidget(self.btn_start)
        ctrl_row.addWidget(self.btn_stop)
        ctrl_row.addWidget(self.btn_export_totals)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Sección / Subdivisión", "Tiempo acumulado"])

        layout.addLayout(sel_row)
        layout.addWidget(self.elapsed_label)
        layout.addLayout(ctrl_row)
        layout.addWidget(self.tree)

        # conexiones
        self.btn_add_section.clicked.connect(self.add_section)
        self.btn_add_sub.clicked.connect(self.add_sub)
        self.btn_rename_section.clicked.connect(self.rename_section)
        self.btn_rename_sub.clicked.connect(self.rename_sub)
        self.cmb_section.currentIndexChanged.connect(self._on_section_change)
        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_export_totals.clicked.connect(self.export_totals_csv)

    # ---------- pestaña Histórico ----------
    def _build_history_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)

        # filtros fila 1
        filt1 = QHBoxLayout()
        self.cmb_hist_section = QComboBox()
        self.cmb_hist_sub = QComboBox()
        self.cmb_hist_section.currentIndexChanged.connect(self._on_hist_section_change)
        filt1.addWidget(QLabel("Sección:"))
        filt1.addWidget(self.cmb_hist_section)
        filt1.addWidget(QLabel("Subdivisión:"))
        filt1.addWidget(self.cmb_hist_sub)

        # filtros fila 2
        filt2 = QHBoxLayout()
        self.date_from = QDateEdit(); self.date_from.setCalendarPopup(True)
        self.date_to = QDateEdit();   self.date_to.setCalendarPopup(True)
        self.cmb_group = QComboBox(); self.cmb_group.addItems(["Sin agrupar", "Día", "Semana", "Mes"])
        self.chk_merge = QCheckBox("Combinar subdivisiones")
        self.btn_apply_filters = QPushButton("Aplicar filtros")
        self.btn_clear_filters = QPushButton("Limpiar")
        self.btn_export_sessions = QPushButton("Export Sessions CSV")

        filt2.addWidget(QLabel("Desde:")); filt2.addWidget(self.date_from)
        filt2.addWidget(QLabel("Hasta:")); filt2.addWidget(self.date_to)
        filt2.addSpacing(12)
        filt2.addWidget(QLabel("Agrupar por:")); filt2.addWidget(self.cmb_group)
        filt2.addWidget(self.chk_merge)
        filt2.addStretch(1)
        filt2.addWidget(self.btn_apply_filters)
        filt2.addWidget(self.btn_clear_filters)
        filt2.addWidget(self.btn_export_sessions)

        # acciones
        actions = QHBoxLayout()
        self.btn_edit = QPushButton("Editar sesión")
        self.btn_delete = QPushButton("Borrar seleccionadas")
        actions.addWidget(self.btn_edit)
        actions.addWidget(self.btn_delete)
        actions.addStretch(1)

        # tablas: sesiones (6 cols) + resumen (4 cols)
        self.tbl_sessions = QTableWidget(0, 6)
        self.tbl_sessions.setHorizontalHeaderLabels(
            ["ID", "Sección", "Subdivisión", "Inicio", "Fin", "HH:MM:SS"]
        )
        self.tbl_sessions.setSortingEnabled(True)
        self.tbl_sessions.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_sessions.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_sessions.setColumnHidden(0, True)

        self.tbl_summary = QTableWidget(0, 4)
        self.tbl_summary.setHorizontalHeaderLabels(
            ["Periodo", "Sección", "Subdivisión", "HH:MM:SS"]
        )
        self.tbl_summary.setSortingEnabled(True)
        self.tbl_summary.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_summary.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_summary.hide()

        layout.addLayout(filt1)
        layout.addLayout(filt2)
        layout.addLayout(actions)
        layout.addWidget(self.tbl_sessions)
        layout.addWidget(self.tbl_summary)

        # conexiones
        self.btn_apply_filters.clicked.connect(self.apply_history_filters)
        self.btn_clear_filters.clicked.connect(self.clear_history_filters)
        self.btn_export_sessions.clicked.connect(self.export_sessions_csv)
        self.btn_edit.clicked.connect(self.edit_selected_session)
        self.btn_delete.clicked.connect(self.delete_selected_sessions)
        self.cmb_group.currentIndexChanged.connect(self.apply_history_filters)
        self.chk_merge.stateChanged.connect(self.apply_history_filters)

    # ---------- helpers UI ----------
    def _rebuild_tree(self):
        self.tree.clear()
        for sec in sorted(self.sections.keys()):
            sec_total = sum(self.sections[sec].values())
            sec_item = QTreeWidgetItem([sec, fmt_hms(sec_total)])
            for sub, secs in sorted(self.sections[sec].items()):
                sec_item.addChild(QTreeWidgetItem([f" └ {sub}", fmt_hms(secs)]))
            self.tree.addTopLevelItem(sec_item)
        self.tree.expandAll()

    def _refresh_sections(self, select=None):
        self.cmb_section.blockSignals(True)
        self.cmb_section.clear()
        self.cmb_section.addItems(sorted(self.sections.keys()))
        self.cmb_section.blockSignals(False)
        if select:
            idx = self.cmb_section.findText(select)
            if idx >= 0:
                self.cmb_section.setCurrentIndex(idx)

    def _refresh_subs(self, select=None):
        sec = self.cmb_section.currentText()
        self.cmb_sub.clear()
        if not sec:
            return
        self.cmb_sub.addItems(sorted(self.sections[sec].keys()))
        if select:
            idx = self.cmb_sub.findText(select)
            if idx >= 0:
                self.cmb_sub.setCurrentIndex(idx)

    def _refresh_history_filters(self):
        self.cmb_hist_section.blockSignals(True)
        self.cmb_hist_section.clear()
        self.cmb_hist_section.addItem("Todas")
        self.cmb_hist_section.addItems(sorted(self.sections.keys()))
        self.cmb_hist_section.blockSignals(False)
        self._on_hist_section_change()
        today = QDate.currentDate()
        self.date_to.setDate(today)
        self.date_from.setDate(today.addDays(-30))

    def _on_hist_section_change(self):
        self.cmb_hist_sub.blockSignals(True)
        self.cmb_hist_sub.clear()
        self.cmb_hist_sub.addItem("Todas")
        sec = self.cmb_hist_section.currentText()
        if sec and sec != "Todas":
            for sub in sorted(self.sections.get(sec, {}).keys()):
                self.cmb_hist_sub.addItem(sub)
        self.cmb_hist_sub.blockSignals(False)

    # ---------- acciones Timer ----------
    def add_section(self):
        name, ok = QInputDialog.getText(self, "Nueva sección", "Nombre:")
        name = (name or "").strip()
        if ok and name:
            if name in self.sections:
                QMessageBox.information(self, "Info", "Esa sección ya existe.")
            else:
                _ = self.sections[name]
                save_data(self.sections, self.current, self.sessions)
                self._refresh_sections(select=name)
                self._refresh_subs()
                self._rebuild_tree()
                self._refresh_history_filters()

    def add_sub(self):
        sec = self.cmb_section.currentText()
        if not sec:
            QMessageBox.warning(self, "Atención", "Primero crea o selecciona una sección.")
            return
        name, ok = QInputDialog.getText(self, "Nueva subdivisión", "Nombre:")
        name = (name or "").strip()
        if ok and name:
            if name in self.sections[sec]:
                QMessageBox.information(self, "Info", "Ya existe esa subdivisión.")
            else:
                self.sections[sec][name] = 0
                save_data(self.sections, self.current, self.sessions)
                self._refresh_subs(select=name)
                self._rebuild_tree()
                self._refresh_history_filters()

    def start(self):
        sec = self.cmb_section.currentText()
        sub = self.cmb_sub.currentText()
        if not sec or not sub:
            QMessageBox.warning(self, "Atención", "Selecciona sección y subdivisión.")
            return
        if self._running:
            QMessageBox.information(self, "Info", "Ya está en marcha.")
            return
        self._running = True
        self._t0 = time.time()
        self.current = {"section": sec, "sub": sub, "start_ts": self._t0}
        save_data(self.sections, self.current, self.sessions)
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.ui_timer.start()

    def stop(self):
        if not self._running:
            return
        self._running = False
        self.ui_timer.stop()
        t1 = time.time()
        elapsed = int(t1 - self._t0)
        sec = self.current["section"]
        sub = self.current["sub"]
        self.sessions.append({
            "id": str(uuid.uuid4()),
            "section": sec, "sub": sub,
            "start_ts": float(self._t0), "end_ts": float(t1),
            "start_iso": ts_to_iso(self._t0), "end_iso": ts_to_iso(t1),
            "seconds": elapsed
        })
        self.sections = recalc_totals_from_sessions(self.sessions)
        self._t0 = None
        self.current = None
        self.elapsed_label.setText("00:00:00")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        save_data(self.sections, self.current, self.sessions)
        self._rebuild_tree()
        if self.tabs.currentWidget() is self.history_tab:
            self.apply_history_filters()

    def _update_label(self):
        if self._running:
            self.elapsed_label.setText(fmt_hms(time.time() - self._t0))

    def _on_section_change(self):
        self._refresh_subs()

    # ---------- renombrar ----------
    def rename_section(self):
        old = self.cmb_section.currentText()
        if not old:
            QMessageBox.information(self, "Renombrar sección", "No hay sección seleccionada.")
            return
        new, ok = QInputDialog.getText(self, "Renombrar sección", f"Nuevo nombre para '{old}':")
        new = (new or "").strip()
        if not ok or not new or new == old:
            return
        for s in self.sessions:
            if s["section"] == old:
                s["section"] = new
        self.sections = recalc_totals_from_sessions(self.sessions)
        save_data(self.sections, self.current, self.sessions)
        self._refresh_sections(select=new)
        self._refresh_subs()
        self._rebuild_tree()
        self._refresh_history_filters()
        self.apply_history_filters()
        QMessageBox.information(self, "Renombrar sección", f"Sección '{old}' renombrada a '{new}'.")

    def rename_sub(self):
        sec = self.cmb_section.currentText()
        sub_old = self.cmb_sub.currentText()
        if not sec or not sub_old:
            QMessageBox.information(self, "Renombrar subdivisión", "Selecciona sección y subdivisión.")
            return
        sub_new, ok = QInputDialog.getText(self, "Renombrar subdivisión", f"Nuevo nombre para '{sub_old}' en '{sec}':")
        sub_new = (sub_new or "").strip()
        if not ok or not sub_new or sub_new == sub_old:
            return
        for s in self.sessions:
            if s["section"] == sec and s["sub"] == sub_old:
                s["sub"] = sub_new
        self.sections = recalc_totals_from_sessions(self.sessions)
        save_data(self.sections, self.current, self.sessions)
        self._refresh_subs(select=sub_new)
        self._rebuild_tree()
        self._refresh_history_filters()
        self.apply_history_filters()
        QMessageBox.information(self, "Renombrar subdivisión", f"Subdivisión renombrada a '{sub_new}'.")

    # ---------- filtros histórico / agrupación ----------
    def _collect_filters(self):
        sec = self.cmb_hist_section.currentText()
        sub = self.cmb_hist_sub.currentText()
        dfrom = self.date_from.date()
        dto = self.date_to.date()
        start_ts = datetime.combine(date(dfrom.year(), dfrom.month(), dfrom.day()), dtime.min).timestamp()
        end_ts = datetime.combine(date(dto.year(), dto.month(), dto.day()), dtime.max).timestamp()
        return sec, sub, start_ts, end_ts

    def apply_history_filters(self):
        self.filtered_sessions = []
        sec_filter, sub_filter, start_ts, end_ts = self._collect_filters()
        for s in self.sessions:
            cond_sec = (sec_filter == "Todas") or (s["section"] == sec_filter)
            cond_sub = (sub_filter == "Todas") or (s["sub"] == sub_filter)
            in_range = (s["start_ts"] >= start_ts) and (s["start_ts"] <= end_ts)
            if cond_sec and cond_sub and in_range:
                self.filtered_sessions.append(s)
        self._fill_history_table(self.filtered_sessions)
        self._maybe_fill_summary(self.filtered_sessions)

    def clear_history_filters(self):
        self._refresh_history_filters()
        self.apply_history_filters()

    def _fill_history_table(self, sessions):
        self.tbl_sessions.setRowCount(0)
        self.tbl_sessions.setSortingEnabled(False)
        for s in sessions:
            row = self.tbl_sessions.rowCount()
            self.tbl_sessions.insertRow(row)
            secs = int(s["seconds"])
            vals = [
                s["id"],
                s["section"],
                s["sub"],
                s.get("start_iso") or ts_to_iso(s["start_ts"]),
                s.get("end_iso") or ts_to_iso(s["end_ts"]),
                fmt_hms(secs)
            ]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(v)
                # Orden correcto por HH:MM:SS usando segundos como clave oculta
                if col == 5:
                    item.setData(Qt.ItemDataRole.UserRole, secs)
                self.tbl_sessions.setItem(row, col, item)
        self.tbl_sessions.setSortingEnabled(True)
        self.tbl_sessions.resizeColumnsToContents()

    def _period_key(self, ts: float, mode: str) -> str:
        dt = datetime.fromtimestamp(ts)
        if mode == "Día":
            return dt.strftime("%Y-%m-%d")
        if mode == "Semana":
            iso = dt.isocalendar()
            return f"{iso.year}-W{iso.week:02d}"
        if mode == "Mes":
            return dt.strftime("%Y-%m")
        return ""

    def _maybe_fill_summary(self, sessions):
        mode = self.cmb_group.currentText()
        if mode == "Sin agrupar":
            self.tbl_summary.hide()
            return

        merge_subs = self.chk_merge.isChecked()
        agg = defaultdict(int)
        for s in sessions:
            period = self._period_key(s["start_ts"], mode)
            key = (period, s["section"], "(Todas)" if merge_subs else s["sub"])
            agg[key] += int(s["seconds"])

        self.tbl_summary.setRowCount(0)
        self.tbl_summary.setSortingEnabled(False)
        for (period, sec, sub), secs in sorted(agg.items()):
            row = self.tbl_summary.rowCount()
            self.tbl_summary.insertRow(row)
            secs = int(secs)
            vals = [period, sec, sub, fmt_hms(secs)]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(v)
                # ordenar por HH:MM:SS usando segundos como clave oculta
                if col == 3:
                    item.setData(Qt.ItemDataRole.UserRole, secs)
                self.tbl_summary.setItem(row, col, item)
        self.tbl_summary.setSortingEnabled(True)
        self.tbl_summary.resizeColumnsToContents()
        self.tbl_summary.show()

    # ---------- editar / borrar sesiones ----------
    def _get_selected_session_ids(self):
        ids = []
        for idx in self.tbl_sessions.selectionModel().selectedRows():
            sid = self.tbl_sessions.item(idx.row(), 0).text()
            ids.append(sid)
        return ids

    def edit_selected_session(self):
        ids = self._get_selected_session_ids()
        if len(ids) != 1:
            QMessageBox.information(self, "Editar sesión", "Selecciona exactamente una fila.")
            return
        sid = ids[0]
        sess = next((s for s in self.sessions if s["id"] == sid), None)
        if not sess:
            QMessageBox.warning(self, "Editar sesión", "No se encontró la sesión.")
            return
        dlg = EditSessionDialog(self, sess)
        if dlg.exec() == QDialog.Accepted:
            updated = dlg.get_result()
            if not updated:
                return
            for i, s in enumerate(self.sessions):
                if s["id"] == sid:
                    self.sessions[i] = updated
                    break
            self.sections = recalc_totals_from_sessions(self.sessions)
            save_data(self.sections, self.current, self.sessions)
            self._rebuild_tree()
            self.apply_history_filters()
            QMessageBox.information(self, "Editar sesión", "Sesión actualizada.")

    def delete_selected_sessions(self):
        ids = self._get_selected_session_ids()
        if not ids:
            QMessageBox.information(self, "Borrar sesiones", "Selecciona una o más filas.")
            return
        ans = QMessageBox.question(
            self, "Borrar sesiones",
            f"¿Seguro que quieres borrar {len(ids)} sesión(es)?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if ans != QMessageBox.Yes:
            return
        self.sessions = [s for s in self.sessions if s["id"] not in ids]
        self.sections = recalc_totals_from_sessions(self.sessions)
        save_data(self.sections, self.current, self.sessions)
        self._rebuild_tree()
        self.apply_history_filters()
        QMessageBox.information(self, "Borrar sesiones", "Sesión(es) eliminada(s).")

    # ---------- CSV ----------
    def export_totals_csv(self):
        if not self.sections:
            QMessageBox.information(self, "Export CSV", "No hay datos para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Totals CSV", "times_totals.csv", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            total_all = 0
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Section", "Subdivision", "Seconds", "HH:MM:SS"])
                for sec in sorted(self.sections.keys()):
                    for sub, secs in sorted(self.sections[sec].items()):
                        secs = int(secs)
                        w.writerow([sec, sub, secs, fmt_hms(secs)])
                        total_all += secs
                w.writerow([])
                w.writerow(["TOTAL", "", total_all, fmt_hms(total_all)])
            QMessageBox.information(self, "Export CSV", f"Exportado:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export CSV", f"Error exportando:\n{e}")

    def export_sessions_csv(self):
        rows = self.tbl_sessions.rowCount()
        if rows == 0:
            QMessageBox.information(self, "Export CSV", "No hay sesiones en la tabla para exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Sessions CSV", "times_sessions.csv", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                # Notar que aquí exportamos SIN “Seconds”
                w.writerow(["ID", "Section", "Subdivision", "Start", "End", "HH:MM:SS"])
                for r in range(rows):
                    w.writerow([self.tbl_sessions.item(r, c).text() for c in range(6)])
            QMessageBox.information(self, "Export CSV", f"Exportado:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export CSV", f"Error exportando:\n{e}")


# ============== run ==============
if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app, dark=True)
    w = SectionTimerApp()
    w.resize(1020, 640)
    w.show()
    sys.exit(app.exec())
