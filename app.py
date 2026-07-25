"""
Hertz — Lab Manual Conversational Assistant
Capabl Agent AI Program — Week 4
Minimal Streamlit front-end. Full UI polish is a later-week deliverable;
this just wires the Week 4 agent up to a chat interface so it can be
demoed and deployed on Streamlit Cloud.
"""

import streamlit as st
from agent import build_vectorstore, build_agent

st.set_page_config(page_title="Hertz — Lab Manual Assistant", page_icon="🔬")
st.title("🔬 Hertz — Lab Manual Conversational Assistant")
st.caption("Week 4: procedure, theory, safety-info, and calculate — multi-tool agent")

if "executor" not in st.session_state:
    st.session_state.executor = None
if "messages" not in st.session_state:
    st.session_state.messages = []

uploaded_pdf = st.file_uploader("Upload your lab manual (PDF)", type="pdf")

if uploaded_pdf is not None and st.session_state.executor is None:
    with st.spinner("Reading and indexing your lab manual..."):
        temp_path = f"/tmp/{uploaded_pdf.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_pdf.getbuffer())
        build_vectorstore(temp_path)
        st.session_state.executor = build_agent()
    st.success("Manual indexed. Ask away!")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if question := st.chat_input("Ask about a procedure, theory, or safety info..."):
    if st.session_state.executor is None:
        st.warning("Please upload a lab manual PDF first.")
    else:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = st.session_state.executor.invoke({"input": question})
                answer = result["output"]
                st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})
