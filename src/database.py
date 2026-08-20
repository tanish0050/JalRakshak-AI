"""SQLite storage helpers for citizen reports."""
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import uuid4

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "data" / "jalrakshak.db"


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialise_database():
    with get_connection() as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS reports (
            report_id TEXT PRIMARY KEY, name TEXT NOT NULL, location TEXT NOT NULL,
            issue TEXT NOT NULL, contact TEXT, description TEXT, latitude REAL,
            longitude REAL, photo_path TEXT, status TEXT NOT NULL DEFAULT 'New',
            created_at TEXT NOT NULL)""")


def create_report(name, location, issue, contact, description, latitude, longitude, photo_path, source=None, village=None, block=None, district=None):
    report_id = f"JR-{datetime.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
    with get_connection() as connection:
        connection.execute("""INSERT INTO reports
            (report_id, name, location, issue, contact, description, latitude, longitude, photo_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
            report_id, name.strip(), location.strip(), issue, contact.strip(), description.strip(), latitude,
            longitude, photo_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))
    return report_id


def get_reports():
    initialise_database()
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM reports ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


def update_status(report_id, status):
    with get_connection() as connection:
        connection.execute("UPDATE reports SET status = ? WHERE report_id = ?", (status, report_id))
