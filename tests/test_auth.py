import re

import pytest

from aethera.auth import (
    authenticate_user,
    create_user,
    get_user_by_id,
    get_user_by_username,
    hash_password,
    suggest_username_variations,
    verify_password,
)
from aethera.database import create_session, init_db, list_reports, list_sessions, save_message, save_report


def test_password_hashing_is_salted_and_verifiable():
    salt_a = "a" * 32
    salt_b = "b" * 32
    password_hash_a = hash_password("secret123", salt_a)
    password_hash_b = hash_password("secret123", salt_b)

    assert password_hash_a != password_hash_b
    assert verify_password("secret123", salt_a, password_hash_a)
    assert verify_password("secret123", salt_b, password_hash_b)
    assert not verify_password("wrong-password", salt_a, password_hash_a)


def test_suggest_username_variations_returns_unique_new_names():
    suggestions = suggest_username_variations("John")

    assert len(suggestions) == 3
    assert len(set(suggestions)) == 3
    assert all(candidate.startswith("john") for candidate in suggestions)
    assert all(candidate != "john" for candidate in suggestions)
    assert all(re.fullmatch(r"john[a-z0-9]+", candidate) for candidate in suggestions)


def test_create_user_stores_salted_hash_and_rejects_bad_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr("aethera.database.DB_PATH", tmp_path / "auth_users.db")
    init_db()

    user = create_user("soban", "secret123", "Soban")

    stored = get_user_by_username("soban")
    assert stored is not None
    assert stored["display_name"] == "Soban"
    assert stored["salt"]
    assert stored["password_hash"] != "secret123"
    assert verify_password("secret123", stored["salt"], stored["password_hash"])
    assert authenticate_user("soban", "secret123") is not None
    assert authenticate_user("soban", "incorrect-password") is None
    assert authenticate_user("unknown-user", "secret123") is None
    assert get_user_by_id(user["id"]) is not None


def test_create_user_rejects_duplicate_username_and_invalid_input(tmp_path, monkeypatch):
    monkeypatch.setattr("aethera.database.DB_PATH", tmp_path / "auth_users.db")
    init_db()

    create_user("reused-name", "secret123")

    with pytest.raises(ValueError):
        create_user("reused-name", "secret123")
    with pytest.raises(ValueError):
        create_user("   ", "secret123")
    with pytest.raises(ValueError):
        create_user("shorty", "123")


def test_each_user_only_sees_their_own_conversations_and_reports(tmp_path, monkeypatch):
    monkeypatch.setattr("aethera.database.DB_PATH", tmp_path / "auth_isolation.db")
    init_db()

    user_a = create_user("user-a", "secret123")
    user_b = create_user("user-b", "secret123")

    session_a = create_session("User A chat", user_a["id"])
    session_b = create_session("User B chat", user_b["id"])
    save_message(session_a, "user", "hello from user A")
    save_message(session_b, "user", "hello from user B")
    save_report(
        {
            "report_id": "REPORT-A-001",
            "session_id": session_a,
            "category": "water_pollution",
            "summary": "User A report",
            "description": "User A observed waste.",
        },
        user_a["id"],
    )

    assert [session["id"] for session in list_sessions(user_a["id"])] == [session_a]
    assert [session["id"] for session in list_sessions(user_b["id"])] == [session_b]
    assert [report["id"] for report in list_reports(user_a["id"])] == ["REPORT-A-001"]
    assert list_reports(user_b["id"]) == []
