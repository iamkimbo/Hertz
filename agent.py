"""
Hertz — Lab Manual Conversational Assistant
Capabl Agent AI Program — Week 3

Core agent module. A genuine LangChain tool-calling agent: the LLM decides
which tool (if any) to call based on the student's question, rather than
following one fixed hardcoded path.

Week 3 adds two new tools on top of Week 2's get_procedure:
  - explain_theory     -> looks up the theory/background section of an experiment
  - get_safety_info     -> looks up precautions / safety notes for an experiment

All three tools share the same underlying FAISS vector store built from the
uploaded lab manual PDF; each tool differs in *what section it steers the
retrieval toward* and how it's described to the LLM.
"""

import os
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ---------------------------------------------------------------------------
# Vector store setup (shared across all tools)
# ---------------------------------------------------------------------------

_vectorstore = None


def build_vectorstore(pdf_path: str):
    """Load a lab manual PDF, split it, and embed it into a FAISS index.
    Called once per uploaded manual; result is cached in _vectorstore."""
    global _vectorstore

    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(pages)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_API_KEY,
    )

    _vectorstore = FAISS.from_documents(chunks, embeddings)
    return _vectorstore


def _search(query: str, k: int = 4) -> str:
    if _vectorstore is None:
        return "No lab manual has been uploaded yet. Please upload a PDF first."
    results = _vectorstore.similarity_search(query, k=k)
    if not results:
        return "Nothing relevant found in the manual for that query."
    return "\n\n---\n\n".join(r.page_content for r in results)


# ---------------------------------------------------------------------------
# Tools — each one is a distinct capability the agent can choose to invoke
# ---------------------------------------------------------------------------

@tool
def get_procedure(experiment_query: str) -> str:
    """Use this to find the step-by-step procedure of a lab experiment.
    Input should describe which experiment, e.g. 'Experiment 3' or
    'the procedure for finding resistivity'."""
    query = f"procedure steps method {experiment_query}"
    return _search(query)


@tool
def explain_theory(experiment_query: str) -> str:
    """Use this to explain the theory, background, or underlying concept
    behind a lab experiment — for questions like 'why does this happen'
    or 'what is the theory behind Experiment 2'. Input should describe
    which experiment or concept the student is asking about."""
    query = f"theory background principle concept aim {experiment_query}"
    return _search(query)


@tool
def get_safety_info(experiment_query: str) -> str:
    """Use this to find safety precautions, warnings, or things to be
    careful about for a lab experiment — for questions like 'what
    precautions should I take' or 'is this experiment dangerous'.
    Input should describe which experiment."""
    query = f"precautions safety warning caution hazard {experiment_query}"
    return _search(query)


TOOLS = [get_procedure, explain_theory, get_safety_info]

# ---------------------------------------------------------------------------
# Agent construction
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Hertz, an assistant that helps engineering students
understand their lab manual. You have three tools available:

- get_procedure: for step-by-step "how do I do this experiment" questions
- explain_theory: for "why" / conceptual / background questions
- get_safety_info: for precautions and safety questions

Decide which tool (if any) is relevant to the student's question and call it.
If the question needs more than one tool, call them in sequence. If the
question doesn't need the manual at all (e.g. general chit-chat), answer
directly without calling a tool. Always answer using only information
retrieved from the manual — don't invent experiment details that weren't
found in a tool result. If nothing relevant was found, say so plainly."""


def build_agent():
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    executor = AgentExecutor(agent=agent, tools=TOOLS, verbose=True)
    return executor


if __name__ == "__main__":
    # Quick manual smoke test (requires a PDF path + GEMINI_API_KEY set)
    import sys
    if len(sys.argv) < 2:
        print("Usage: python agent.py <path_to_lab_manual.pdf>")
        sys.exit(1)

    build_vectorstore(sys.argv[1])
    executor = build_agent()

    print("Hertz agent ready. Ask a question (Ctrl+C to quit).")
    while True:
        q = input("\n> ")
        result = executor.invoke({"input": q})
        print("\n", result["output"])
