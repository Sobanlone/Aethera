from __future__ import annotations

import json
import os
from typing import Callable, Dict, List, Optional

import requests

from aethera.config import (
    DEFAULT_MODEL,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_TEMPERATURE,
    OLLAMA_KEEP_ALIVE,
    OLLAMA_NUM_CTX,
)


class OllamaError(RuntimeError):
    """Raised when Ollama returns an unsuccessful API response."""


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None, timeout: int = 30):
        self.base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.environ.get("AETHERA_MODEL", DEFAULT_MODEL)
        self.timeout = timeout

    def list_models(self) -> List[str]:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            models = []
            for item in payload.get("models", []):
                names = item.get("name") or item.get("model")
                if names:
                    models.append(names)
            return sorted(set(models))
        except (requests.RequestException, ValueError):
            return []

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def generate(self, prompt: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT, temperature: float = DEFAULT_TEMPERATURE, max_tokens: int = 512, stream: bool = False) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": stream,
            "keep_alive": OLLAMA_KEEP_ALIVE,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": OLLAMA_NUM_CTX,
            },
        }
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout * 2,
            stream=stream,
        )
        self._raise_for_error(response)
        if stream:
            text_parts: List[str] = []
            for line in response.iter_lines(chunk_size=1):
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if chunk.get("response"):
                    text_parts.append(chunk["response"])
            return "".join(text_parts)
        data = response.json()
        return data.get("response", "")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = 512,
        stream: bool = False,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "keep_alive": OLLAMA_KEEP_ALIVE,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": OLLAMA_NUM_CTX,
            },
        }
        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout * 2,
            stream=stream,
        )
        self._raise_for_error(response)
        if stream:
            text_parts: List[str] = []
            for line in response.iter_lines(chunk_size=1):
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                content = chunk.get("message", {}).get("content")
                if content:
                    text_parts.append(content)
                    if on_chunk:
                        on_chunk(content)
            return "".join(text_parts)
        data = response.json()
        return data.get("message", {}).get("content", "")

    @staticmethod
    def _raise_for_error(response: requests.Response) -> None:
        if response.ok:
            return
        try:
            detail = response.json().get("error", response.text)
        except ValueError:
            detail = response.text
        raise OllamaError(f"Ollama API returned HTTP {response.status_code}: {detail}")
