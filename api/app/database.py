import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.getenv("DATABASE_URL", "sqlite:////tmp/munai.db").replace("sqlite:////", "/").replace("sqlite:///", "")

# Ensure directory exists
db_dir = os.path.dirname(DB_PATH)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'operator',
                position TEXT DEFAULT '',
                region TEXT DEFAULT '',
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS wells (
                id TEXT PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                product TEXT DEFAULT 'oil',
                production24h REAL DEFAULT 0,
                temperature REAL DEFAULT 0,
                tubing_internal_p REAL DEFAULT 0,
                tubing_external_p REAL DEFAULT 0,
                annulus_p REAL DEFAULT 0,
                pump_strokes INTEGER DEFAULT 0,
                lat REAL DEFAULT 50.0,
                lng REAL DEFAULT 55.0,
                operator_id TEXT,
                manager_id TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                well_id TEXT NOT NULL,
                operator_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                ai_score INTEGER DEFAULT 0,
                summary TEXT DEFAULT '',
                flag TEXT,
                temperature REAL,
                production24h REAL,
                tubing_internal_p REAL,
                tubing_external_p REAL,
                annulus_p REAL,
                pump_strokes INTEGER,
                comment TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                reviewed_at TEXT,
                reviewed_by TEXT
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                icon TEXT DEFAULT 'info',
                title TEXT NOT NULL,
                body TEXT DEFAULT '',
                tone TEXT DEFAULT 'info',
                unread INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS calendar_events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                event_type TEXT DEFAULT 'Событие',
                created_by TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                who TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.commit()
    finally:
        conn.close()
