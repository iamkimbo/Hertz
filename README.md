# Hertz — Lab Manual Conversational Assistant

**Capabl Agent AI Program — Week 6 Submission**
**Team:** Rakim & Saif

## This week's checkpoints

- ✅ **Completed workflows** — all six agent tools (procedure, theory,
  safety, calculate, pre-lab prep, post-lab report) are wired into the
  agent and verified working end-to-end against a mock manual.
- ✅ **Working API endpoints** — added `api.py`, a small FastAPI layer
  exposing the same agent via real HTTP endpoints (`/upload`, `/ask`,
  `/health`), independent of the Streamlit UI. All three tested and
  confirmed working (see "API testing" below).
- ✅ **Started interactive UI/UX** — added a sidebar with a capability
  list and clickable example questions that populate the chat directly,
  on top of the existing upload + chat flow.

## What this is

Hertz is an AI assistant that lets students upload lab manuals and ask
questions about experiments instead of flipping through pages. It's a
genuine tool-calling agent: the AI decides for itself which tool(s) to
call based on the question, rather than following one fixed hardcoded path.

## What's new this week

Week 5 begins the **Domain Specialization** phase (Week 5-6), using Track
A **Option A2: Comprehensive Experiment Guide** — extending Hertz across
the full experiment lifecycle instead of just the procedure itself.

Two new tools:

- **`prelab_prep`** *(new)* — what to prepare, bring, and know before
  starting an experiment (apparatus, materials, prerequisite concepts)
- **`postlab_report_help`** *(new)* — what observations, results, and
  conclusion format belong in the lab report/record for an experiment

Combined with the four tools from Weeks 2-4, Hertz now has **six tools**
covering before, during, and after a lab session:

| Stage | Tool |
|---|---|
| Before lab | `prelab_prep` |
| During lab | `get_procedure`, `explain_theory`, `get_safety_info`, `calculate` |
| After lab | `postlab_report_help` |

## Why this counts as an agent, not "just code"

The LLM decides which tool(s) a question needs — including combining
several in one answer (e.g. "what do I need to prepare for Experiment 3,
and what should I write in my report afterward?" triggers both
`prelab_prep` and `postlab_report_help`). This is not a hardcoded
if/else router; it's LangChain's `create_agent` reasoning loop.

## Files

- `agent.py` — vector store setup + all six tools + agent construction
- `app.py` — Streamlit chat UI wired to the agent (with sidebar + example questions)
- `api.py` — FastAPI backend exposing the agent as HTTP endpoints
- `requirements.txt` — pinned dependencies (tested versions)
- `.env.example` — template for your Gemini API key

## API endpoints

Run the API separately from the Streamlit UI:
```bash
uvicorn api:app --reload
```

- `GET /health` — health check, returns `{"status": "ok"}`
- `POST /upload` — upload a lab manual PDF (multipart form, field name `file`), returns a `session_id`
- `POST /ask` — body `{"session_id": "...", "question": "..."}`, returns `{"answer": "..."}`

Full interactive docs are auto-generated at `/docs` once the server is running.

### API testing done

- `/health` returns 200 with the expected payload.
- `/ask` correctly returns 404 with a clear error for an unknown `session_id`
  instead of crashing.
- `/upload` correctly rejects non-PDF files (400) and empty files (400)
  before attempting to process them.
- Full `/upload` → `/ask` round trip with a real PDF requires a live Gemini
  API key and hasn't been run in this environment — test this first with
  your key before the demo.

## Setup

1. Get a free Gemini API key: https://aistudio.google.com/app/apikey
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your API key (copy `.env.example` to `.env`, or paste it into the
   app's password field when it launches).
4. Run locally:
   ```bash
   streamlit run app.py
   ```
5. Try a full-lifecycle question, e.g. "What should I prepare before
   Experiment 3, and what should I note down for the lab report?"

## Deployment (Streamlit Cloud)

1. Push this repo to GitHub.
2. Go to https://share.streamlit.io and connect the repo.
3. Set `app.py` as the entry point.
4. In Settings -> Secrets, add:
   ```
   GOOGLE_API_KEY = "your_key_here"
   ```
5. Deploy.

## Known limitations

- `calculate` only accepts plain numeric expressions — no units or
  variable names; the LLM is expected to resolve those to numbers first.
- Experiment identification is semantic-search based, not a strict
  "Experiment N" parser.
- No persistent storage yet — re-uploading is required each session.
- `postlab_report_help` and `prelab_prep` quality depends on how
  explicitly the source manual documents apparatus lists and
  observation/result sections — sparse manuals will return less.

## Next (Week 6)

Finish Option A2: add lab report **generation assistance with templates**,
study material/revision note generation from experiments, and basic
progress tracking across experiments — closing the Week 5-6 milestone.
