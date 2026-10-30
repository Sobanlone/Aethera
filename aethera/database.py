from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from aethera.config import DB_PATH, DEFAULT_CONTEXT_WINDOW, DEFAULT_MAX_TOKENS, DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT, DEFAULT_TEMPERATURE


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            user_id TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            user_id TEXT,
            category TEXT NOT NULL,
            summary TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT,
            incident_time TEXT,
            evidence TEXT,
            impact TEXT,
            missing_info TEXT,
            observed_facts TEXT,
            unverified_info TEXT,
            suggested_next_steps TEXT,
            evidence_files TEXT NOT NULL DEFAULT '[]',
            checklist TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
        """
    )
    report_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(reports)").fetchall()
    }
    if "evidence_files" not in report_columns:
        conn.execute(
            "ALTER TABLE reports ADD COLUMN evidence_files TEXT NOT NULL DEFAULT '[]'"
        )
    if "checklist" not in report_columns:
        conn.execute(
            "ALTER TABLE reports ADD COLUMN checklist TEXT NOT NULL DEFAULT '[]'"
        )
    if "user_id" not in report_columns:
        conn.execute("ALTER TABLE reports ADD COLUMN user_id TEXT")
    session_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(sessions)").fetchall()
    }
    if "user_id" not in session_columns:
        conn.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL DEFAULT '',
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    default_settings = {
        "model": DEFAULT_MODEL,
        "temperature": str(DEFAULT_TEMPERATURE),
        "max_tokens": str(DEFAULT_MAX_TOKENS),
        "context_window": str(DEFAULT_CONTEXT_WINDOW),
        "streaming": "true",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
    }
    for key, value in default_settings.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )

    conn.commit()
    conn.close()


def list_sessions(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    query = """
        SELECT s.id, s.name, s.created_at, s.updated_at
        FROM sessions s
        WHERE EXISTS (
            SELECT 1 FROM messages m WHERE m.session_id = s.id
        )
    """
    params: List[Any] = []
    if user_id:
        query += " AND s.user_id = ?"
        params.append(user_id)
    query += " ORDER BY s.updated_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_session(name: Optional[str] = None, user_id: Optional[str] = None) -> str:
    import uuid

    session_id = str(uuid.uuid4())
    created = utc_now()
    session_name = name or f"Conversation {len(list_sessions(user_id)) + 1}"
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (id, name, created_at, updated_at, user_id) VALUES (?, ?, ?, ?, ?)",
        (session_id, session_name, created, created, user_id),
    )
    conn.commit()
    conn.close()
    return session_id


def rename_session(session_id: str, new_name: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE sessions SET name = ?, updated_at = ? WHERE id = ?",
        (new_name.strip() or "Untitled conversation", utc_now(), session_id),
    )
    conn.commit()
    conn.close()


def delete_session(session_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM reports WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def save_message(session_id: str, role: str, content: str) -> None:
    import uuid

    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), session_id, role, content, utc_now()),
    )
    conn.execute(
        "UPDATE sessions SET updated_at = ? WHERE id = ?",
        (utc_now(), session_id),
    )
    conn.commit()
    conn.close()


def list_messages(session_id: str) -> List[Dict[str, str]]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_session_name(session_id: str) -> str:
    conn = get_connection()
    row = conn.execute("SELECT name FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return row["name"] if row else "Conversation"


def get_setting(key: str, default: str = "") -> str:
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def list_reports(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    query = "SELECT * FROM reports"
    params: List[Any] = []
    if user_id:
        query += " WHERE user_id = ?"
        params.append(user_id)
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    reports = [dict(row) for row in rows]
    for report in reports:
        for field in ("evidence_files", "checklist"):
            try:
                report[field] = json.loads(report.get(field) or "[]")
            except json.JSONDecodeError:
                report[field] = []
    return reports


def save_report(report: Dict[str, Any], user_id: Optional[str] = None) -> str:
    report_id = report["report_id"]
    owner_user_id = user_id or report.get("user_id") or "system"
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO reports (
            id, session_id, user_id, category, summary, description, location, incident_time,
            evidence, impact, missing_info, observed_facts, unverified_info,
            suggested_next_steps, evidence_files, checklist, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            session_id = excluded.session_id,
            user_id = excluded.user_id,
            category = excluded.category,
            summary = excluded.summary,
            description = excluded.description,
            location = excluded.location,
            incident_time = excluded.incident_time,
            evidence = excluded.evidence,
            impact = excluded.impact,
            missing_info = excluded.missing_info,
            observed_facts = excluded.observed_facts,
            unverified_info = excluded.unverified_info,
            suggested_next_steps = excluded.suggested_next_steps,
            evidence_files = excluded.evidence_files,
            checklist = excluded.checklist,
            status = excluded.status,
            created_at = excluded.created_at
        """,
        (
            report_id,
            report.get("session_id", "system"),
            owner_user_id,
            report.get("category", "general_environmental_concern"),
            report.get("summary", ""),
            report.get("description", ""),
            report.get("location", ""),
            report.get("incident_time", ""),
            report.get("evidence", ""),
            report.get("impact", ""),
            report.get("missing_info", ""),
            report.get("observed_facts", ""),
            report.get("unverified_info", ""),
            report.get("suggested_next_steps", ""),
            json.dumps(report.get("evidence_files", [])),
            json.dumps(report.get("checklist", [])),
            report.get("status", "draft"),
            report.get("created_at", utc_now()),
        ),
    )
    conn.commit()
    conn.close()
    return report_id


def export_conversation(session_id: str) -> str:
    messages = list_messages(session_id)
    session_name = get_session_name(session_id)
    payload = {
        "session_id": session_id,
        "session_name": session_name,
        "messages": messages,
    }
    return json.dumps(payload, indent=2)


def import_report(report_payload: Dict[str, Any], session_id: str = "system") -> str:
    required = ["category", "summary", "description"]
    for field in required:
        if not report_payload.get(field):
            raise ValueError(f"Missing required report field: {field}")

    report = {
        "report_id": report_payload.get("report_id") or f"AETH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "session_id": session_id,
        "category": report_payload.get("category", "general_environmental_concern"),
        "summary": report_payload.get("summary", ""),
        "description": report_payload.get("description", ""),
        "location": report_payload.get("location", ""),
        "incident_time": report_payload.get("incident_time", ""),
        "evidence": report_payload.get("evidence", ""),
        "impact": report_payload.get("impact", ""),
        "missing_info": report_payload.get("missing_info", ""),
        "observed_facts": report_payload.get("observed_facts", ""),
        "unverified_info": report_payload.get("unverified_info", ""),
        "suggested_next_steps": report_payload.get("suggested_next_steps", ""),
        "evidence_files": report_payload.get("evidence_files", []),
        "checklist": report_payload.get("checklist", []),
        "status": report_payload.get("status", "draft"),
        "created_at": report_payload.get("created_at", utc_now()),
    }
    return save_report(report)


def get_recent_reports(limit: int = 10, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    query = "SELECT * FROM reports"
    params: List[Any] = []
    if user_id:
        query += " WHERE user_id = ?"
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    if user_id:
        params.insert(0, user_id)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    reports = [dict(row) for row in rows]
    for report in reports:
        for field in ("evidence_files", "checklist"):
            try:
                report[field] = json.loads(report.get(field) or "[]")
            except json.JSONDecodeError:
                report[field] = []
    return reports
