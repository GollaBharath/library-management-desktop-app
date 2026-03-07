"""Dashboard panel – summary statistics and quick info."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
import database as db
from styles import (
    BG_CARD, BG_PANEL, ACCENT, ACCENT2, SUCCESS, WARNING, DANGER,
    INFO, PURPLE, TEXT_PRIMARY, TEXT_SECONDARY, BG_HOVER
)


class StatCard(QFrame):
    def __init__(self, label: str, value: str, color: str = ACCENT,
                 icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 22))
        icon_lbl.setStyleSheet(f"color: {color}; background: transparent;")
        top.addWidget(icon_lbl)
        top.addStretch()
        layout.addLayout(top)

        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("card_value")
        self.value_lbl.setStyleSheet(
            f"font-size: 30px; font-weight: bold; color: {color}; background: transparent;"
        )
        layout.addWidget(self.value_lbl)

        self.label_lbl = QLabel(label)
        self.label_lbl.setObjectName("card_label")
        self.label_lbl.setStyleSheet(
            f"font-size: 12px; color: {TEXT_SECONDARY}; background: transparent;"
        )
        layout.addWidget(self.label_lbl)

        self.setStyleSheet(
            f"QFrame#card {{ background-color: {BG_CARD}; border: 1px solid #2A2A4A; "
            f"border-radius: 12px; border-left: 4px solid {color}; }}"
        )

    def update_value(self, value: str):
        self.value_lbl.setText(value)


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._refresh()
        # Auto-refresh every 60 seconds
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(60_000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = QLabel("📊 Dashboard")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {TEXT_PRIMARY}; background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()
        date_lbl = QLabel()
        from datetime import date
        date_lbl.setText(date.today().strftime("%A, %d %B %Y"))
        date_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        header.addWidget(date_lbl)
        root.addLayout(header)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: #2A2A4A;")
        root.addWidget(line)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(content)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(20)

        # ── Seats section ──
        seats_lbl = QLabel("SEATS OVERVIEW")
        seats_lbl.setStyleSheet(
            f"font-size: 11px; letter-spacing: 2px; color: {TEXT_SECONDARY}; "
            f"font-weight: bold; background: transparent;"
        )
        vbox.addWidget(seats_lbl)

        seats_grid = QGridLayout()
        seats_grid.setSpacing(14)

        self.card_total    = StatCard("Total Seats",     "–", ACCENT,   "🪑")
        self.card_occupied = StatCard("Occupied Seats",  "–", DANGER,   "🔴")
        self.card_available= StatCard("Available Seats", "–", SUCCESS,  "🟢")
        self.card_reserved = StatCard("Women Reserved",  "–", PURPLE,   "💜")

        seats_grid.addWidget(self.card_total,     0, 0)
        seats_grid.addWidget(self.card_occupied,  0, 1)
        seats_grid.addWidget(self.card_available, 0, 2)
        seats_grid.addWidget(self.card_reserved,  0, 3)
        vbox.addLayout(seats_grid)

        # ── Students section ──
        students_lbl = QLabel("STUDENTS OVERVIEW")
        students_lbl.setStyleSheet(
            f"font-size: 11px; letter-spacing: 2px; color: {TEXT_SECONDARY}; "
            f"font-weight: bold; background: transparent;"
        )
        vbox.addWidget(students_lbl)

        students_grid = QGridLayout()
        students_grid.setSpacing(14)

        self.card_fulltime  = StatCard("Full-time Students",  "–", INFO,    "📚")
        self.card_halftime  = StatCard("Half-time Students",  "–", ACCENT2, "⏰")
        self.card_due_today = StatCard("Fees Due Today",      "–", WARNING, "💰")
        self.card_overdue   = StatCard("Overdue Payments",    "–", DANGER,  "⚠️")

        students_grid.addWidget(self.card_fulltime,  0, 0)
        students_grid.addWidget(self.card_halftime,  0, 1)
        students_grid.addWidget(self.card_due_today, 0, 2)
        students_grid.addWidget(self.card_overdue,   0, 3)
        vbox.addLayout(students_grid)

        vbox.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def _refresh(self):
        stats = db.get_dashboard_stats()
        self.card_total.update_value(str(stats["total_seats"]))
        self.card_occupied.update_value(str(stats["occupied_seats"]))
        self.card_available.update_value(str(stats["available_seats"]))
        self.card_reserved.update_value(str(stats["reserved_seats"]))
        self.card_fulltime.update_value(str(stats["fulltime_students"]))
        self.card_halftime.update_value(str(stats["halftime_students"]))
        self.card_due_today.update_value(str(stats["due_today"]))
        self.card_overdue.update_value(str(stats["overdue"]))

    def refresh(self):
        self._refresh()
