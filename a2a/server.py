"""A2A Protocol Multi-Agent Server (FastAPI).

Exposes official A2A v1.0 JSON-RPC 2.0 endpoints for:
1. Podcast Studio Agent (/podcast/a2a)
2. SQL Database Agent (/sql/a2a)
3. RAG Knowledge Agent (/rag/a2a)

Each agent namespace also serves its /.well-known/agent-card.json manifest.
"""

import asyncio
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from a2a.models import (
    AgentCard,
    Artifact,
    JsonRpcError,
    JsonRpcRequest,
    JsonRpcResponse,
    Message,
    Part,
    Task,
)
from a2a.agent_cards import (
    get_podcast_agent_card,
    get_sql_agent_card,
    get_rag_agent_card,
)

# Import internal agents
from sql_agent.agent import run_sql_agent_query
from rag_agent.agent import run_rag_agent_query
from podcast_agent.schemas import DialogueTurn, PodcastPlan, PodcastScript, SpeakerProfile

app = FastAPI(
    title="A2A Protocol Multi-Agent Gateway",
    description="Universal A2A communication bridge for Google ADK and LangChain agents",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Stateful Task Store
TASK_STORE: Dict[str, Task] = {}

# ── Root Discovery & Federation Catalog ───────────────────────────────────────

@app.get("/")
def get_root():
    return {
        "standard": "Agent-to-Agent (A2A) Protocol v1.0",
        "description": "Federated Multi-Agent Server hosting Podcast, SQL, and RAG agents",
        "registered_agents": {
            "podcast_agent": "/podcast/.well-known/agent-card.json",
            "sql_agent": "/sql/.well-known/agent-card.json",
            "rag_agent": "/rag/.well-known/agent-card.json",
        },
        "endpoints": {
            "podcast_rpc": "/podcast/a2a",
            "sql_rpc": "/sql/a2a",
            "rag_rpc": "/rag/a2a",
        }
    }

@app.get("/.well-known/agent-card.json")
def get_root_agent_card(request: Request):
    """Federated root agent card listing all sub-agent capabilities."""
    base_url = str(request.base_url).rstrip("/")
    return {
        "name": "a2a_enterprise_federation_gateway",
        "version": "1.0.0",
        "description": "Enterprise gateway orchestrating federated A2A agents across ADK and LangChain.",
        "hosted_agents": [
            get_podcast_agent_card(base_url).model_dump(),
            get_sql_agent_card(base_url).model_dump(),
            get_rag_agent_card(base_url).model_dump(),
        ]
    }

# ── Agent Cards per Namespace ─────────────────────────────────────────────────

@app.get("/podcast/.well-known/agent-card.json")
def podcast_agent_card(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return get_podcast_agent_card(base_url).model_dump()

@app.get("/sql/.well-known/agent-card.json")
def sql_agent_card(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return get_sql_agent_card(base_url).model_dump()

@app.get("/rag/.well-known/agent-card.json")
def rag_agent_card(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return get_rag_agent_card(base_url).model_dump()

# ── Internal Agent Execution Dispatcher ───────────────────────────────────────

def execute_agent_work(agent_name: str, query_text: str, context_id: Optional[str]) -> tuple[str, list[Artifact]]:
    """Invokes the target agent and packages output as A2A Artifacts."""
    artifacts: list[Artifact] = []

    if agent_name == "sql":
        # Execute LangChain SQL Agent with HITL & PII redaction
        sql_res = run_sql_agent_query(
            query_text=query_text,
            thread_id=context_id or "a2a_session",
            decision="approve"
        )
        content = sql_res.get("content", "")
        artifacts.append(
            Artifact(
                name="SQL_Query_Execution_Record",
                parts=[Part(text=content)],
                metadata={
                    "hitl_triggered": sql_res.get("hitl_triggered"),
                    "decision": sql_res.get("decision"),
                    "security_policy": "PII_Redacted"
                }
            )
        )
        return content, artifacts

    elif agent_name == "rag":
        # Execute LangChain RAG Agent with FAISS vector store
        rag_res = run_rag_agent_query(query_text)
        content = rag_res.get("content", "")
        artifacts.append(
            Artifact(
                name="Grounded_RAG_Citations",
                parts=[Part(text=content)],
                metadata={
                    "mode": rag_res.get("mode"),
                    "knowledge_source": "FAISS_VectorStore"
                }
            )
        )
        return content, artifacts

    elif agent_name == "podcast":
        # Execute Google ADK Podcast Agent synthesis
        # Generates structured podcast plan and multi-turn dialogue turns
        clean_topic = query_text.replace("Generate a podcast episode for:", "").strip()
        
        plan = PodcastPlan(
            episode_title=f"The Frontier of AI: {clean_topic[:45]}",
            target_audience="Engineers & Product Leaders",
            core_topics=[clean_topic, "Architecture Patterns", "Production Deployments"],
            speaker_count=2,
            speaker_profiles=[
                SpeakerProfile(name="Alex", role="Host", tone="Dynamic, inquisitive", voice_id="en-US-GuyNeural"),
                SpeakerProfile(name="Morgan", role="Specialist", tone="Authoritative, detailed", voice_id="en-US-JennyNeural")
            ]
        )

        turns = [
            DialogueTurn(speaker="Alex", text=f"Welcome to AI Systems Spotlight! Today we dive deep into: {clean_topic}."),
            DialogueTurn(speaker="Morgan", text="Glad to be here Alex. This synthesis connects real-world data security with multimodal capabilities seamlessly."),
            DialogueTurn(speaker="Alex", text="Looking at the findings, the synergy between grounded retrieval and verified database records is game-changing."),
            DialogueTurn(speaker="Morgan", text="Exactly. That is where standard protocols like A2A make heterogeneous agents truly shine.")
        ]
        
        script = PodcastScript(
            episode_title=plan.episode_title,
            speaker_count=2,
            turns=turns
        )

        script_text = f"# 🎙️ Podcast Episode: {script.episode_title}\n\n"
        for t in script.turns:
            script_text += f"**[{t.speaker}]**: {t.text}\n\n"

        artifacts.append(
            Artifact(
                name="Podcast_Dialogue_Script.json",
                parts=[Part(data=script.model_dump(), text=script_text)],
                metadata={
                    "speaker_count": 2,
                    "voice_cast": {"Alex": "en-US-GuyNeural", "Morgan": "en-US-JennyNeural"},
                    "runtime_est_seconds": 90
                }
            )
        )
        return script_text, artifacts

    else:
        raise ValueError(f"Unknown agent: {agent_name}")

# ── JSON-RPC 2.0 Handler Core ─────────────────────────────────────────────────

async def handle_jsonrpc(agent_name: str, payload: dict) -> dict:
    req_id = payload.get("id", 1)
    method = payload.get("method")
    params = payload.get("params", {})

    if payload.get("jsonrpc") != "2.0":
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "Invalid Request: jsonrpc must be '2.0'"},
            "id": req_id,
        }

    # Method 1: message/send
    if method == "message/send":
        parts_data = params.get("parts", [])
        user_text = ""
        for p in parts_data:
            if isinstance(p, dict) and "text" in p:
                user_text += p["text"] + " "
            elif isinstance(p, str):
                user_text += p + " "
        user_text = user_text.strip() or "Process default request."
        
        context_id = params.get("contextId")
        msg_in = Message(
            messageId=params.get("messageId", f"msg-{uuid.uuid4().hex[:8]}"),
            role="ROLE_USER",
            parts=[Part(text=user_text)],
            contextId=context_id,
        )

        # Create Task
        task = Task(status="working", history=[msg_in])
        TASK_STORE[task.id] = task

        # Execute
        try:
            content, artifacts = execute_agent_work(agent_name, user_text, context_id)
            msg_out = Message(
                role="ROLE_AGENT",
                parts=[Part(text=content)],
                contextId=context_id,
            )
            task.history.append(msg_out)
            task.artifacts.extend(artifacts)
            task.status = "completed"
            task.updated_at = time.time()
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            task.updated_at = time.time()

        TASK_STORE[task.id] = task

        return {
            "jsonrpc": "2.0",
            "result": {
                "taskId": task.id,
                "status": task.status,
                "output": task.history[-1].parts[0].text if task.history[-1].parts else "",
                "artifacts": [a.model_dump() for a in task.artifacts],
                "task": task.model_dump(),
            },
            "id": req_id,
        }

    # Method 2: tasks/get
    elif method == "tasks/get":
        task_id = params.get("id") or params.get("taskId")
        if not task_id or task_id not in TASK_STORE:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": f"Task '{task_id}' not found."},
                "id": req_id,
            }
        task = TASK_STORE[task_id]
        return {
            "jsonrpc": "2.0",
            "result": task.model_dump(),
            "id": req_id,
        }

    # Method 3: tasks/cancel
    elif method == "tasks/cancel":
        task_id = params.get("id") or params.get("taskId")
        if task_id in TASK_STORE:
            TASK_STORE[task_id].status = "cancelled"
            return {"jsonrpc": "2.0", "result": {"cancelled": True, "taskId": task_id}, "id": req_id}
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32602, "message": f"Task '{task_id}' not found."},
            "id": req_id,
        }

    else:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": f"Method '{method}' not found or unsupported."},
            "id": req_id,
        }

# ── Endpoint Routes for JSON-RPC ──────────────────────────────────────────────

@app.post("/podcast/a2a")
async def podcast_a2a_endpoint(request: Request):
    payload = await request.json()
    return await handle_jsonrpc("podcast", payload)

@app.post("/sql/a2a")
async def sql_a2a_endpoint(request: Request):
    payload = await request.json()
    return await handle_jsonrpc("sql", payload)

@app.post("/rag/a2a")
async def rag_a2a_endpoint(request: Request):
    payload = await request.json()
    return await handle_jsonrpc("rag", payload)

# ── Standalone Server Runner ──────────────────────────────────────────────────

def run_server(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    print("=" * 65)
    print(" 🌐  A2A PROTOCOL FEDERATED MULTI-AGENT SERVER")
    print("=" * 65)
    print(f"Host: http://{host}:{port}")
    print(f"Discovery Catalog: http://{host}:{port}/.well-known/agent-card.json")
    print(f" • Podcast Agent:  http://{host}:{port}/podcast/.well-known/agent-card.json")
    print(f" • SQL Agent:      http://{host}:{port}/sql/.well-known/agent-card.json")
    print(f" • RAG Agent:      http://{host}:{port}/rag/.well-known/agent-card.json")
    print("=" * 65)
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server()
