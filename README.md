# Hertz — Lab Manual Conversational Assistant

**Capabl Agent AI Program — Week 2 Submission**
**Team:** Rakim & Saif

## What this is

Hertz is an AI assistant that lets students upload lab manuals and ask
questions about experiments instead of flipping through pages — starting
with procedure lookup ("What is the procedure of Experiment 3?").

It's a genuine tool-calling agent: the AI decides for itself whether to
search the manual, rather than following one fixed hardcoded path.

## Why this counts as an agent, not "just code"

| Hardcoded RAG chain | This project |
|---|---|
| Always retrieves, every single query | The LLM **decides** whether retrieval is needed |
| One fixed path | The LLM chooses which tool(s) to call, in what order |
| No reasoning step | The LLM reasons about the question before acting |

The agent is built with LangChain's `create_agent`, which wraps the model in
a tool-calling loop (model -> decide -> call tool -> observe result -> decide
again -> answer). Right now it has **one** tool, `get_procedure`. In Weeks
3-4, more tools (`explain_theory`, `get_safety_info`, `calculate`) get added
to the *same* agent — the architecture doesn't change, only the toolbox
grows.

## Architecture

```
Student question
      |
      v
  Gemini LLM (the agent's "brain")
      |
      | decides: "this needs the manual" -> calls tool
      v
 get_procedure(experiment_query)
      |
      | searches FAISS vector index built from the uploaded PDF
      v
 Relevant manual excerpts (with page numbers)
      |
      v
  Gemini LLM synthesizes a final answer, grounded in the excerpts
      |
      v
  Answer shown in Streamlit chat
```

## Files

- `agent.py` — the agent itself: PDF -> chunks -> FAISS vectorstore,
  the `get_procedure` tool, and the tool-calling agent construction.
- `app.py` — Streamlit UI: upload a PDF, chat with the agent.
- `requirements.txt` — pinned dependency versions.
- `.env.example` — template for your Gemini API key.

## Setup

1. Get a free Gemini API key: https://aistudio.google.com/app/apikey
2. Clone this repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your API key (either):
   - Copy `.env.example` to `.env` and fill in your key, or
   - Enter it directly in the app's password field when it launches.
4. Run locally:
   ```bash
   streamlit run app.py
   ```
5. Upload a lab manual PDF and ask a question about an experiment.

## Deployment (Streamlit Cloud)

1. Push this repo to GitHub.
2. Go to https://share.streamlit.io and connect the repo.
3. Set `app.py` as the entry point.
4. In the app's Settings -> Secrets, add:
   ```
   GOOGLE_API_KEY = "your_key_here"
   ```
5. Deploy. You'll get a public URL to include in your submission.

## Week 1 checklist (from the project brief)

- [x] GitHub repo with lab assistant project structure
- [x] Development environment set up (Python, LangChain, Streamlit, PyPDF, FAISS)
- [x] Lab manual PDF processing and text extraction
- [x] Basic experiment identification via semantic search (experiment name/number in query)
- [x] Procedure step extraction and formatting, with page-level source citation
- [x] Streamlit interface for upload + experiment queries
- [ ] Deploy on Streamlit Cloud *(do this after you test locally with your own manual)*
- [ ] Record 2-minute demo video *(record after deployment)*

## What's intentionally NOT in Week 1

Theory explanation, safety info, and calculations are Week 3-4 tools.
Adding them now would just mean rebuilding this same architecture later —
better to get one tool working end-to-end and correctly first.

## Known limitations (be upfront about these in the viva)

- Experiment identification relies on semantic similarity search, not a
  strict "Experiment N" parser — very inconsistently numbered manuals may
  need query rephrasing (e.g. "titration experiment" instead of "Exp 3").
- No persistent storage yet — re-uploading is required each session
  (SQLite metadata for experiment tracking is a Week 2+ addition).
- Single-tool agent — by design, for a focused Week 1 milestone.
