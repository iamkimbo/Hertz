"""
Lab Manual Conversational Assistant — Week 1 Agent Core

This is a genuine tool-calling AI AGENT, not a hardcoded RAG chain.

The difference matters:
  - A RAG CHAIN always does: question -> retrieve -> answer. Same path every time.
  - An AGENT is given tools and DECIDES for itself whether to call a tool,
    which tool to call, and what to do with the result, before answering.

Week 1 ships with exactly ONE tool (get_procedure) registered on a real
tool-calling agent loop. Weeks 3-4 add explain_theory, get_safety_info,
calculate, etc. as MORE tools on the SAME agent — the architecture doesn't
change, only the toolbox grows.
"""

import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.agents import create_agent
from langchain_core.tools import tool

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# ---------------------------------------------------------------------------
# STEP 1: Build a vector store from an uploaded lab manual PDF
# ---------------------------------------------------------------------------

def build_vectorstore(pdf_path: str):
    """
    Loads a lab manual PDF, splits it into overlapping chunks, embeds each
    chunk with Gemini's embedding model, and stores them in a FAISS index
    for similarity search. Returns the FAISS vectorstore.
    """
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(pages)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GOOGLE_API_KEY,
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore


# ---------------------------------------------------------------------------
# STEP 2: Define the agent's TOOL(S)
#
# A tool is just a Python function the LLM can choose to call. The agent
# sees the function name, its docstring, and its arguments, and decides
# on its own when it's relevant to use.
# ---------------------------------------------------------------------------

def make_get_procedure_tool(vectorstore):
    """
    Factory that builds a get_procedure tool bound to a specific lab
    manual's vectorstore (each uploaded manual gets its own tool instance).
    """

    @tool
    def get_procedure(experiment_query: str) -> str:
        """
        Retrieves the step-by-step procedure for a specific experiment from
        the uploaded lab manual. Use this whenever the student asks what the
        steps/procedure/method of an experiment are, e.g. "What is the
        procedure of Experiment 3?" or "How do I perform the titration
        experiment?". Input should be the experiment name or number as
        mentioned by the student.
        """
        results = vectorstore.similarity_search(experiment_query, k=4)
        if not results:
            return "No matching experiment procedure was found in this manual."

        context = "\n\n---\n\n".join(
            f"[Source: page {doc.metadata.get('page', '?')}]\n{doc.page_content}"
            for doc in results
        )
        return context

    return get_procedure


# ---------------------------------------------------------------------------
# STEP 3: Build the actual AGENT (tool-calling loop, not a fixed chain)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a laboratory manual assistant for engineering students. "
    "You have access to a tool called get_procedure that searches the "
    "student's uploaded lab manual. Call it whenever the student asks "
    "about an experiment's steps or procedure. Base your answer ONLY on "
    "what the tool returns — do not invent procedure steps. If the tool "
    "finds nothing relevant, say so honestly and ask the student to "
    "check the experiment name or number. Always mention which page(s) "
    "the information came from so the student can cross-check the "
    "original manual. Keep answers clear and step-by-step."
)


def build_agent(vectorstore):
    """
    Creates a tool-calling agent backed by Gemini using LangChain's current
    create_agent API (a prebuilt LangGraph ReAct-style loop under the hood).

    The LLM decides for itself whether to call get_procedure based on the
    student's question — this is NOT a hardcoded call that fires every time.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2,
    )

    tools = [make_get_procedure_tool(vectorstore)]

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
    return agent


def ask_agent(agent, question: str) -> str:
    """
    Runs the agent on a single question and returns the final text answer.
    """
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    final_message = result["messages"][-1]
    return final_message.content
