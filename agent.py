"""
Hertz — Lab Manual Conversational Assistant — Agent Core (Week 5)

This is a genuine tool-calling AI AGENT, not a hardcoded RAG chain.

The difference matters:
  - A RAG CHAIN always does: question -> retrieve -> answer. Same path every time.
  - An AGENT is given tools and DECIDES for itself whether to call a tool,
    which tool(s) to call, and what to do with the result, before answering.

Week 1-2: get_procedure. Week 3: explain_theory, get_safety_info.
Week 4: calculate (closing the Week 3-4 "complete experiment understanding"
milestone). Week 5 begins the Week 5-6 "Domain Specialization" milestone
using Track A Option A2 (Comprehensive Experiment Guide): prelab_prep and
postlab_report_help extend the assistant across the full experiment
lifecycle — before, during, and after the lab session — not just the
procedure itself.
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


def make_explain_theory_tool(vectorstore):
    """
    Factory that builds an explain_theory tool bound to a specific lab
    manual's vectorstore.
    """

    @tool
    def explain_theory(topic_or_experiment: str) -> str:
        """
        Retrieves the theory, background concept, or working principle
        behind an experiment or topic from the uploaded lab manual. Use
        this whenever the student asks "why", "what is the concept behind",
        "explain the theory of", or wants to understand a topic rather than
        just the steps to perform it, e.g. "Explain the theory behind
        Experiment 3" or "What is the principle of titration?". Input
        should be the topic or experiment name/number as mentioned by
        the student.
        """
        results = vectorstore.similarity_search(
            f"theory principle concept background {topic_or_experiment}", k=4
        )
        if not results:
            return "No matching theory or background section was found in this manual."

        context = "\n\n---\n\n".join(
            f"[Source: page {doc.metadata.get('page', '?')}]\n{doc.page_content}"
            for doc in results
        )
        return context

    return explain_theory


def make_get_safety_info_tool(vectorstore):
    """
    Factory that builds a get_safety_info tool bound to a specific lab
    manual's vectorstore.
    """

    @tool
    def get_safety_info(experiment_query: str) -> str:
        """
        Retrieves safety precautions, hazards, and required protective
        equipment for a specific experiment from the uploaded lab manual.
        Use this whenever the student asks about safety, precautions,
        hazards, risks, or what protective gear is needed, e.g. "What
        safety precautions should I take for Experiment 3?" or "Is this
        chemical hazardous?". Input should be the experiment name or
        number as mentioned by the student.
        """
        results = vectorstore.similarity_search(
            f"safety precautions hazards warning {experiment_query}", k=4
        )
        if not results:
            return (
                "No specific safety section was found in this manual for that "
                "experiment. Advise the student to follow standard lab safety "
                "practices and check with their lab instructor."
            )

        context = "\n\n---\n\n".join(
            f"[Source: page {doc.metadata.get('page', '?')}]\n{doc.page_content}"
            for doc in results
        )
        return context

    return get_safety_info


def make_calculate_tool():
    """
    Factory for the calculate tool. This one does NOT need the vectorstore —
    it's a pure computation tool, not a retrieval tool. Uses a safe,
    restricted expression evaluator (no eval() on raw input).
    """
    import ast
    import operator

    _OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.Mod: operator.mod,
    }

    def _safe_eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_safe_eval(node.operand))
        raise ValueError("Unsupported expression")

    @tool
    def calculate(expression: str) -> str:
        """
        Evaluates a mathematical expression — use this for unit conversions,
        formula-based calculations, or any arithmetic the student needs while
        working through an experiment (e.g. molarity calculations, converting
        units, computing a result from a formula). Input must be a plain
        arithmetic expression using numbers and + - * / % ** and parentheses
        only, e.g. "(0.5 * 1000) / 250" or "2.5 ** 2". Do not include units
        or variable names in the expression — resolve those to numbers first.
        """
        try:
            tree = ast.parse(expression, mode="eval")
            result = _safe_eval(tree.body)
            return f"{expression} = {result}"
        except Exception:
            return (
                f"Could not evaluate '{expression}'. Please provide a plain "
                "numeric expression using + - * / % ** and parentheses only."
            )

    return calculate


def make_prelab_prep_tool(vectorstore):
    """
    Factory for the pre-lab preparation tool (Week 5 — Option A2:
    Comprehensive Experiment Guide specialization).
    """

    @tool
    def prelab_prep(experiment_query: str) -> str:
        """
        Generates a pre-lab preparation checklist for an experiment: what
        to read beforehand, what equipment/materials to bring, and what
        background knowledge is assumed. Use this when the student asks
        "what should I prepare before Experiment 3", "what do I need before
        the lab session", or similar before-the-lab questions. Input should
        be the experiment name or number.
        """
        results = vectorstore.similarity_search(
            f"apparatus materials equipment required prerequisites {experiment_query}",
            k=4,
        )
        if not results:
            return "No matching pre-lab information was found in this manual."

        context = "\n\n---\n\n".join(
            f"[Source: page {doc.metadata.get('page', '?')}]\n{doc.page_content}"
            for doc in results
        )
        return context

    return prelab_prep


def make_postlab_report_tool(vectorstore):
    """
    Factory for the post-lab report assistance tool (Week 5 — Option A2:
    Comprehensive Experiment Guide specialization).
    """

    @tool
    def postlab_report_help(experiment_query: str) -> str:
        """
        Retrieves what should go into the post-lab report/record for an
        experiment: observations to note, expected results, and the
        conclusion format expected in the manual. Use this when the
        student asks about writing up the experiment, what to include in
        the lab record, or what results/observations to note down. Input
        should be the experiment name or number.
        """
        results = vectorstore.similarity_search(
            f"observation result conclusion report record {experiment_query}",
            k=4,
        )
        if not results:
            return (
                "No specific report/observation format was found in this manual "
                "for that experiment. Advise the student to follow their "
                "institution's standard lab record format."
            )

        context = "\n\n---\n\n".join(
            f"[Source: page {doc.metadata.get('page', '?')}]\n{doc.page_content}"
            for doc in results
        )
        return context

    return postlab_report_help


# ---------------------------------------------------------------------------
# STEP 3: Build the actual AGENT (tool-calling loop, not a fixed chain)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are Hertz, a laboratory manual assistant for engineering students. "
    "You have six tools available:\n"
    "- get_procedure: finds step-by-step experiment procedures\n"
    "- explain_theory: finds the theory/concept/principle behind an experiment\n"
    "- get_safety_info: finds safety precautions and hazards for an experiment\n"
    "- calculate: evaluates a numeric expression for unit conversions or "
    "formula-based calculations\n"
    "- prelab_prep: finds what to prepare/bring/know before starting an "
    "experiment\n"
    "- postlab_report_help: finds what observations/results/conclusion "
    "format belongs in the lab report for an experiment\n\n"
    "Decide which tool(s) are relevant to the student's question — call more "
    "than one if the question genuinely needs it (e.g. a question asking for "
    "both the procedure and the safety precautions should call both tools). "
    "Base retrieval-based answers ONLY on what the tools return — never "
    "invent manual content. If a tool finds nothing relevant, say so "
    "honestly. Always mention which page(s) retrieved information came from "
    "so the student can cross-check the original manual. Keep answers clear "
    "and organized, using headings or steps where useful when multiple tools "
    "contributed to one answer."
)


def build_agent(vectorstore):
    """
    Creates a tool-calling agent backed by Gemini using LangChain's current
    create_agent API (a prebuilt LangGraph ReAct-style loop under the hood).

    The LLM decides for itself which of the six tools (if any) to call
    based on the student's question — this is NOT a hardcoded router.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2,
    )

    tools = [
        make_get_procedure_tool(vectorstore),
        make_explain_theory_tool(vectorstore),
        make_get_safety_info_tool(vectorstore),
        make_calculate_tool(),
        make_prelab_prep_tool(vectorstore),
        make_postlab_report_tool(vectorstore),
    ]

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
