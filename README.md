# Hertz — Lab Manual Conversational Assistant

**Capabl Agent AI Program — Week 3 Submission**
**Team:** Rakim & Saif

## What's new this week

Week 2 shipped a single-tool agent (`get_procedure`). Week 3 expands the
agent to three tools, so it's genuinely choosing between capabilities
rather than always doing the same lookup:

- **`get_procedure`** — step-by-step experiment procedure (from Week 2)
- **`explain_theory`** *(new)* — theory/background/concept behind an experiment
- **`get_safety_info`** *(new)* — precautions and safety warnings for an experiment

The agent is still a genuine LangChain tool-calling agent: given a
student's question, the LLM itself decides which tool (if any) to call —
this is not a hardcoded if/else router. All three tools query the same
FAISS index of the uploaded manual, but each nudges retrieval toward a
different kind of content and is described differently to the LLM so it
learns when to use which.

## Files

- `agent.py` — vector store setup + all three tools + agent construction
- `app.py` — minimal Streamlit chat UI wired to the agent
- `requirements.txt` — dependencies

## Running locally

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your_key_here
streamlit run app.py
```

## Next week (Week 4)

Add a `calculate` tool and refine multi-tool routing (e.g. handling
questions that need both theory and safety info together), closing out
the Week 3–4 milestone.
