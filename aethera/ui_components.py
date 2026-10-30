from __future__ import annotations

import base64
from html import escape
from pathlib import Path

import streamlit as st


ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"


def render_design_system() -> None:
    stylesheet = (ASSETS_DIR / "aethera.css").read_text(encoding="utf-8")
    backdrop = _asset_css_url("background-botanical.svg")
    sidebar = _asset_css_url("sidebar-vine.svg")
    stylesheet = stylesheet.replace(
        "var(--aethera-botanical-backdrop)", backdrop
    ).replace(
        "var(--aethera-sidebar-vine)", sidebar
    )
    st.html(f"<style>{stylesheet}</style>")


def _asset_css_url(filename: str) -> str:
    path = ASSETS_DIR / filename
    if not path.is_file():
        return "none"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f'url("data:image/svg+xml;base64,{encoded}")'


def render_empty_state(eyebrow: str, title: str, description: str) -> None:
    st.html(
        f"""
        <section class="aethera-empty-state">
          <div class="aethera-empty-eyebrow">{escape(eyebrow)}</div>
          <h3>{escape(title)}</h3>
          <p>{escape(description)}</p>
        </section>
        """
    )


def render_section_kicker(label: str) -> None:
    st.html(f'<div class="aethera-section-kicker">{escape(label)}</div>')


def render_conversation_heading(title: str, model: str) -> None:
    st.html(
        f"""
        <div class="aethera-conversation-heading">
          <div class="aethera-section-kicker">ENVIRONMENTAL INTELLIGENCE · {escape(model)}</div>
          <h2>{escape(title)}</h2>
        </div>
        """
    )


def render_page_heading(eyebrow: str, title: str, description: str) -> None:
    st.html(
        f"""
        <header class="aethera-page-heading">
          <div class="aethera-section-kicker">{escape(eyebrow)}</div>
          <h1>{escape(title)}</h1>
          <p>{escape(description)}</p>
        </header>
        """
    )
