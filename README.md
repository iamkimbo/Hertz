# Hertz — Lab Manual Conversational Assistant

**Capabl Agent AI Program — Week 4 Submission**
**Team:** Rakim & Saif

## What this is

Hertz is an AI assistant that lets students upload lab manuals and ask
questions about experiments instead of flipping through pages. It's a
genuine tool-calling agent: the AI decides for itself which tool(s) to
call based on the question, rather than following one fixed hardcoded path.

## What's new this week

Week 4 completes the core Track A toolset. The agent now has **four tools**:

- **`get_procedure`** *(Week 2)* — step-by-step experiment procedure
- **`explain_theory`** *(Week 3)* — theory/concept/principle behind an experiment
- **`get_safety_info`** *(Week 3)* — precautions and hazards for an experiment
- **`calculate`** *(new)* — evaluates numeric expressions for unit
  conversions and formula-based calculations (e.g. molarity, dilution),
  using a safe AST-based evaluator — not a raw `eval()` — so it can't be
  used to run arbitrary code

This closes the Week 3-4 milestone: a complete multi-tool agent that
correctly picks which tool(s) a question needs, including combining more
than one tool in a single answer — e.g. "explain Experiment 3, list its
safety precautions, and calculate the molarity for 0.5 mol in 250 mL"
triggers three separate tool calls, merged into one response.

## Why this counts as an agent, not "just code"

| Hardcoded pipeline | Hertz |
|---|---|
| Always retrieves, every single query | The LLM **decides** whether retrieval is needed, and which kind |
| One fixed path | The LLM chooses which tool(s) to call, in what order |
| No reasoning step | The LLM reasons about the question before acting |

Built with LangChain's `create_agent`, which wraps Gemini in a tool-calling
loop: model reasons -> decides to call a tool (or several) -> observes the
result(s) -> reasons again -> answers.

## Files

- `agent.py` — vector store setup + all four tools + agent construction
- `app.py` — Streamlit chat UI wired to the agent
- `requirements.txt` — pinned dependencies (tested versions)
- `.env.example` — template for your Gemini API key

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
5. Upload a lab manual PDF and try a question that needs more than one
   tool, e.g. "Explain Experiment 3's theory and list the safety
   precautions."

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

- `calculate` only accepts plain numeric expressions (numbers and
  `+ - * / % **`) — it won't resolve units or variable names on its own;
  the LLM is expected to convert those to numbers before calling it.
- Experiment identification is semantic-search based, not a strict
  "Experiment N" parser.
- No persistent storage yet — re-uploading is required each session.

## Next (Week 5-6)

Pick a Track A specialization: either subject-specific handling (Physics
vs Chemistry vs CS labs) or full experiment lifecycle support (pre-lab,
during-lab, post-lab).
