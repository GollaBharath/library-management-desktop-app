"""Student management: list, add, edit, remove, search."""
from datetime import date, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QTextEdit, QDateEdit, QMessageBox,
    QHeaderView, QAbstractItemView, QFrame, QSplitter,
    QScrollArea, QGroupBox, QSpinBox
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import database as db
from styles import (
    TEXT_PRIMARY, TEXT_SECONDARY, BG_CARD, BG_PANEL, ACCENT,
    SUCCESS, DANGER, WARNING, INFO, PURPLE, BG_HOVER
)


def _date_str(d: date) -> str:
    return d.isoformat() if d else ""


def _qdate(s: str) -> QDate:
    if s:
        try:
            parts = s.split("-")
            return QDate(int(parts[0]), int(parts[1]), int(parts[2]))
        except Exception:
            pass
    return QDate.currentDate()


class StudentDialog(QDialog):
    """Add / Edit student dialog."""
    def __init__(self, student_data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Student" if not student_data else "Edit Student")
        self.setMinimumWidth(500)
        self.setMinimumHeight(580)
        self._data = student_data or {}
        self._result_data = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        form = QFormLayout(inner)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        # Name
        self._name = QLineEdit(self._data.get("name", ""))
        self._name.setPlaceholderText("Full name")
        form.addRow("Name *", self._name)

        # Phone
        self._phone = QLineEdit(self._data.get("phone", ""))
        self._phone.setPlaceholderText("+91 XXXXXXXXXX")
        form.addRow("Phone *", self._phone)

        # Type
        self._type = QComboBox()
        self._type.addItems(["Full-time", "Half-time"])
        idx = 0 if self._data.get("student_type", "Full-time") == "Full-time" else 1
        self._type.setCurrentIndex(idx)
        self._type.currentIndexChanged.connect(self._on_type_change)
        form.addRow("Type *", self._type)

        # Shift (half-time)
        self._shift = QComboBox()
        self._shift.addItems(["Morning (6AM–2PM)", "Evening (2PM–11PM)"])
        if self._data.get("shift") and "Evening" in self._data.get("shift", ""):
            self._shift.setCurrentIndex(1)
        form.addRow("Shift", self._shift)

        # Seat (full-time)
        self._seat_row_label = QLabel("Seat Number")
        avail = db.get_available_seats()
        cur_seat = self._data.get("seat_number")
        if cur_seat and cur_seat not in avail:
            avail.insert(0, cur_seat)
        self._seat = QComboBox()
        self._seat.addItem("— None —", None)
        for sn in avail:
            self._seat.addItem(str(sn), sn)
        if cur_seat:
            for i in range(self._seat.count()):
                if self._seat.itemData(i) == cur_seat:
                    self._seat.setCurrentIndex(i)
                    break
        form.addRow("Seat Number", self._seat)

        # Join date
        self._join = QDateEdit()
        self._join.setCalendarPopup(True)
        self._join.setDisplayFormat("dd MMM yyyy")
        self._join.setDate(_qdate(self._data.get("join_date", _date_str(date.today()))))
        form.addRow("Join Date *", self._join)

        # Last payment
        self._last_pay = QDateEdit()
        self._last_pay.setCalendarPopup(True)
        self._last_pay.setDisplayFormat("dd MMM yyyy")
        lp = self._data.get("last_payment_date") or _date_str(date.today())
        self._last_pay.setDate(_qdate(lp))
        self._last_pay.dateChanged.connect(self._update_next_payment)
        form.addRow("Last Payment", self._last_pay)

        # Next payment
        self._next_pay = QDateEdit()
        self._next_pay.setCalendarPopup(True)
        self._next_pay.setDisplayFormat("dd MMM yyyy")
        np_str = self._data.get("next_payment_date")
        if np_str:
            self._next_pay.setDate(_qdate(np_str))
        else:
            self._update_next_payment()
        form.addRow("Next Payment", self._next_pay)

        # Notes
        self._notes = QTextEdit(self._data.get("notes", ""))
        self._notes.setPlaceholderText("Optional notes…")
        self._notes.setFixedHeight(70)
        form.addRow("Notes", self._notes)

        scroll.setWidget(inner)
        layout.addWidget(scroll)

        # Buttons
        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.setObjectName("btn_success")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self._on_type_change()

    def _on_type_change(self):
        is_full = self._type.currentText() == "Full-time"
        self._shift.setEnabled(not is_full)
        self._seat.setEnabled(is_full)

    def _update_next_payment(self):
        lp = self._last_pay.date().toPyDate()
        from dateutil.relativedelta import relativedelta
        try:
            np = lp + relativedelta(months=1)
        except ImportError:
            # Fallback: add 30 days
            np = lp + timedelta(days=30)
        self._next_pay.setDate(QDate(np.year, np.month, np.day))

    def _save(self):
        name = self._name.text().strip()
        phone = self._phone.text().strip()
        if not name or not phone:
            QMessageBox.warning(self, "Validation", "Name and Phone are required.")
            return
        stype = self._type.currentText()
        shift = None
        seat = None
        if stype == "Half-time":
            shift = "Morning" if self._shift.currentIndex() == 0 else "Evening"
        else:
            seat = self._seat.currentData()

        self._result_data = {
            "name": name,
            "phone": phone,
            "student_type": stype,
            "shift": shift,
            "seat_number": seat,
            "join_date": self._join.date().toPyDate().isoformat(),
            "last_payment_date": self._last_pay.date().toPyDate().isoformat(),
            "next_payment_date": self._next_pay.date().toPyDate().isoformat(),
            "notes": self._notes.toPlainText().strip(),
        }
        self.accept()

    def get_data(self):
        return self._result_data


class StudentManagementWidget(QWidget):
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
        title = QLabel("👥 Student Management")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {TEXT_PRIMARY}; background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("➕ Add Student")
        add_btn.setObjectName("btn_primary")
        add_btn.clicked.connect(self._add_student)
        header.addWidget(add_btn)
        root.addLayout(header)

        # Search bar
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search by name, phone, or seat number…")
        self._search.textChanged.connect(self.refresh)
        search_row.addWidget(self._search)

        filter_lbl = QLabel("Type:")
        filter_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        self._filter = QComboBox()
        self._filter.addItems(["All", "Full-time", "Half-time"])
        self._filter.currentIndexChanged.connect(self.refresh)
        search_row.addWidget(filter_lbl)
        search_row.addWidget(self._filter)
        root.addLayout(search_row)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels([
            "ID", "Name", "Phone", "Type", "Shift/Seat",
            "Join Date", "Last Paid", "Next Due", "Actions"
        ])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setColumnWidth(0, 40)
        self._table.setColumnWidth(3, 90)
        self._table.setColumnWidth(4, 110)
        self._table.setColumnWidth(5, 100)
        self._table.setColumnWidth(6, 100)
        self._table.setColumnWidth(7, 100)
        self._table.setColumnWidth(8, 180)
        root.addWidget(self._table)

    def refresh(self):
        search = self._search.text().strip() if hasattr(self, "_search") else ""
        students = db.get_all_students(search)
        ftype = self._filter.currentText() if hasattr(self, "_filter") else "All"
        if ftype != "All":
            students = [s for s in students if s["student_type"] == ftype]

        self._table.setRowCount(len(students))
        today = date.today().isoformat()

        for row, s in enumerate(students):
            self._table.setRowHeight(row, 44)

            items = [
                str(s["id"]),
                s["name"],
                s["phone"],
                s["student_type"],
                (f"Shift: {s['shift']}" if s["student_type"] == "Half-time"
                 else (f"Seat: {s['seat_number']}" if s["seat_number"] else "No Seat")),
                s.get("join_date", ""),
                s.get("last_payment_date") or "–",
                s.get("next_payment_date") or "–",
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

                # Color overdue
                if col == 7 and s.get("next_payment_date"):
                    if s["next_payment_date"] < today:
                        item.setForeground(QColor(DANGER))
                    elif s["next_payment_date"] == today:
                        item.setForeground(QColor(WARNING))

                self._table.setItem(row, col, item)

            # Action buttons cell
            cell_widget = QWidget()
            cell_widget.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(cell_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(6)

            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Edit student")
            edit_btn.setFixedSize(32, 32)
            edit_btn.setStyleSheet(
                f"background-color: {BG_HOVER}; border-radius: 6px; color: white;"
                f"QPushButton:hover {{ background-color: {INFO}; }}"
            )
            edit_btn.clicked.connect(lambda _, sid=s["id"]: self._edit_student(sid))

            pay_btn = QPushButton("💰")
            pay_btn.setToolTip("Record payment")
            pay_btn.setFixedSize(32, 32)
            pay_btn.setStyleSheet(
                f"background-color: {BG_HOVER}; border-radius: 6px; color: white;"
            )
            pay_btn.clicked.connect(lambda _, sid=s["id"]: self._record_payment(sid))

            del_btn = QPushButton("🗑️")
            del_btn.setToolTip("Remove student")
            del_btn.setFixedSize(32, 32)
            del_btn.setStyleSheet(
                f"background-color: {BG_HOVER}; border-radius: 6px; color: white;"
            )
            del_btn.clicked.connect(lambda _, sid=s["id"]: self._remove_student(sid))

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(pay_btn)
            btn_layout.addWidget(del_btn)
            btn_layout.addStretch()

            self._table.setCellWidget(row, 8, cell_widget)

    def _add_student(self):
        dlg = StudentDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            if data:
                db.add_student(data)
                self.refresh()
                self.data_changed.emit()

    def _edit_student(self, student_id: int):
        student = db.get_student(student_id)
        if not student:
            return
        dlg = StudentDialog(student_data=student, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            if data:
                db.update_student(student_id, data)
                self.refresh()
                self.data_changed.emit()

    def _record_payment(self, student_id: int):
        student = db.get_student(student_id)
        if not student:
            return
        dlg = PaymentDialog(student, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh()
            self.data_changed.emit()

    def _remove_student(self, student_id: int):
        student = db.get_student(student_id)
        if not student:
            return
        reply = QMessageBox.question(
            self, "Remove Student",
            f"Remove {student['name']} from the system?\n\n"
            "Their record will be archived and a WhatsApp message will be sent.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            phone = db.remove_student(student_id)
            if phone:
                try:
                    from utils.whatsapp import send_message, format_removal_message
                    msg_tmpl = db.get_setting("whatsapp_removal_message") or ""
                    msg = format_removal_message(msg_tmpl, student["name"])
                    send_message(phone, msg)
                    QMessageBox.information(
                        self, "Removed",
                        f"{student['name']} has been removed.\nWhatsApp removal message queued."
                    )
                except Exception:
                    QMessageBox.information(
                        self, "Removed",
                        f"{student['name']} has been removed."
                    )
            self.refresh()
            self.data_changed.emit()


class PaymentDialog(QDialog):
    def __init__(self, student: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Record Payment – {student['name']}")
        self.setMinimumWidth(400)
        self._student = student
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        info = QLabel(
            f"<b>{self._student['name']}</b>  |  {self._student['phone']}<br>"
            f"Type: {self._student['student_type']}"
        )
        info.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)

        fee = float(db.get_setting("monthly_fee") or "500")
        self._amount = QLineEdit(str(fee))
        self._amount.setPlaceholderText("Amount")
        form.addRow("Amount (₹)", self._amount)

        self._pay_date = QDateEdit()
        self._pay_date.setCalendarPopup(True)
        self._pay_date.setDisplayFormat("dd MMM yyyy")
        self._pay_date.setDate(QDate.currentDate())
        self._pay_date.dateChanged.connect(self._update_next)
        form.addRow("Payment Date", self._pay_date)

        self._next_date = QDateEdit()
        self._next_date.setCalendarPopup(True)
        self._next_date.setDisplayFormat("dd MMM yyyy")
        form.addRow("Next Due Date", self._next_date)
        self._update_next()

        self._note = QLineEdit()
        self._note.setPlaceholderText("Optional note")
        form.addRow("Note", self._note)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("✅ Confirm Payment")
        save_btn.setObjectName("btn_success")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _update_next(self):
        pd = self._pay_date.date().toPyDate()
        try:
            from dateutil.relativedelta import relativedelta
            nd = pd + relativedelta(months=1)
        except ImportError:
            nd = pd + timedelta(days=30)
        self._next_date.setDate(QDate(nd.year, nd.month, nd.day))

    def _save(self):
        try:
            amount = float(self._amount.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid", "Enter a valid amount.")
            return
        pay_date = self._pay_date.date().toPyDate().isoformat()
        next_date = self._next_date.date().toPyDate().isoformat()
        note = self._note.text().strip()
        db.record_payment(self._student["id"], amount, pay_date, next_date, note)
        self.accept()
