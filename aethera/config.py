from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = Path(os.environ.get("AETHERA_DB_PATH", str(DATA_DIR / "aethera.db")))
DEFAULT_MODEL = os.environ.get("AETHERA_MODEL", "llama3.2:3b")
DEFAULT_TEMPERATURE = float(os.environ.get("AETHERA_TEMPERATURE", "0.7"))
DEFAULT_MAX_TOKENS = int(os.environ.get("AETHERA_MAX_TOKENS", "256"))
DEFAULT_CONTEXT_WINDOW = int(os.environ.get("AETHERA_CONTEXT_WINDOW", "12"))
OLLAMA_NUM_CTX = int(os.environ.get("OLLAMA_NUM_CTX", "2048"))
OLLAMA_KEEP_ALIVE = os.environ.get("OLLAMA_KEEP_ALIVE", "30m")

DEFAULT_SYSTEM_PROMPT = """You are Aethera, a helpful environmental AI assistant.

Goals:
- Answer environmental questions clearly and practically.
- Distinguish verified facts from uncertain conclusions.
- Recommend safe next steps and professional help when needed.
- Do not invent evidence, legal conclusions, or scientific claims.
- If the user describes an environmental problem, help analyse it and produce a structured report.

When information is uncertain, say so explicitly.
"""
