# FOR_RITURAJ.md

An engaging, plain-language tour of this project so future-you (and teammates) can jump back in fast.

## 1) Elevator pitch (what this is)
An end-to-end, LLM-assisted pipeline that turns raw requirements into Gherkin feature files, verifies them, and generates Java automation scripts (API or UI) with iterative chat-based refinement.

## 2) Architecture story (how it flows)
- **Streamlit UI (`app.py`/`app_v2.py`)**: Orchestrates the experience—configures LLM provider, captures requirements, shows generated artifacts, and hosts chat-based refinement for both feature files and scripts.
- **Agents (`agents/`)**:
  - `RequirementAgent`: turns requirements into feature JSON (API/UI variants) and supports chat refinements.
  - `VerificationAgent`: reviews the feature for gaps and consistency.
  - `AutomationScriptAgent`: converts feature JSON to per-scenario script JSON, then to Java, supports merge + chat refinements.
- **Features layer (`features/`)**: parsing/merging helpers (e.g., indentation-safe merges).
- **Utils (`utils/gherkin_json_utils.py`, `utils/java_json_utils.py`, `utils/llm_config.py`)**: conversions (Gherkin ↔ JSON IR), Java/JSON helpers, and LLM wiring.
- **API layer (`api/`)**: Models/routes for serving outputs (if hosted as a service).
- **Docs (`docs/`)**: design notes, refactoring guides, indentation handling, hybrid workflow, etc.
- **Tests (`tests/`)**: coverage for parsing/merging/refinement behaviors.

## 3) Folder-by-folder quick tour
- `app.py`, `app_v2.py`, `run.py`, `main.py`: Streamlit entry points.
- `agents/`: Core orchestration logic per stage (requirements → verification → scripts → refinements).
- `features/`: Parser/merger utilities (handles tricky whitespace/indentation).
- `utils/`: Gherkin/JSON and Java/JSON conversions, LLM config helpers.
- `api/`: FastAPI-style layer (models/routes) for service mode.
- `docs/`: Internal design/implementation readmes.
- `tests/`: Regression tests for parsing/merging/refinement logic.
- `uploads/`, `outputs/`: Runtime artifacts.

## 4) Key decisions & trade-offs
- **JSON IR for scripts**: Chosen for deterministic, safe edits vs. direct string surgery on Java. Trade-off: extra conversion layer, but refinements are predictable.
- **Streamlit UI first**: Fast iteration and demo-friendly; less control over advanced layouts vs. custom frontend.
- **Agent separation**: Requirement/Verification/Automation split keeps concerns clear; slightly more wiring overhead.
- **Dual providers (Groq/Azure OpenAI)**: Flexibility + fallbacks; adds config surface and validation paths.

## 5) Bugs we hit & how we fixed them (representative)
- **Undefined key guards**: Cleared invalid API keys in error paths; avoided referencing undefined `key_source`.
- **Indentation-sensitive merges**: Added indentation-safe merge logic to avoid malformed Java when stitching scenarios.
- **Diff accuracy**: Improved unified diff views for feature/script refinements to reduce user confusion.
- **Fallback paths**: Hardened JSON IR → Java conversions when legacy string-based merge is used.

## 6) Pitfalls to watch for
- **Session state resets**: When rerunning Streamlit after config changes, ensure session flags are reset (feature/script versions, chat state).
- **API key validity**: Validate and clear bad keys; avoid stale session values on cloud vs. local.
- **Gherkin parsing**: Input validation—non-Gherkin text can slip through; warn early.
- **Large prompts**: Long requirements or chat history can bloat prompt size; consider summarizing.

## 7) Lessons & best practices
- Keep a **JSON IR** between LLM output and code generation for safe deterministic edits.
- Show users **diffs** before applying changes—build trust and catch surprises.
- Reset state deliberately on key user actions (new generation, accept/reject, start over).
- Keep **providers pluggable** (Groq/Azure); surface clear config/status in UI.
- Write small, focused tests for parsing/merging to catch regressions early.

## 8) Quickstart / how to run (local)
```bash
# from repo root
pip install -r requirements.txt
streamlit run app.py --server.port 8504
```

## 9) Changelog (add entries as you go)
- 2026-01-27: Added this FOR_RITURAJ.md starter.
