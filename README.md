# Study Point – Library Management System

A full-featured **desktop application** for managing a private study room/library.  
Built with **Python + PyQt5 + SQLite**.

---

## Features

| Module                 | Description                                                  |
| ---------------------- | ------------------------------------------------------------ |
| **Dashboard**          | Live stats: seats, students, due fees, overdue count         |
| **Seat Layout**        | Visual 69-seat grid — color-coded Green/Red/Purple           |
| **Student Management** | Add / Edit / Remove students; full + half-time types         |
| **Payment Management** | Record fees, auto-generate next due date, view history       |
| **Overdue Fees**       | Auto-detected overdue list, bulk WhatsApp reminders          |
| **Removed Students**   | Archived records with removal timestamp                      |
| **Settings**           | Fee amount, seats, timings, WhatsApp messages — all editable |

---

## Prerequisites

- Python 3.9+
- Linux / Windows / macOS desktop

---

## Installation

```bash
# 1. Clone / enter the project folder
cd library-management-desktop-app

# 2. Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py
```

---

## Dependencies

| Package           | Purpose                              |
| ----------------- | ------------------------------------ |
| `PyQt5`           | Desktop GUI framework                |
| `openpyxl`        | Excel export                         |
| `pywhatkit`       | WhatsApp Web automation              |
| `pandas`          | Optional data helpers                |
| `python-dateutil` | Accurate month-based date arithmetic |

> **Note:** `pywhatkit` opens **WhatsApp Web** in your browser to send messages.  
> Make sure WhatsApp Web is logged in before sending reminders.

---

## Project Structure

```
library-management-desktop-app/
├── main.py                  # Application entry point
├── database.py              # SQLite ORM helpers
├── styles.py                # Dark theme stylesheet
├── requirements.txt
├── library.db               # Auto-created on first run
├── ui/
│   ├── dashboard.py
│   ├── seat_layout.py
│   ├── student_management.py
│   ├── payment_management.py
│   ├── overdue_payments.py
│   ├── removed_students.py
│   └── settings_panel.py
└── utils/
    ├── whatsapp.py
    └── export.py
```

---

## Student Types

| Type          | Seat                | Entry Hours        | Shift              |
| ------------- | ------------------- | ------------------ | ------------------ |
| **Full-time** | Fixed assigned seat | 6:00 AM – 11:00 PM | —                  |
| **Half-time** | No fixed seat       | Shift hours only   | Morning or Evening |

---

## Seat Color Codes

| Color     | Meaning            |
| --------- | ------------------ |
| 🟢 Green  | Available          |
| 🔴 Red    | Occupied           |
| 🟣 Purple | Reserved for Women |

---

## Payment Logic

- When a student pays on **2 March** → next due date = **2 April**
- Overdue section auto-populates for all students past due date
- WhatsApp reminders fire automatically on due date (hourly check)

---

## Data Backup & Export

Go to **Settings** → scroll to _Data Backup & Export_:

- **Backup Database** — saves a timestamped `.db` file
- **Export Excel** — exports all students to `.xlsx`
- **Export CSV** — exports all students to `.csv`

---

## WhatsApp Reminders

Reminders use `pywhatkit` which opens WhatsApp Web.  
You can fully customize the message text in **Settings**.

Default placeholders:

- `{name}` — replaced with the student's name

---

## License

MIT — free to use and modify.
