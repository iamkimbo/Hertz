"""
Hertz — Lab Manual Conversational Assistant — Streamlit UI (Week 4)

Upload a lab manual PDF, then ask it questions like:
    "What is the procedure of Experiment 3?"
    "Explain the theory behind Experiment 3"
    "What safety precautions should I take?"
    "Calculate molarity for 0.5 mol in 250 mL"

Behind this UI is a real tool-calling AGENT (see agent.py) with four tools
— not a hardcoded retrieve-then-answer chain.
"""

import os
import tempfile
import streamlit as st
from agent import build_vectorstore, build_agent, ask_agent

st.set_page_config(page_title="Hertz — Lab Manual Assistant", page_icon="🔬", layout="centered")

st.title("🔬 Hertz — Lab Manual Conversational Assistant")
st.caption("Upload your lab manual PDF, then ask about procedures, theory, safety, or calculations.")

# --- API key handling -------------------------------------------------------
api_key = os.environ.get("GOOGLE_API_KEY") or st.session_state.get("api_key", "")
if not api_key:
    api_key = st.text_input("Enter your Google Gemini API key", type="password")
    if api_key:
        st.session_state["api_key"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key

if not api_key:
    st.info("Get a free Gemini API key at https://aistudio.google.com/app/apikey")
    st.stop()

# --- Session state -----------------------------------------------------------
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Upload + process lab manual ---------------------------------------------
uploaded_file = st.file_uploader("Upload lab manual (PDF)", type=["pdf"])

if uploaded_file is not None and st.session_state.vectorstore is None:
    with st.spinner("Reading and indexing your lab manual... this takes a moment"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            vectorstore = build_vectorstore(tmp_path)
            st.session_state.vectorstore = vectorstore
            st.session_state.agent = build_agent(vectorstore)
            st.success(f"Manual processed! You can now ask questions about it.")
        except Exception as e:
            st.error(f"Something went wrong while processing the PDF: {e}")
        finally:
            os.unlink(tmp_path)

if uploaded_file is None:
    st.session_state.vectorstore = None
    st.session_state.agent = None

# --- Chat interface -----------------------------------------------------------
if st.session_state.agent is not None:
    st.divider()
    st.subheader("Ask about an experiment")

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    user_question = st.chat_input("e.g. Explain Experiment 3's theory and safety precautions")

    if user_question:
        st.session_state.chat_history.append(("user", user_question))
        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    answer = ask_agent(st.session_state.agent, user_question)
                except Exception as e:
                    answer = f"Something went wrong: {e}"
                st.markdown(answer)
        st.session_state.chat_history.append(("assistant", answer))
else:
    st.info("Upload a lab manual PDF above to get started.")
