"""
Lab Manual — API Layer (Week 6)

Exposes the existing agent (agent.py — unchanged) as real HTTP endpoints,
in addition to the Streamlit UI in app.py. Same agent, same tools —
this just gives it a second, API-based way to be used.

Run with:
    uvicorn api:app --reload

Endpoints:
    POST /upload   — upload a lab manual PDF, returns a session_id
    POST /ask       — ask a question against a previously uploaded manual
    GET  /health    — simple health check
"""

import os
import tempfile
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agent import build_vectorstore, build_agent, ask_agent

app = FastAPI(title="Lab Manual API", description="Lab Manual Conversational Assistant API")

# Allow the frontend (deployed separately, e.g. on Vercel/Netlify) to call
# this API from the browser. Wide open for coursework/demo purposes — if
# this ever needs real access control, replace "*" with the actual
# frontend origin(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store: session_id -> agent executor
# NOTE: this resets if the server restarts. Fine for a demo/coursework
# deployment; a real product would persist this (see README limitations).
_SESSIONS: dict[str, object] = {}


class AskRequest(BaseModel):
    session_id: str
    question: str


class AskResponse(BaseModel):
    answer: str


@app.get("/health")
def health():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "lab-manual-api"}


@app.post("/upload")
async def upload_manual(file: UploadFile = File(...)):
    """
    Upload a lab manual PDF. Builds a FAISS index and an agent bound to it,
    stores the agent in-memory under a new session_id, and returns that id.
    Use the returned session_id in subsequent /ask calls.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        vectorstore = build_vectorstore(tmp_path)
        agent = build_agent(vectorstore)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {e}")
    finally:
        os.unlink(tmp_path)

    session_id = str(uuid.uuid4())
    _SESSIONS[session_id] = agent

    return JSONResponse({"session_id": session_id, "filename": file.filename})


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """
    Ask a question against a manual that was previously uploaded via /upload.
    The agent decides which of its six tools to call based on the question.
    """
    agent = _SESSIONS.get(request.session_id)
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown session_id. Upload a manual via /upload first.",
        )

    try:
        answer = ask_agent(agent, request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    return AskResponse(answer=answer)
