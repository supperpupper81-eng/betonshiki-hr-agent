import sqlite3
import hashlib
import os
from datetime import datetime, timedelta

DB_PATH = os.getenv("DB_PATH", "sent_candidates.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent (
            hash TEXT PRIMARY KEY,
            title TEXT,
            contacts TEXT,
            sent_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def make_hash(title: str, contacts: str) -> str:
    raw = f"{title}|{contacts}".lower().strip()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def already_sent(title: str, contacts: str) -> bool:
    h = make_hash(title, contacts)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM sent WHERE hash = ?", (h,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def mark_as_sent(title: str, contacts: str):
    h = make_hash(title, contacts)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO sent (hash, title, contacts, sent_at) VALUES (?, ?, ?, ?)",
        (h, title[:200], contacts[:100], datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def cleanup_old(days: int = 45):
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM sent WHERE sent_at < ?", (cutoff,))
    conn.commit()
    conn.close()
