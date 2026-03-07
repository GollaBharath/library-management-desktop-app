"""Removed / archived students panel."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QFrame,
    QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import database as db
from styles import (
    TEXT_PRIMARY, TEXT_SECONDARY, DANGER, SUCCESS, WARNING,
    BG_CARD, BG_PANEL, ACCENT
)


class RemovedStudentsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("🗂️ Removed Students")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {TEXT_PRIMARY}; background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        root.addLayout(header)

        # Info banner
        banner = QFrame()
        banner.setStyleSheet(
            f"background-color: #1A1A2C; border: 1px solid #2A2A4A; border-radius: 8px;"
        )
        banner_l = QHBoxLayout(banner)
        banner_l.setContentsMargins(14, 10, 14, 10)
        info = QLabel(
            "ℹ️  This section shows all students who have been removed from the system. "
            "Their records are archived here for reference."
        )
        info.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        banner_l.addWidget(info)
        root.addWidget(banner)

        # Search
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search by name or phone…")
        self._search.textChanged.connect(self.refresh)
        search_row.addWidget(self._search)
        root.addLayout(search_row)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels([
            "Name", "Phone", "Type", "Shift/Seat",
            "Join Date", "Last Paid", "Removed On", "Reason", "Actions"
        ])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setColumnWidth(1, 130)
        self._table.setColumnWidth(2, 90)
        self._table.setColumnWidth(3, 100)
        self._table.setColumnWidth(4, 100)
        self._table.setColumnWidth(5, 100)
        self._table.setColumnWidth(6, 130)
        self._table.setColumnWidth(7, 130)
        self._table.setColumnWidth(8, 100)
        root.addWidget(self._table)

        # Count bar
        count_row = QHBoxLayout()
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        count_row.addWidget(self._count_lbl)
        count_row.addStretch()
        root.addLayout(count_row)

    def refresh(self):
        search = self._search.text().strip() if hasattr(self, "_search") else ""
        students = db.get_removed_students(search)
        self._table.setRowCount(len(students))
        self._count_lbl.setText(f"Total archived: {len(students)}")

        for row, s in enumerate(students):
            self._table.setRowHeight(row, 44)
            seat_shift = (
                f"Shift: {s['shift']}" if s["student_type"] == "Half-time"
                else (f"Seat: {s['seat_number']}" if s["seat_number"] else "–")
            )
            removed_at = s.get("removed_at", "")
            if removed_at and "T" in removed_at:
                removed_at = removed_at.split("T")[0]

            row_data = [
                s["name"], s["phone"], s["student_type"], seat_shift,
                s.get("join_date") or "–", s.get("last_payment_date") or "–",
                removed_at, s.get("removal_reason") or "–",
            ]
            for col, text in enumerate(row_data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                item.setForeground(QColor(TEXT_SECONDARY))
                self._table.setItem(row, col, item)

            # Action buttons
            cell_widget = QWidget()
            cell_widget.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(cell_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)

            del_btn = QPushButton("🗑️")
            del_btn.setToolTip("Permanently delete record")
            del_btn.setFixedSize(32, 32)
            del_btn.setStyleSheet(
                f"background-color: #2A2A3A; border-radius: 6px; color: {DANGER};"
                f"border: 1px solid {DANGER};"
            )
            del_btn.clicked.connect(lambda _, rid=s["id"]: self._delete_record(rid))
            btn_layout.addWidget(del_btn)
            btn_layout.addStretch()
            self._table.setCellWidget(row, 8, cell_widget)

    def _delete_record(self, record_id: int):
        reply = QMessageBox.question(
            self, "Delete Record",
            "Permanently delete this archived record? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.delete_removed_student_record(record_id)
            self.refresh()
