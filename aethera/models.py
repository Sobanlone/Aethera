from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field

from aethera.config import DEFAULT_CONTEXT_WINDOW, DEFAULT_MAX_TOKENS, DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT, DEFAULT_TEMPERATURE


class AnalysisResult(BaseModel):
    category: str
    confidence: float
    summary: str
    explanation: str
    follow_up_questions: List[str] = Field(default_factory=list)
    possible_impacts: List[str] = Field(default_factory=list)
    suggested_next_steps: List[str] = Field(default_factory=list)
    observed_facts: List[str] = Field(default_factory=list)
    unverified_info: List[str] = Field(default_factory=list)


class IncidentReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"AETH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    category: str = "general_environmental_concern"
    summary: str = ""
    description: str = ""
    location: str = ""
    incident_time: str = ""
    evidence: str = ""
    impact: str = ""
    missing_info: str = ""
    observed_facts: str = ""
    unverified_info: str = ""
    suggested_next_steps: str = ""
    status: str = "draft"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AppSettings(BaseModel):
    model: str = DEFAULT_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    context_window: int = DEFAULT_CONTEXT_WINDOW
    streaming: bool = True
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
