from __future__ import annotations

import hashlib
import hmac
import random
import re
import string
import uuid
from typing import Any, Dict, List, Optional, Set

from aethera import database as db


MIN_PASSWORD_LENGTH = 6
PBKDF2_ITERATIONS = 600_000


def suggest_username_variations(base_username: str, limit: int = 3) -> List[str]:
    base = re.sub(r"[^a-z0-9_]", "", (base_username or "").strip().lower())
    if not base:
        return []
    suggestions: List[str] = []
    seen: Set[str] = set()
    attempts = 0
    while len(suggestions) < limit and attempts < 100:
        attempts += 1
        pattern = attempts % 3
        if pattern == 0:
            candidate = f"{base}{random.choice(string.ascii_lowercase)}"
        elif pattern == 1:
            candidate = f"{base}{random.randint(10, 999)}"
        else:
            candidate = f"{base}{random.choice(string.ascii_lowercase) * 2}"
        if candidate in seen or candidate == base:
            continue
        seen.add(candidate)
        suggestions.append(candidate)
    return suggestions


def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or uuid.uuid4().hex
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    candidate_hash = hash_password(password, salt)
    return hmac.compare_digest(candidate_hash, password_hash)


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = db.get_connection()
    row = conn.execute(
        """
        SELECT id, username, display_name, salt, password_hash, created_at
        FROM users
        WHERE username = ?
        """,
        (username.strip().lower(),),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    conn = db.get_connection()
    row = conn.execute(
        """
        SELECT id, username, display_name, salt, password_hash, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(username: str, password: str, display_name: str = "") -> Dict[str, Any]:
    normalized_username = username.strip().lower()
    if not normalized_username:
        raise ValueError("Username is required.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError("Password must be at least 6 characters long.")
    if get_user_by_username(normalized_username) is not None:
        raise ValueError("That username is already taken. Please choose another.")

    salt = uuid.uuid4().hex
    user_id = str(uuid.uuid4())
    created = db.utc_now()
    conn = db.get_connection()
    conn.execute(
        """
        INSERT INTO users (id, username, display_name, salt, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, normalized_username, display_name.strip(), salt, hash_password(password, salt), created),
    )
    conn.commit()
    conn.close()
    return get_user_by_id(user_id) or {
        "id": user_id,
        "username": normalized_username,
        "display_name": display_name.strip(),
        "salt": salt,
        "password_hash": hash_password(password, salt),
        "created_at": created,
    }


def update_user_password(user_id: str, new_password: str) -> None:
    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValueError("Password must be at least 6 characters long.")
    conn = db.get_connection()
    conn.execute(
        "UPDATE users SET salt = ?, password_hash = ? WHERE id = ?",
        (uuid.uuid4().hex, hash_password(new_password), user_id),
    )
    conn.commit()
    conn.close()


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_username(username)
    if user is None:
        return None
    if not verify_password(password, user["salt"], user["password_hash"]):
        return None
    return user
