import sqlite3
import os
from datetime import datetime, date
from typing import List, Optional, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Settings table
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Seats table
    c.execute("""
        CREATE TABLE IF NOT EXISTS seats (
            seat_number INTEGER PRIMARY KEY,
            is_reserved_women INTEGER NOT NULL DEFAULT 0,
            student_id INTEGER,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    # Students table
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            student_type TEXT NOT NULL CHECK(student_type IN ('Full-time','Half-time')),
            shift TEXT,
            seat_number INTEGER,
            join_date TEXT NOT NULL,
            last_payment_date TEXT,
            next_payment_date TEXT,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Payments table
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            next_payment_date TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    # Removed students table
    c.execute("""
        CREATE TABLE IF NOT EXISTS removed_students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            student_type TEXT NOT NULL,
            shift TEXT,
            seat_number INTEGER,
            join_date TEXT,
            last_payment_date TEXT,
            next_payment_date TEXT,
            notes TEXT DEFAULT '',
            removed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            removal_reason TEXT DEFAULT ''
        )
    """)

    # Insert default settings
    defaults = {
        "monthly_fee": "500",
        "total_seats": "69",
        "women_reserved_seats": "10",
        "opening_time": "06:00",
        "closing_time": "23:00",
        "morning_shift_start": "06:00",
        "morning_shift_end": "14:00",
        "evening_shift_start": "14:00",
        "evening_shift_end": "23:00",
        "whatsapp_reminder_message": (
            "Hello {name},\n\nYour study point fee is due today.\n"
            "Please pay your monthly fee to continue using your seat.\n\n"
            "नमस्ते {name},\n\nआज आपकी लाइब्रेरी फीस देय है।\n"
            "कृपया अपनी सीट जारी रखने के लिए आज भुगतान करें।"
        ),
        "whatsapp_removal_message": (
            "Hello {name},\n\nYour study point membership has ended. "
            "You are no longer registered.\n\n"
            "नमस्ते {name},\n\nआपकी लाइब्रेरी सदस्यता समाप्त हो गई है। "
            "अब आप पंजीकृत नहीं हैं।"
        ),
    }

    for key, value in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    conn.commit()

    # Initialize seats if not already done
    total = int(get_setting("total_seats") or "69")
    women_count = int(get_setting("women_reserved_seats") or "10")
    _sync_seats(c, total, women_count)

    conn.commit()
    conn.close()


def _sync_seats(c, total_seats: int, women_reserved: int):
    """Ensure seats table matches total_seats and women_reserved counts."""
    existing = c.execute("SELECT MAX(seat_number) FROM seats").fetchone()[0] or 0

    # Add missing seats
    for i in range(existing + 1, total_seats + 1):
        c.execute("INSERT OR IGNORE INTO seats (seat_number, is_reserved_women) VALUES (?, 0)", (i,))

    # Remove extra seats (only if unoccupied)
    if existing > total_seats:
        c.execute(
            "DELETE FROM seats WHERE seat_number > ? AND student_id IS NULL",
            (total_seats,)
        )

    # Update women reservation: first `women_reserved` seats get flagged
    c.execute("UPDATE seats SET is_reserved_women = 0")
    c.execute(
        "UPDATE seats SET is_reserved_women = 1 WHERE seat_number <= ?",
        (women_reserved,)
    )


# ─── Settings ────────────────────────────────────────────────────────────────

def get_setting(key: str) -> Optional[str]:
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else None


def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    if key in ("total_seats", "women_reserved_seats"):
        c = conn.cursor()
        total = int(get_setting("total_seats") or "69")
        women = int(get_setting("women_reserved_seats") or "10")
        _sync_seats(c, total, women)
        conn.commit()
    conn.close()


def get_all_settings() -> Dict[str, str]:
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


# ─── Seats ───────────────────────────────────────────────────────────────────

def get_all_seats() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.seat_number, s.is_reserved_women, s.student_id,
               st.name as student_name, st.student_type
        FROM seats s
        LEFT JOIN students st ON s.student_id = st.id
        ORDER BY s.seat_number
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def assign_seat(seat_number: int, student_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE seats SET student_id = ? WHERE seat_number = ?",
        (student_id, seat_number)
    )
    conn.execute(
        "UPDATE students SET seat_number = ? WHERE id = ?",
        (seat_number, student_id)
    )
    conn.commit()
    conn.close()


def free_seat(seat_number: int):
    conn = get_connection()
    conn.execute("UPDATE seats SET student_id = NULL WHERE seat_number = ?", (seat_number,))
    conn.commit()
    conn.close()


def get_available_seats() -> List[int]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT seat_number FROM seats WHERE student_id IS NULL ORDER BY seat_number"
    ).fetchall()
    conn.close()
    return [r["seat_number"] for r in rows]


# ─── Students ────────────────────────────────────────────────────────────────

def add_student(data: Dict[str, Any]) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO students
            (name, phone, student_type, shift, seat_number, join_date,
             last_payment_date, next_payment_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"], data["phone"], data["student_type"],
        data.get("shift"), data.get("seat_number"),
        data["join_date"], data.get("last_payment_date"),
        data.get("next_payment_date"), data.get("notes", "")
    ))
    student_id = c.lastrowid
    if data.get("seat_number") and data["student_type"] == "Full-time":
        c.execute(
            "UPDATE seats SET student_id = ? WHERE seat_number = ?",
            (student_id, data["seat_number"])
        )
    conn.commit()
    conn.close()
    return student_id


def update_student(student_id: int, data: Dict[str, Any]):
    conn = get_connection()
    old = conn.execute("SELECT seat_number FROM students WHERE id = ?", (student_id,)).fetchone()
    if old and old["seat_number"] and old["seat_number"] != data.get("seat_number"):
        conn.execute("UPDATE seats SET student_id = NULL WHERE seat_number = ?", (old["seat_number"],))

    conn.execute("""
        UPDATE students SET
            name = ?, phone = ?, student_type = ?, shift = ?,
            seat_number = ?, join_date = ?, last_payment_date = ?,
            next_payment_date = ?, notes = ?
        WHERE id = ?
    """, (
        data["name"], data["phone"], data["student_type"],
        data.get("shift"), data.get("seat_number"),
        data["join_date"], data.get("last_payment_date"),
        data.get("next_payment_date"), data.get("notes", ""),
        student_id
    ))
    if data.get("seat_number") and data["student_type"] == "Full-time":
        conn.execute(
            "UPDATE seats SET student_id = ? WHERE seat_number = ?",
            (student_id, data["seat_number"])
        )
    conn.commit()
    conn.close()


def remove_student(student_id: int, reason: str = "") -> Optional[str]:
    """Archive student, free seat, and return phone number."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if not row:
        conn.close()
        return None
    conn.execute("""
        INSERT INTO removed_students
            (original_id, name, phone, student_type, shift, seat_number,
             join_date, last_payment_date, next_payment_date, notes, removal_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_id, row["name"], row["phone"], row["student_type"],
        row["shift"], row["seat_number"], row["join_date"],
        row["last_payment_date"], row["next_payment_date"],
        row["notes"], reason
    ))
    if row["seat_number"]:
        conn.execute("UPDATE seats SET student_id = NULL WHERE seat_number = ?", (row["seat_number"],))
    conn.execute("DELETE FROM payments WHERE student_id = ?", (student_id,))
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    phone = row["phone"]
    conn.commit()
    conn.close()
    return phone


def get_all_students(search: str = "") -> List[Dict]:
    conn = get_connection()
    if search:
        like = f"%{search}%"
        rows = conn.execute("""
            SELECT * FROM students
            WHERE name LIKE ? OR phone LIKE ? OR CAST(seat_number AS TEXT) LIKE ?
            ORDER BY name
        """, (like, like, like)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student(student_id: int) -> Optional[Dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_overdue_students() -> List[Dict]:
    today = date.today().isoformat()
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM students
        WHERE next_payment_date IS NOT NULL AND next_payment_date <= ?
        ORDER BY next_payment_date
    """, (today,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_due_today_students() -> List[Dict]:
    today = date.today().isoformat()
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM students
        WHERE next_payment_date = ?
    """, (today,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Payments ────────────────────────────────────────────────────────────────

def record_payment(student_id: int, amount: float, payment_date: str,
                   next_date: str, note: str = ""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO payments (student_id, amount, payment_date, next_payment_date, note)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, amount, payment_date, next_date, note))
    conn.execute("""
        UPDATE students SET last_payment_date = ?, next_payment_date = ?
        WHERE id = ?
    """, (payment_date, next_date, student_id))
    conn.commit()
    conn.close()


def get_payment_history(student_id: int) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM payments WHERE student_id = ?
        ORDER BY payment_date DESC
    """, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_payment(payment_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
    conn.commit()
    conn.close()


# ─── Removed Students ────────────────────────────────────────────────────────

def get_removed_students(search: str = "") -> List[Dict]:
    conn = get_connection()
    if search:
        like = f"%{search}%"
        rows = conn.execute("""
            SELECT * FROM removed_students
            WHERE name LIKE ? OR phone LIKE ?
            ORDER BY removed_at DESC
        """, (like, like)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM removed_students ORDER BY removed_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_removed_student_record(record_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM removed_students WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


# ─── Dashboard Stats ─────────────────────────────────────────────────────────

def get_dashboard_stats() -> Dict[str, Any]:
    conn = get_connection()
    total_seats = int(conn.execute("SELECT COUNT(*) FROM seats").fetchone()[0])
    occupied = int(conn.execute("SELECT COUNT(*) FROM seats WHERE student_id IS NOT NULL").fetchone()[0])
    reserved = int(conn.execute("SELECT COUNT(*) FROM seats WHERE is_reserved_women = 1").fetchone()[0])
    available = total_seats - occupied
    fulltime_count = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE student_type = 'Full-time'"
    ).fetchone()[0])
    halftime_count = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE student_type = 'Half-time'"
    ).fetchone()[0])
    today = date.today().isoformat()
    due_today = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE next_payment_date = ?", (today,)
    ).fetchone()[0])
    overdue = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE next_payment_date < ?", (today,)
    ).fetchone()[0])
    conn.close()
    return {
        "total_seats": total_seats,
        "occupied_seats": occupied,
        "available_seats": available,
        "reserved_seats": reserved,
        "fulltime_students": fulltime_count,
        "halftime_students": halftime_count,
        "due_today": due_today,
        "overdue": overdue,
    }


# ─── Export ──────────────────────────────────────────────────────────────────

def export_students_data() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]
