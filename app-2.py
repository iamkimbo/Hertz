"""
Hertz — Lab Manual Conversational Assistant — Streamlit UI (Week 7)

Upload a lab manual PDF, then ask it questions like:
    "What is the procedure of Experiment 3?"
    "Explain the theory behind Experiment 3"
    "What safety precautions should I take?"
    "Calculate molarity for 0.5 mol in 250 mL"
    "What should I prepare before Experiment 3?"
    "What should I note down for the lab report?"

Behind this UI is a real tool-calling AGENT (see agent.py) with six tools
covering the full experiment lifecycle — before, during, and after the
lab session — not a hardcoded retrieve-then-answer chain.

Week 7 focus: frontend polish for presentation (theme, layout, empty
states, status indicators). No agent logic changed in this file.
"""

import os
import tempfile
import streamlit as st
from agent import build_vectorstore, build_agent, ask_agent

st.set_page_config(
    page_title="Hertz — Lab Manual Assistant",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --- Header -------------------------------------------------------------
st.markdown(
    """
    <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0;">
        <span style="font-size:2.1rem;">🔬</span>
        <span style="font-size:1.9rem; font-weight:700; color:#1B2A2A;">Hertz</span>
    </div>
    <p style="color:#5B6B6B; margin-top:0.1rem; margin-bottom:1.2rem; font-size:0.95rem;">
        Ask your lab manual anything — procedures, theory, safety, calculations, prep, or reports.
    </p>
    """,
    unsafe_allow_html=True,
)

# --- Sidebar: capabilities + example questions ---------------------------
with st.sidebar:
    st.markdown("### What Hertz can help with")
    st.markdown(
        "- 📋 **Procedure** — step-by-step instructions\n"
        "- 📖 **Theory** — the concept behind an experiment\n"
        "- ⚠️ **Safety** — precautions and hazards\n"
        "- 🧮 **Calculations** — unit conversions, formulas\n"
        "- 🎒 **Pre-lab prep** — what to bring/know beforehand\n"
        "- 📝 **Post-lab report** — what to note for your write-up\n"
    )
    st.divider()
    st.markdown("### Try asking")
    example_questions = [
        "What is the procedure of Experiment 3?",
        "Explain the theory behind Experiment 3",
        "What safety precautions should I take?",
        "What should I prepare before this experiment?",
        "What should I note down for the lab report?",
    ]
    clicked_example = None
    for eq in example_questions:
        if st.button(eq, use_container_width=True):
            clicked_example = eq

    st.divider()
    st.caption("Built by Rakim & Saif · Capabl Agent AI Program")

# --- API key handling -----------------------------------------------------
api_key = os.environ.get("GOOGLE_API_KEY") or st.session_state.get("api_key", "")
if not api_key:
    api_key = st.text_input("Enter your Google Gemini API key", type="password")
    if api_key:
        st.session_state["api_key"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key

if not api_key:
    st.info("Get a free Gemini API key at https://aistudio.google.com/app/apikey")
    st.stop()

# --- Session state ----------------------------------------------------------
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "manual_name" not in st.session_state:
    st.session_state.manual_name = None

# --- Upload + process lab manual --------------------------------------------
uploaded_file = st.file_uploader(
    "Upload lab manual (PDF)",
    type=["pdf"],
    help="Your manual is processed locally for this session and not stored permanently.",
)

if uploaded_file is not None and st.session_state.vectorstore is None:
    with st.spinner(f"Reading and indexing \u201c{uploaded_file.name}\u201d\u2026"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            vectorstore = build_vectorstore(tmp_path)
            st.session_state.vectorstore = vectorstore
            st.session_state.agent = build_agent(vectorstore)
            st.session_state.manual_name = uploaded_file.name
        except Exception as e:
            st.error(f"Something went wrong while processing the PDF: {e}")
        finally:
            os.unlink(tmp_path)

if uploaded_file is None:
    st.session_state.vectorstore = None
    st.session_state.agent = None
    st.session_state.manual_name = None

# --- Status strip -------------------------------------------------------
if st.session_state.agent is not None:
    st.success(f"✅ **{st.session_state.manual_name}** is ready — ask a question below.")

# --- Chat interface -----------------------------------------------------------
if st.session_state.agent is not None:
    st.divider()

    if not st.session_state.chat_history:
        st.markdown(
            "<p style='color:#5B6B6B; font-size:0.9rem;'>"
            "No questions yet — type one below, or click an example in the sidebar."
            "</p>",
            unsafe_allow_html=True,
        )

    for role, msg in st.session_state.chat_history:
        avatar = "🧑‍🎓" if role == "user" else "🔬"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg)

    user_question = st.chat_input(
        "e.g. What should I prepare before Experiment 3, and what should I note for the report?"
    )

    # An example-question button click counts the same as typing + submitting
    if clicked_example and not user_question:
        user_question = clicked_example

    if user_question:
        st.session_state.chat_history.append(("user", user_question))
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(user_question)

        with st.chat_message("assistant", avatar="🔬"):
            with st.spinner("Thinking..."):
                try:
                    answer = ask_agent(st.session_state.agent, user_question)
                except Exception as e:
                    answer = f"Something went wrong: {e}"
                st.markdown(answer)
        st.session_state.chat_history.append(("assistant", answer))
else:
    st.markdown(
        """
        <div style="text-align:center; padding: 2.5rem 1rem; background:#EEF3F1;
                    border-radius:12px; margin-top:1rem;">
            <div style="font-size:2.4rem;">📄</div>
            <p style="color:#1B2A2A; font-weight:600; margin:0.4rem 0 0.2rem 0;">
                No manual loaded yet
            </p>
            <p style="color:#5B6B6B; font-size:0.9rem; margin:0;">
                Upload a lab manual PDF above to start asking questions.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
