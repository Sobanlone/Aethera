# Aethera

Aethera is an AI-powered environmental assistance chatbot designed for SDG 15 (Life on Land). It provides general environmental guidance, issue analysis, guided incident reporting, and a local, privacy-conscious workflow built around Ollama and SQLite.

The Streamlit interface uses a dark black-and-forest-green theme configured in `.streamlit/config.toml`.
Shared interface tokens and responsive component styling are maintained in `assets/aethera.css` and `aethera/ui_components.py`.
The chat uses a small animated flower-and-leaf indicator while a local AI response is being generated; it respects the browser's reduced-motion preference.
The backdrop uses original local SVG plant illustrations, softly blended into the main canvas and sidebar so the decoration works offline without stock-photo dependencies.
The browser tab uses the supplied `assets/favicon.ico` icon.

## Ollama troubleshooting

Open **Settings** and select **Test selected Ollama model** to check local inference. If Aethera reports that the model runner crashed, test the model in PowerShell with `ollama run <model> "Reply with hello"`. If the CLI test also fails, Ollama itself is crashing before Aethera can receive a response.

On systems where Ollama's GPU runner crashes, the documented CPU AVX2 backend can be selected with the user environment variable `OLLAMA_LLM_LIBRARY=cpu_avx2`. Fully quit and reopen Ollama after setting it. CPU inference is slower than a working GPU backend; update the graphics driver and retest GPU inference before removing the override.

## Features

- Conversational environmental AI assistant
- Environmental problem analysis and follow-up questions
- Guided incident reporting and editable drafts
- Local knowledge base for environmental guidance
- Persistent multi-session chat history with SQLite
- Conversations are created only after the first message and named from that prompt
- Select, rename, export, and delete saved conversations
- Dashboard with Plotly charts
- AI-assisted report drafting with a rule-based offline analysis option
- Photo evidence uploads and a documentation checklist for reports
- Local image evidence uploads capped at 8 MB per file
- JSON, PDF, and PNG report exports
- Local AI processing using Ollama
- Local account sign-in and sign-up with salted password hashing

## Installation

1. Create a virtual environment:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
2. Install dependencies:
   - `python -m pip install -r requirements.txt`
3. Ensure Ollama is installed and running locally.
4. Check available models:
   - `ollama list`
5. Run the app:
   - Double-click `run_aethera.bat` to install dependencies if needed and launch Aethera in your browser.
   - Or run `python -m aethera` from the project directory; Streamlit opens the browser automatically.

## Local AI configuration

Aethera streams chat output as Ollama generates it and keeps the model loaded for 30 minutes between requests by default. A 2,048-token context and 256-token response limit are the defaults for new installations; the response limit can be adjusted in Settings. You can tune these defaults with environment variables:

- `AETHERA_MODEL`
- `AETHERA_TEMPERATURE`
- `AETHERA_MAX_TOKENS`
- `AETHERA_CONTEXT_WINDOW`
- `OLLAMA_BASE_URL`
- `OLLAMA_NUM_CTX` (default: `2048`)
- `OLLAMA_KEEP_ALIVE` (default: `30m`; set to `0` to unload immediately)

For lower latency on CPU-only systems, use a smaller quantized Ollama model and keep the model on the CPU AVX2 backend if that backend is stable on your device. A compatible GPU backend is typically faster.

## Privacy

Aethera keeps conversations and saved reports in a local SQLite database. The app prioritises local inference via Ollama and does not claim to be fully offline if external services are used.

## Accounts

Aethera includes a local account system for shared use of a single device:

- Open the account screen to **sign in** with an existing username and password, or choose **Create account** to register a new local account.
- Passwords are salted and hashed with PBKDF2-SHA256 (600,000 iterations, using Python's standard library) before being stored in the local SQLite database; plaintext passwords are never saved.
- Usernames are stored lowercase and must be unique per device, so the same person cannot create a second account. New passwords must be at least 6 characters long.
- After signing in, the workspace opens on a fresh conversation; use **Sign out** from the sidebar to return to the account screen.
- Conversations and saved reports are stored per user, so each account only sees its own data. All data stays in the local SQLite database on the device.

## Project structure

- `aethera/app.py` — Streamlit interface and navigation
- `aethera/ui_components.py` — shared page headings, empty states, and design-system loading
- `assets/aethera.css` — shared responsive Aethera design tokens and component styling
- `aethera/database.py` — SQLite storage and persistence
- `aethera/auth.py` — local account creation, sign-in, and password verification
- `aethera/ollama_client.py` — local Ollama interaction
- `aethera/environmental_analysis.py` — issue classification and follow-up logic
- `aethera/knowledge_base.py` — curated environmental knowledge entries
- `tests/` — automated tests and validation scenarios

## Known limitations

- The app uses a curated local knowledge base rather than a full external retrieval system.
- The environmental classifier is heuristic and uses user text patterns; it is designed for demonstration and local analysis rather than regulatory/forensic conclusions.
- Real AI output depends on the availability of a locally installed Ollama model.

## Hackathon demo flow

1. Open the app.
2. Ask a general environmental question.
3. Describe an incident.
4. Review the structured analysis and missing-information prompts.
5. Save and export a report.
6. Open the dashboard to see the saved report summary.
