"""Overdue fee payments panel."""
from datetime import date
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QHeaderView,
    QAbstractItemView, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
import database as db
from styles import (
    TEXT_PRIMARY, TEXT_SECONDARY, ACCENT, SUCCESS, DANGER,
    WARNING, BG_CARD, BG_PANEL
)


class OverduePaymentsWidget(QWidget):
    data_changed = pyqtSignal()

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
        title = QLabel("⚠️ Overdue Fees")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {TEXT_PRIMARY}; background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()

        self._count_badge = QLabel("")
        self._count_badge.setStyleSheet(
            f"background-color: {DANGER}; color: white; font-weight: bold; "
            f"border-radius: 12px; padding: 4px 12px; font-size: 13px;"
        )
        header.addWidget(self._count_badge)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        send_all_btn = QPushButton("📱 Send All Reminders")
        send_all_btn.setObjectName("btn_warning")
        send_all_btn.clicked.connect(self._send_all_reminders)
        header.addWidget(send_all_btn)
        root.addLayout(header)

        # Info banner
        banner = QFrame()
        banner.setStyleSheet(
            f"background-color: #2C1A1A; border: 1px solid {DANGER}; "
            f"border-radius: 8px; padding: 4px;"
        )
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(14, 10, 14, 10)
        info_lbl = QLabel(
            "⚠️  Students listed below have overdue fee payments. "
            "Mark them as paid or send a WhatsApp reminder."
        )
        info_lbl.setStyleSheet(f"color: {DANGER}; background: transparent;")
        banner_layout.addWidget(info_lbl)
        root.addWidget(banner)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Name", "Phone", "Type", "Seat/Shift",
            "Last Paid", "Due Date", "Days Overdue", "Actions"
        ])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setColumnWidth(1, 130)
        self._table.setColumnWidth(2, 90)
        self._table.setColumnWidth(3, 110)
        self._table.setColumnWidth(4, 110)
        self._table.setColumnWidth(5, 110)
        self._table.setColumnWidth(6, 100)
        self._table.setColumnWidth(7, 200)
        root.addWidget(self._table)

    def refresh(self):
        students = db.get_overdue_students()
        today = date.today()
        self._table.setRowCount(len(students))

        self._count_badge.setText(f"{len(students)} overdue")
        if len(students) == 0:
            self._count_badge.setStyleSheet(
                f"background-color: {SUCCESS}; color: white; font-weight: bold; "
                f"border-radius: 12px; padding: 4px 12px; font-size: 13px;"
            )
        else:
            self._count_badge.setStyleSheet(
                f"background-color: {DANGER}; color: white; font-weight: bold; "
                f"border-radius: 12px; padding: 4px 12px; font-size: 13px;"
            )

        for row, s in enumerate(students):
            self._table.setRowHeight(row, 48)
            seat_shift = (
                f"Shift: {s['shift']}" if s["student_type"] == "Half-time"
                else (f"Seat: {s['seat_number']}" if s["seat_number"] else "No Seat")
            )
            due = s.get("next_payment_date") or ""
            days_overdue = 0
            if due:
                try:
                    due_date = date.fromisoformat(due)
                    days_overdue = (today - due_date).days
                except Exception:
                    pass

            row_data = [
                s["name"], s["phone"], s["student_type"], seat_shift,
                s.get("last_payment_date") or "–", due, str(days_overdue),
            ]
            for col, text in enumerate(row_data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                item.setForeground(QColor(DANGER))
                self._table.setItem(row, col, item)

            # Action buttons
            cell_widget = QWidget()
            cell_widget.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(cell_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(6)

            pay_btn = QPushButton("✅ Mark Paid")
            pay_btn.setObjectName("btn_success")
            pay_btn.setFixedHeight(32)
            pay_btn.clicked.connect(lambda _, sid=s["id"]: self._mark_paid(sid))

            wa_btn = QPushButton("📱 Remind")
            wa_btn.setObjectName("btn_warning")
            wa_btn.setFixedHeight(32)
            wa_btn.clicked.connect(lambda _, sid=s["id"], name=s["name"],
                                   phone=s["phone"]: self._send_reminder(name, phone))

            btn_layout.addWidget(pay_btn)
            btn_layout.addWidget(wa_btn)
            btn_layout.addStretch()
            self._table.setCellWidget(row, 7, cell_widget)

    def _mark_paid(self, student_id: int):
        student = db.get_student(student_id)
        if not student:
            return
        from ui.student_management import PaymentDialog
        dlg = PaymentDialog(student, parent=self)
        if dlg.exec_():
            self.refresh()
            self.data_changed.emit()

    def _send_reminder(self, name: str, phone: str):
        try:
            from utils.whatsapp import send_message, format_reminder_message
            tmpl = db.get_setting("whatsapp_reminder_message") or ""
            msg = format_reminder_message(tmpl, name)
            send_message(phone, msg)
            QMessageBox.information(
                self, "Reminder", f"WhatsApp reminder queued for {name}."
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not send message:\n{e}")

    def _send_all_reminders(self):
        students = db.get_overdue_students()
        if not students:
            QMessageBox.information(self, "No Overdue", "No overdue students found.")
            return
        reply = QMessageBox.question(
            self, "Send All Reminders",
            f"Send WhatsApp reminders to all {len(students)} overdue students?\n"
            "This will open WhatsApp Web for each student.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            from utils.whatsapp import send_message, format_reminder_message
            tmpl = db.get_setting("whatsapp_reminder_message") or ""
            for s in students:
                msg = format_reminder_message(tmpl, s["name"])
                send_message(s["phone"], msg)
            QMessageBox.information(
                self, "Reminders Queued",
                f"Reminders are being sent to {len(students)} students.\n"
                "Check WhatsApp Web windows."
            )
