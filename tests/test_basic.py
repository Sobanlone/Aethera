import json

import pytest

from aethera.database import import_report, init_db
from aethera.environmental_analysis import EnvironmentalAnalyzer


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_db()


def test_issue_classification_dumping():
    analyzer = EnvironmentalAnalyzer()
    result = analyzer.parse_env_issue("Someone is dumping garbage near our forest and river.")
    assert result["category"] == "illegal_dumping"
    assert "possible_impacts" in result
    assert "suggested_next_steps" in result


def test_issue_classification_deforestation():
    analyzer = EnvironmentalAnalyzer()
    result = analyzer.parse_env_issue("Several trees were cut down in the neighbourhood park.")
    assert result["category"] == "deforestation"


def test_json_validation_accepts_valid_payload():
    analyzer = EnvironmentalAnalyzer()
    payload = {
        "category": "water_pollution",
        "summary": "Water pollution observed",
        "explanation": "Plastic waste is entering the pond.",
        "follow_up_questions": ["Where is the location?"],
        "possible_impacts": ["wildlife harm"],
        "suggested_next_steps": ["Document the site"],
        "observed_facts": ["A pond is affected"],
        "unverified_info": ["Cause is unknown"],
    }
    assert analyzer.validate_json(payload)["summary"] == "Water pollution observed"


def test_invalid_json_rejected():
    analyzer = EnvironmentalAnalyzer()
    with pytest.raises(ValueError):
        analyzer.validate_json({"category": "test"})


def test_import_report_validates_required_fields():
    with pytest.raises(ValueError):
        import_report({"category": "water_pollution"})


def test_import_report_succeeds():
    report = {
        "report_id": "TEST-REPORT-001",
        "category": "water_pollution",
        "summary": "Plastic waste in river",
        "description": "Plastic bottles and bags are collecting in the river.",
        "location": "North park",
        "incident_time": "2026-10-26T10:00:00Z",
        "evidence": "Photos attached",
        "impact": "Wildlife risk",
        "missing_info": "No exact source",
        "observed_facts": "River has plastic waste",
        "unverified_info": "No official samples",
        "suggested_next_steps": "Document and report",
        "status": "draft",
        "created_at": "2026-10-26T10:00:00Z",
    }
    report_id = import_report(report)
    assert report_id == "TEST-REPORT-001"


def test_knowledge_base_matches_queries():
    from aethera.knowledge_base import EnvironmentalKnowledgeBase

    kb = EnvironmentalKnowledgeBase()
    matches = kb.retrieve("water pollution aquatic ecosystems")
    assert matches
    assert any("Water quality" in match.title for match in matches)


def test_report_json_is_loadable():
    payload = {
        "report_id": "JSON-TEST-001",
        "category": "habitat_destruction",
        "summary": "Habitat damaged",
        "description": "Several trees and nesting sites were removed.",
        "location": "Forest edge",
        "incident_time": "2026-10-25T08:30:00Z",
        "evidence": "Photos taken",
        "impact": "Habitat loss",
        "missing_info": "No owner identified",
        "observed_facts": "Trees removed",
        "unverified_info": "Cause uncertain",
        "suggested_next_steps": "Document and contact conservation office",
        "status": "draft",
        "created_at": "2026-10-25T08:30:00Z",
    }
    assert json.loads(json.dumps(payload))["summary"] == "Habitat damaged"


def test_saved_report_keeps_checklist_and_evidence_files(tmp_path, monkeypatch):
    import aethera.database as database

    monkeypatch.setattr(database, "DB_PATH", tmp_path / "reports.db")
    database.init_db()
    report = {
        "report_id": "TEST-CHECKLIST-001",
        "session_id": "system",
        "category": "water_pollution",
        "summary": "Visible waste in a stream",
        "description": "Bottles and wrappers were observed near the water.",
        "evidence_files": ["reports/TEST-CHECKLIST-001/photo.png"],
        "checklist": ["Approximate location recorded", "Photo or video evidence available"],
    }

    database.save_report(report)
    saved = database.list_reports()[0]

    assert saved["evidence_files"] == report["evidence_files"]
    assert saved["checklist"] == report["checklist"]


def test_report_image_and_pdf_exports_are_valid():
    from io import BytesIO

    from PIL import Image

    from aethera.report_exports import report_pdf, report_png

    report = {
        "report_id": "EXPORT-001",
        "category": "habitat_destruction",
        "summary": "Damaged nesting area",
        "description": "Vegetation was cleared near a nesting area.",
        "location": "North wetland",
        "checklist": ["Approximate location recorded"],
    }

    pdf = report_pdf(report)
    png = report_png(report)

    assert pdf.startswith(b"%PDF")
    with Image.open(BytesIO(png)) as image:
        assert image.format == "PNG"
        assert image.width == 1200


def test_conversation_title_is_based_on_first_prompt():
    from aethera.app import conversation_title

    assert conversation_title("  What is biodiversity?  ") == "What is biodiversity?"
    assert len(conversation_title("a very long first prompt " * 8)) <= 48


def test_empty_conversations_are_hidden_and_saved_conversations_can_be_deleted(tmp_path, monkeypatch):
    import aethera.database as database

    monkeypatch.setattr(database, "DB_PATH", tmp_path / "conversations.db")
    database.init_db()
    session_id = database.create_session("What is biodiversity?")
    assert database.list_sessions() == []

    database.save_message(session_id, "user", "What is biodiversity?")
    assert database.list_sessions()[0]["name"] == "What is biodiversity?"

    database.delete_session(session_id)
    assert database.list_sessions() == []
    assert database.list_messages(session_id) == []


def test_ollama_client_preserves_model_runner_error(monkeypatch):
    import requests

    from aethera.ollama_client import OllamaClient, OllamaError

    response = requests.Response()
    response.status_code = 500
    response.url = "http://localhost:11434/api/chat"
    response.headers["Content-Type"] = "application/json"
    response._content = b'{"error":"llama-server process has terminated"}'
    monkeypatch.setattr("aethera.ollama_client.requests.post", lambda *args, **kwargs: response)

    with pytest.raises(OllamaError, match="llama-server process has terminated"):
        OllamaClient(model="test-model").chat(
            [{"role": "user", "content": "hello"}],
            stream=False,
        )


def test_ollama_chat_streams_chunks_and_keeps_model_warm(monkeypatch):
    from aethera.config import OLLAMA_KEEP_ALIVE, OLLAMA_NUM_CTX
    from aethera.ollama_client import OllamaClient

    class FakeResponse:
        ok = True

        def iter_lines(self, chunk_size):
            assert chunk_size == 1
            yield b'{"message":{"content":"Hello"},"done":false}'
            yield b'{"message":{"content":" there"},"done":true}'

    request_args = {}

    def fake_post(*args, **kwargs):
        request_args.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr("aethera.ollama_client.requests.post", fake_post)
    received_chunks = []

    result = OllamaClient(model="test-model").chat(
        [{"role": "user", "content": "hello"}],
        stream=True,
        on_chunk=received_chunks.append,
    )

    assert result == "Hello there"
    assert received_chunks == ["Hello", " there"]
    assert request_args["stream"] is True
    assert request_args["json"]["keep_alive"] == OLLAMA_KEEP_ALIVE
    assert request_args["json"]["options"]["num_ctx"] == OLLAMA_NUM_CTX


def test_ai_response_uses_streamed_chunks_without_availability_probe(monkeypatch):
    from aethera.app import generate_ai_response
    from aethera.models import AppSettings

    class FakeClient:
        def __init__(self, model):
            self.model = model

        def chat(self, messages, temperature, max_tokens, stream, on_chunk):
            assert messages[-1] == {"role": "user", "content": "hello"}
            assert stream is True
            on_chunk("Hello")
            return "Hello"

    monkeypatch.setattr("aethera.app.OllamaClient", FakeClient)
    received_chunks = []

    result = generate_ai_response(
        "hello",
        [],
        AppSettings(model="test-model", streaming=True),
        on_chunk=received_chunks.append,
    )

    assert result == "Hello"
    assert received_chunks == ["Hello"]


def test_ollama_runner_error_explains_recovery_steps():
    from aethera.app import format_ollama_error

    error = format_ollama_error(
        "Ollama API returned HTTP 500: llama-server process has terminated: NTSTATUS 0xe06d7363"
    )

    assert "Update Ollama for Windows" in error
    assert "ollama run <model>" in error
    assert "NTSTATUS 0xe06d7363" in error


def test_custom_favicon_is_a_valid_ico():
    from pathlib import Path

    from PIL import Image

    favicon_path = Path(__file__).resolve().parents[1] / "assets" / "favicon.ico"
    with Image.open(favicon_path) as favicon:
        assert favicon.format == "ICO"
        assert (48, 48) in favicon.ico.sizes()
