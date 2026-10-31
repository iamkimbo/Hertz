# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Lab Manual — a conversational AI agent that answers questions about an uploaded
lab manual PDF (procedures, theory, safety, calculations, pre-lab prep,
post-lab reports). Built for the Capabl Agent AI Program coursework
(Week 7 submission).

## Commands

```bash
pip install -r requirements.txt      # install dependencies

streamlit run app.py                 # run the Streamlit UI (primary front door)
uvicorn api:app --reload             # run the FastAPI backend (separate terminal, optional)
```

There is no test suite, linter, or build step in this repo.

Requires `GOOGLE_API_KEY` (a Gemini API key). Set it via a `.env` file
(copy `env.example` → `.env`) or, for `app.py`, paste it into the
password-field prompt shown when no key is found in the environment.

## Architecture

Everything routes through **`agent.py`**, which is the only file with real
logic:

1. `build_vectorstore(pdf_path)` — loads the PDF, chunks it
   (1000 chars / 200 overlap), embeds with Gemini
   (`models/embedding-001`), and returns a FAISS index.
2. Six tool factories (`make_get_procedure_tool`, `make_explain_theory_tool`,
   `make_get_safety_info_tool`, `make_calculate_tool`,
   `make_prelab_prep_tool`, `make_postlab_report_tool`) — each factory
   (except `calculate`) closes over a specific manual's vectorstore and
   does a `similarity_search` with a query rewritten for that tool's
   intent (e.g. `explain_theory` prepends "theory principle concept
   background" to the user's query before searching). `calculate` is the
   one non-retrieval tool: it evaluates arithmetic via a restricted `ast`
   walker (`_safe_eval`), never Python's `eval()`.
3. `build_agent(vectorstore)` — wires those six tools plus a Gemini
   chat model (`gemini-2.0-flash`) into a LangChain `create_agent` loop.
   This is a genuine tool-calling agent (the model decides which tools to
   call, including calling several for one question), not a fixed
   retrieve-then-answer chain — that distinction is the point of the
   project and is called out in `agent.py`'s module docstring.
4. `ask_agent(agent, question)` — runs one turn and returns the final
   message text.

**`app.py`** (Streamlit) and **`api.py`** (FastAPI) are two independent
front doors onto that same agent core — this is a deliberate architectural
choice, not an oversight:

- `app.py` imports `build_vectorstore` / `build_agent` / `ask_agent`
  directly and keeps the vectorstore + agent in `st.session_state`
  (one manual per browser session).
- `api.py` wraps the same three functions behind `/upload` and `/ask`
  HTTP endpoints, keyed by a `session_id` in an **in-memory dict**
  (`_SESSIONS`) — this resets on server restart and is not shared with
  `app.py`'s session state. CORS is wide open (`allow_origins=["*"]`) for
  coursework/demo purposes.
- **The Streamlit UI does not call the FastAPI backend over HTTP.** They
  are separate consumers of `agent.py`, run separately, and don't share
  state. Don't assume wiring between them exists — if a task asks to
  "connect the frontend to the API," that means adding real HTTP calls
  from `app.py` to `api.py`, which doesn't exist today.

## Known repo-state discrepancies

- The README documents `.streamlit/config.toml` and `.env.example`, but
  the actual files in this repo are `config.toml` and `env.example` at
  the repo root (no `.streamlit/` directory, no leading dot). Streamlit's
  theme config is only picked up from `.streamlit/config.toml`, so as
  laid out today the custom theme in `config.toml` is **not** actually
  applied when running `streamlit run app.py`.
- `requirements.txt` pins `langchain==1.3.11` / `langchain-core==1.4.8` /
  etc. — treat these pins as intentional; don't "helpfully" upgrade them
  without checking whether the pinned `create_agent` API in `agent.py`
  still matches.

## Deployment

- Frontend (`app.py`) → Streamlit Community Cloud, `GOOGLE_API_KEY` set
  as a secret.
- Backend (`api.py`) → Render, using `Procfile`
  (`uvicorn api:app --host 0.0.0.0 --port $PORT`) and `runtime.txt`
  (`python-3.12.3`); `GOOGLE_API_KEY` set as an environment variable.
  Render's free tier spins down on idle — first request after idle can
  take ~30-50s.
