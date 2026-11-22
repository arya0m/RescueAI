"""
RescueAI SQLite Storage Engine
Manages operational triage statuses, prediction audit history, and analyst feedback.
"""

import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

DB_PATH_DEFAULT = os.path.join("data", "rescueai.db")


def get_db_connection(db_path: str = DB_PATH_DEFAULT) -> sqlite3.Connection:
    """Returns a SQLite connection with dict-like row factories."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH_DEFAULT) -> None:
    """Initializes tables for triage status, inference history, and analyst feedback."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS triage_status (
                tweet_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                clean_text TEXT NOT NULL,
                predicted_label INTEGER NOT NULL,
                predicted_category TEXT NOT NULL,
                confidence REAL NOT NULL,
                urgency TEXT NOT NULL,
                is_low_confidence INTEGER NOT NULL,
                runner_up_category TEXT,
                runner_up_confidence REAL,
                lat REAL,
                lon REAL,
                is_user INTEGER DEFAULT 0,
                event_name TEXT
            )
        """)
        
        # Ensure migration columns exist on existing databases
        cursor.execute("PRAGMA table_info(history)")
        cols = [col[1] for col in cursor.fetchall()]
        if "lat" not in cols:
            cursor.execute("ALTER TABLE history ADD COLUMN lat REAL")
        if "lon" not in cols:
            cursor.execute("ALTER TABLE history ADD COLUMN lon REAL")
        if "is_user" not in cols:
            cursor.execute("ALTER TABLE history ADD COLUMN is_user INTEGER DEFAULT 0")
        if "event_name" not in cols:
            cursor.execute("ALTER TABLE history ADD COLUMN event_name TEXT")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                tweet_id TEXT,
                raw_text TEXT NOT NULL,
                predicted_label INTEGER NOT NULL,
                is_correct INTEGER NOT NULL,
                user_label INTEGER,
                notes TEXT
            )
        """)
        
        # Indices for efficient filtering
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_created_at ON history(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_is_user ON history(is_user)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_predicted_label ON history(predicted_label)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_triage_status ON triage_status(status)")
        
        conn.commit()


def set_triage_status(tweet_id: str, status: str, db_path: str = DB_PATH_DEFAULT) -> Dict[str, str]:
    """Updates or sets operational triage status for a tweet."""
    allowed = {"unreviewed", "reviewed", "flagged", "irrelevant"}
    if status not in allowed:
        raise ValueError(f"Invalid status '{status}'. Must be one of {allowed}")
    
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO triage_status (tweet_id, status, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(tweet_id) DO UPDATE SET
                status = excluded.status,
                updated_at = excluded.updated_at
        """, (tweet_id, status, now_iso))
        conn.commit()
    
    return {"tweet_id": tweet_id, "status": status, "updated_at": now_iso}


def get_all_triage_statuses(db_path: str = DB_PATH_DEFAULT) -> Dict[str, str]:
    """Returns mapping of tweet_id -> status."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT tweet_id, status FROM triage_status")
        rows = cursor.fetchall()
        return {r["tweet_id"]: r["status"] for r in rows}


def add_history_entry(
    raw_text: str,
    clean_text: str,
    predicted_label: int,
    predicted_category: str,
    confidence: float,
    urgency: str,
    is_low_confidence: bool,
    runner_up_category: Optional[str] = None,
    runner_up_confidence: Optional[float] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    is_user: bool = False,
    event_name: Optional[str] = None,
    db_path: str = DB_PATH_DEFAULT
) -> int:
    """Records an inference prediction into the history audit table."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO history (
                created_at, raw_text, clean_text, predicted_label,
                predicted_category, confidence, urgency, is_low_confidence,
                runner_up_category, runner_up_confidence,
                lat, lon, is_user, event_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now_iso, raw_text, clean_text, predicted_label,
            predicted_category, float(confidence), urgency, int(is_low_confidence),
            runner_up_category, runner_up_confidence,
            lat, lon, int(is_user), event_name
        ))
        conn.commit()
        return cursor.lastrowid


def get_user_messages(db_path: str = DB_PATH_DEFAULT) -> List[Dict[str, Any]]:
    """Returns all user-submitted messages from SQLite."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM history WHERE is_user = 1 ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_user_pins(db_path: str = DB_PATH_DEFAULT) -> List[Dict[str, Any]]:
    """Returns all user-submitted pins with valid coordinates."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM history
            WHERE lat IS NOT NULL AND lon IS NOT NULL
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_history_entries(
    category: Optional[str] = None,
    low_conf_only: Optional[bool] = None,
    q: Optional[str] = None,
    page: int = 1,
    size: int = 50,
    db_path: str = DB_PATH_DEFAULT
) -> Tuple[List[Dict[str, Any]], int]:
    """Retrieves paginated history audit entries."""
    query = "SELECT * FROM history WHERE 1=1"
    params: List[Any] = []
    
    if category:
        query += " AND predicted_category = ?"
        params.append(category)
        
    if low_conf_only:
        query += " AND is_low_confidence = 1"
        
    if q:
        query += " AND raw_text LIKE ?"
        params.append(f"%{q}%")
        
    count_query = f"SELECT COUNT(*) as count FROM ({query})"
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(count_query, params)
        total = cursor.fetchone()["count"]
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([size, (page - 1) * size])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        items = [dict(r) for r in rows]
        
    return items, total


def clear_history_entries(db_path: str = DB_PATH_DEFAULT) -> int:
    """Deletes all prediction history entries."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history")
        deleted = cursor.rowcount
        conn.commit()
        return deleted


def add_feedback_entry(
    raw_text: str,
    predicted_label: int,
    is_correct: bool,
    tweet_id: Optional[str] = None,
    user_label: Optional[int] = None,
    notes: Optional[str] = None,
    db_path: str = DB_PATH_DEFAULT
) -> int:
    """Stores analyst ground-truth feedback."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO feedback (
                created_at, tweet_id, raw_text, predicted_label,
                is_correct, user_label, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            now_iso, tweet_id, raw_text, predicted_label,
            int(is_correct), user_label, notes
        ))
        conn.commit()
        return cursor.lastrowid


def get_feedback_summary(db_path: str = DB_PATH_DEFAULT) -> Dict[str, Any]:
    """Computes analyst agreement stats."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total, SUM(is_correct) as correct FROM feedback")
        row = cursor.fetchone()
        total = row["total"] or 0
        correct = row["correct"] or 0
        
        overall_share = float(correct / total) if total > 0 else 0.0
        
        # Per-class breakdown
        cursor.execute("""
            SELECT predicted_label, COUNT(*) as class_total, SUM(is_correct) as class_correct
            FROM feedback GROUP BY predicted_label
        """)
        class_rows = cursor.fetchall()
        by_class = {}
        for cr in class_rows:
            ct = cr["class_total"]
            cc = cr["class_correct"] or 0
            by_class[int(cr["predicted_label"])] = {
                "total": ct,
                "correct": cc,
                "share": float(cc / ct) if ct > 0 else 0.0
            }
            
    return {
        "total_feedback": total,
        "correct_feedback": correct,
        "agreement_rate": round(overall_share, 4),
        "by_class": by_class
    }
