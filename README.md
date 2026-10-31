# Lab Manual Conversational Assistant

**Capabl Agent AI Program — Week 7 Submission**
**Team:** Rakim & Saif

> Note on numbering: the coordinator's checklist for this stage was
> labeled "Week 6," but our internal count already had a Week 6 submission
> (API + sidebar) done. Content-wise (beautify, finish/test API, deploy)
> this is our Week 7 build — noted here so it's not confusing later.

## This week's checkpoints

- ✅ **Beautified frontend** — custom theme (`.streamlit/config.toml`),
  header with branding, status indicator once a manual is loaded, styled
  empty state, chat avatars. All native Streamlit — no fragile custom CSS
  framework to maintain.
- ✅ **APIs finished** — added CORS middleware to `api.py` so the frontend
  can call it cross-origin if deployed separately. All three endpoints
  (`/health`, `/upload`, `/ask`) re-verified working end-to-end against a
  real Gemini key, including error paths (bad file type, empty file,
  unknown session).
- ✅ **Config bugs fixed** — the theme file and env template had landed at
  the repo root instead of `.streamlit/config.toml` / `.env.example`, so
  Streamlit's theme wasn't actually being picked up and `.env` was never
  loaded by any of the three files. Both fixed; confirmed by running the
  app, not just reading the code.
- ✅ **Model names updated** — `models/embedding-001` and `gemini-2.0-flash`
  had been retired by Google since this project started; both calls were
  404ing. Swapped to the current `models/gemini-embedding-001` and
  `gemini-3.6-flash`, verified against a live API key.
- ✅ **Seventh tool added: `pubchem_safety_lookup`** — calls PubChem's
  public GHS hazard-classification API directly for any named chemical,
  independent of the manual. Verified the agent calls it dynamically
  alongside `get_safety_info` when a question needs both the manual's
  precautions and real-world regulatory hazard data.
- ⚠️ **Analytics dashboard — not built.** This was the other stretch goal
  for this stage. Given the time available, priority went to verifying the
  seven-tool agent and both deployments actually work end-to-end rather
  than adding a dashboard half-finished. Listed under Known limitations.
- ⚠️ **Frontend/API integration** — see "Architecture note" below. This
  was a deliberate choice, not skipped work.
- ✅ **Deployment config added** — `Procfile` and `runtime.txt` for
  deploying `api.py` on Render; Streamlit Cloud deployment steps below
  for `app.py`.

## Architecture note: why the frontend and API are independent

`app.py` (Streamlit) and `api.py` (FastAPI) are **two separate front
doors to the same agent** in `agent.py` — the Streamlit app does not call
the FastAPI backend over HTTP; it imports the agent functions directly.

This was a deliberate choice given the timeline: it's lower-risk (fewer
moving parts to break during a live demo) and both are independently
provable as working. The tradeoff is that they're not "integrated" in the
literal network-call sense. If asked in the viva: the API exists so
Lab Manual's agent can be used by *other* tools/services outside Streamlit
(e.g. a future mobile app, or another team's system) — not because the
Streamlit UI depends on it.

## Files

- `agent.py` — vector store setup + all seven tools + agent construction
- `app.py` — Streamlit chat UI (themed, polished)
- `api.py` — FastAPI backend with CORS enabled
- `.streamlit/config.toml` — custom theme
- `requirements.txt` — pinned dependencies
- `.env.example` — template for your Gemini API key
- `Procfile`, `runtime.txt` — deployment config for Render (API)

## Setup

```bash
pip install -r requirements.txt
```
Set `GOOGLE_API_KEY` via `.env` (copy from `.env.example`) or paste it
into the app's password field when it launches.

```bash
streamlit run app.py          # UI
uvicorn api:app --reload      # API (separate terminal, optional)
```

## Deployment

### Frontend (Streamlit Cloud — free)
1. Push this repo to GitHub (all files, including `.streamlit/config.toml`).
2. Go to https://share.streamlit.io → connect the repo → set `app.py` as
   the entry point.
3. Settings → Secrets → add `GOOGLE_API_KEY = "your_key_here"`.
4. Deploy. You'll get a public `*.streamlit.app` URL.

### Backend API (Render — free tier)
1. Go to https://render.com → New → Web Service → connect this repo.
2. Render auto-detects the `Procfile`. Environment: Python 3.
3. Add environment variable `GOOGLE_API_KEY` in Render's dashboard.
4. Deploy. You'll get a public `*.onrender.com` URL.
5. Note: Render's free tier spins down after inactivity — the first
   request after idle time can take ~30-50 seconds to wake up. Mention
   this if demoing live so it doesn't look broken.

## Known limitations

- **No analytics dashboard.** Planned as a stretch goal for this stage but
  not built — prioritized verifying the core agent and both deployments
  over adding this half-finished. Candidate for Week 8.
- `/upload` sessions are in-memory in `api.py` — lost on server restart.
- `calculate` only accepts plain numeric expressions, no units/variables.
- Experiment identification is semantic-search based, not a strict
  "Experiment N" parser.
- Frontend and API are independent (see architecture note above), not
  wired together over HTTP.
- `pubchem_safety_lookup` depends on PubChem's public API being reachable
  and on the chemical being findable by name — misspellings, formulas
  (e.g. "NaOH"), or very obscure compounds may not resolve. It fails
  gracefully with a message rather than crashing when that happens.
- The default model (`gemini-3.6-flash`) is on Gemini's free tier, which
  caps at **20 requests/day per model**. Each question the agent answers
  uses 1 of those. Don't burn through them rehearsing right before a live
  demo — pace test runs, or switch to a paid tier/plan on your Google AI
  Studio account if you need more headroom.

## Next (Week 8 / final)

Final polish, thorough testing on real GTU manuals, README/demo video,
final PPT and presentation prep.
