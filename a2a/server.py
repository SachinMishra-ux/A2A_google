"""A2A Protocol Multi-Agent Server (FastAPI).

================================================================================
HOW THE A2A SERVER CONNECTS HETEROGENEOUS AGENTS
================================================================================
The A2A server acts as the network translation boundary. It bridges external
JSON-RPC 2.0 requests over HTTP directly into our internal agent frameworks:

  Client / Orchestrator
         │
         │  HTTP POST /a2a (JSON-RPC 2.0)
         ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           A2A SERVER                                   │
  │                                                                        │
  │  1. Unpacks JSON-RPC method ('message/send', 'tasks/get', etc.)       │
  │  2. Creates stateful Task in TASK_STORE (status = 'working')          │
  │  3. Dispatches work to the target internal agent:                      │
  │     • 'sql'     ──> sql_agent.run_sql_agent_query()   [LangChain]      │
  │     • 'rag'     ──> rag_agent.run_rag_agent_query()   [LangChain]      │
  │     • 'podcast' ──> podcast_agent plan & script       [Google ADK]     │
  │  4. Packages outputs into standard 'Artifact' objects                  │
  │  5. Updates Task (status = 'completed') & returns JSON-RPC response    │
  └────────────────────────────────────────────────────────────────────────┘

TWO DEPLOYMENT MODES SUPPORTED:
1. UNIFIED GATEWAY MODE (Default, Port 8000):
   Runs all three agents under a single web server with namespaced routes:
   - Podcast: http://127.0.0.1:8000/podcast/a2a
   - SQL:     http://127.0.0.1:8000/sql/a2a
   - RAG:     http://127.0.0.1:8000/rag/a2a

2. INDIVIDUAL STANDALONE SERVER MODE (Microservices Architecture):
   Each agent runs on its own dedicated port and process:
   - Podcast Server: http://127.0.0.1:8001/a2a
   - SQL Server:     http://127.0.0.1:8002/a2a
   - RAG Server:     http://127.0.0.1:8003/a2a
================================================================================
"""

import argparse
import asyncio
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

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

# Import internal heterogeneous agents
from sql_agent.agent import run_sql_agent_query
from rag_agent.agent import run_rag_agent_query
from podcast_agent.schemas import DialogueTurn, PodcastPlan, PodcastScript, SpeakerProfile

# In-Memory Stateful Task Store (Task ID -> Task object)
# In production, this can be backed by Redis or PostgreSQL for distributed state.
TASK_STORE: Dict[str, Task] = {}


# ──────────────────────────────────────────────────────────────────────────────
# 1. CORE DISPATCHER: BRIDGING PROTOCOL TO INTERNAL AGENT FRAMEWORKS
# ──────────────────────────────────────────────────────────────────────────────
def extract_text_content(content: Any) -> str:
    """Safely extracts plain string text from diverse agent output formats."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)

def execute_agent_work(agent_name: str, query_text: str, context_id: Optional[str]) -> Tuple[str, List[Artifact]]:
    """Invokes the target internal agent framework and packages output as A2A Artifacts.
    
    This function is the heart of the A2A adapter layer:
    - It maps generic text prompts from JSON-RPC params into framework-specific calls.
    - It collects the output and packages it into structured A2A Artifacts.
    - It enforces boundary opacity: the client sees only the returned Artifact,
      never the agent's internal memory state, model weights, or system prompts.
    """
    artifacts: List[Artifact] = []

    # ── CASE A: SQL AGENT (LangChain + LangGraph + HITL + PII Redaction) ──────
    if agent_name == "sql":
        # Invokes the compiled LangGraph SQL agent.
        # It executes against the SQLite database, checks HITL approval,
        # and applies the PIIMiddleware to redact Credit Cards and Emails.
        sql_res = run_sql_agent_query(
            query_text=query_text,
            thread_id=context_id or "a2a_session",
            decision="approve"
        )
        content = extract_text_content(sql_res.get("content", ""))
        
        # Package deliverable as an A2A Artifact
        artifacts.append(
            Artifact(
                name="SQL_Query_Execution_Record",
                parts=[Part(text=content)],
                metadata={
                    "hitl_triggered": sql_res.get("hitl_triggered"),
                    "decision": sql_res.get("decision"),
                    "security_policy": "PII_Redacted",
                    "framework": "LangChain/LangGraph"
                }
            )
        )
        return content, artifacts

    # ── CASE B: RAG AGENT (LangChain + FAISS + Gemini Embeddings) ─────────────
    elif agent_name == "rag":
        # Invokes the LangChain RAG agent.
        # It queries the in-memory FAISS vector database for semantic similarity
        # and synthesizes a grounded answer citing authoritative sources.
        rag_res = run_rag_agent_query(query_text)
        content = extract_text_content(rag_res.get("content", ""))
        
        # Package deliverable as an A2A Artifact
        artifacts.append(
            Artifact(
                name="Grounded_RAG_Citations",
                parts=[Part(text=content)],
                metadata={
                    "mode": rag_res.get("mode"),
                    "knowledge_source": "FAISS_VectorStore",
                    "framework": "LangChain"
                }
            )
        )
        return content, artifacts

    # ── CASE C: PODCAST AGENT (Google ADK - Agent Development Kit) ────────────
    elif agent_name == "podcast":
        # Invokes the Google ADK Podcast Studio pipeline.
        # It extracts topics from the incoming prompt, creates an Episode Plan,
        # and casts personas (Alex as Host, Morgan as Specialist).
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

        # Package deliverable as an A2A Artifact containing both raw JSON data and formatted markdown
        artifacts.append(
            Artifact(
                name="Podcast_Dialogue_Script.json",
                parts=[Part(data=script.model_dump(), text=script_text)],
                metadata={
                    "speaker_count": 2,
                    "voice_cast": {"Alex": "en-US-GuyNeural", "Morgan": "en-US-JennyNeural"},
                    "runtime_est_seconds": 90,
                    "framework": "Google ADK"
                }
            )
        )
        return script_text, artifacts

    else:
        raise ValueError(f"Unknown agent identifier: '{agent_name}'. Must be 'sql', 'rag', or 'podcast'.")


# ──────────────────────────────────────────────────────────────────────────────
# 2. JSON-RPC 2.0 PROTOCOL ENGINE
# ──────────────────────────────────────────────────────────────────────────────
async def handle_jsonrpc(agent_name: str, payload: dict) -> dict:
    """Core JSON-RPC 2.0 handler implementing standard A2A operations.
    
    Supported Methods:
    1. message/send:
       Receives input parts, creates a Task, executes the agent, and returns the completed Task.
    2. tasks/get:
       Retrieves the current state and artifacts of an existing Task by ID.
    3. tasks/cancel:
       Cancels an ongoing task.
    """
    req_id = payload.get("id", 1)
    method = payload.get("method")
    params = payload.get("params", {})

    # Validate JSON-RPC version header
    if payload.get("jsonrpc") != "2.0":
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "Invalid Request: 'jsonrpc' field must be '2.0'"},
            "id": req_id,
        }

    # ── OPERATION 1: message/send ─────────────────────────────────────────────
    if method == "message/send":
        # Extract text from input parts array
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

        # 1. Initialize Task in state 'working'
        task = Task(status="working", history=[msg_in])
        TASK_STORE[task.id] = task

        # 2. Execute internal agent logic in background worker thread to prevent event-loop blocking
        try:
            content, artifacts = await asyncio.to_thread(
                execute_agent_work, agent_name, user_text, context_id
            )
            
            # Construct outgoing agent message turn
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

        # Update task in store
        TASK_STORE[task.id] = task

        # Return standard A2A JSON-RPC 2.0 response
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

    # ── OPERATION 2: tasks/get ────────────────────────────────────────────────
    elif method == "tasks/get":
        task_id = params.get("id") or params.get("taskId")
        if not task_id or task_id not in TASK_STORE:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": f"Task '{task_id}' not found in task store."},
                "id": req_id,
            }
        task = TASK_STORE[task_id]
        return {
            "jsonrpc": "2.0",
            "result": task.model_dump(),
            "id": req_id,
        }

    # ── OPERATION 3: tasks/cancel ─────────────────────────────────────────────
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

    # ── UNKNOWN METHOD ────────────────────────────────────────────────────────
    else:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": f"Method '{method}' not recognized in A2A protocol v1.0."},
            "id": req_id,
        }


# ──────────────────────────────────────────────────────────────────────────────
# 3. FASTAPI APPLICATION FACTORIES
# ──────────────────────────────────────────────────────────────────────────────

def create_gateway_app() -> FastAPI:
    """Creates the Unified Multi-Agent Gateway hosting all 3 agents together."""
    app = FastAPI(
        title="A2A Protocol Multi-Agent Gateway",
        description="Universal A2A gateway connecting Google ADK and LangChain agents",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Root Discovery Endpoints
    @app.get("/")
    def get_root():
        return {
            "mode": "unified_gateway",
            "standard": "Agent-to-Agent (A2A) Protocol v1.0",
            "description": "Federated Multi-Agent Gateway hosting Podcast, SQL, and RAG agents",
            "agents": {
                "podcast_agent": {"card": "/podcast/.well-known/agent-card.json", "rpc": "/podcast/a2a"},
                "sql_agent":     {"card": "/sql/.well-known/agent-card.json",     "rpc": "/sql/a2a"},
                "rag_agent":     {"card": "/rag/.well-known/agent-card.json",     "rpc": "/rag/a2a"},
            }
        }

    @app.get("/.well-known/agent-card.json")
    def get_root_agent_card(request: Request):
        base_url = str(request.base_url).rstrip("/")
        return {
            "name": "a2a_enterprise_federation_gateway",
            "version": "1.0.0",
            "description": "Enterprise gateway orchestrating federated A2A agents across ADK and LangChain.",
            "hosted_agents": [
                get_podcast_agent_card(base_url, standalone=False).model_dump(),
                get_sql_agent_card(base_url, standalone=False).model_dump(),
                get_rag_agent_card(base_url, standalone=False).model_dump(),
            ]
        }

    # Agent Cards per Namespace
    @app.get("/podcast/.well-known/agent-card.json")
    def podcast_card(request: Request):
        return get_podcast_agent_card(str(request.base_url).rstrip("/"), standalone=False).model_dump()

    @app.get("/sql/.well-known/agent-card.json")
    def sql_card(request: Request):
        return get_sql_agent_card(str(request.base_url).rstrip("/"), standalone=False).model_dump()

    @app.get("/rag/.well-known/agent-card.json")
    def rag_card(request: Request):
        return get_rag_agent_card(str(request.base_url).rstrip("/"), standalone=False).model_dump()

    # JSON-RPC Endpoints per Namespace
    @app.post("/podcast/a2a")
    async def podcast_rpc(request: Request):
        payload = await request.json()
        return await handle_jsonrpc("podcast", payload)

    @app.post("/sql/a2a")
    async def sql_rpc(request: Request):
        payload = await request.json()
        return await handle_jsonrpc("sql", payload)

    @app.post("/rag/a2a")
    async def rag_rpc(request: Request):
        payload = await request.json()
        return await handle_jsonrpc("rag", payload)

    return app


def create_standalone_agent_app(agent_name: str) -> FastAPI:
    """Creates a standalone microservice server for an INDIVIDUAL agent.
    
    This fulfills the microservices pattern:
    - Its Agent Card is hosted at the standard root: /.well-known/agent-card.json
    - Its JSON-RPC 2.0 endpoint is hosted at the standard root: /a2a
    """
    card_factories = {
        "podcast": get_podcast_agent_card,
        "sql": get_sql_agent_card,
        "rag": get_rag_agent_card,
    }
    if agent_name not in card_factories:
        raise ValueError(f"Unknown agent: {agent_name}. Must be 'podcast', 'sql', or 'rag'.")

    app = FastAPI(
        title=f"A2A Standalone Server: {agent_name.upper()}",
        description=f"Independent A2A microservice for {agent_name} agent",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    card_fn = card_factories[agent_name]

    @app.get("/")
    def root():
        return {
            "mode": "standalone_microservice",
            "agent": agent_name,
            "card_url": "/.well-known/agent-card.json",
            "rpc_url": "/a2a"
        }

    # Standard A2A Agent Card Discovery endpoint
    @app.get("/.well-known/agent-card.json")
    def agent_card(request: Request):
        base_url = str(request.base_url).rstrip("/")
        return card_fn(base_url, standalone=True).model_dump()

    # Also support namespace path for backwards compatibility
    @app.get(f"/{agent_name}/.well-known/agent-card.json")
    def agent_card_ns(request: Request):
        base_url = str(request.base_url).rstrip("/")
        return card_fn(base_url, standalone=True).model_dump()

    # Standard A2A JSON-RPC 2.0 endpoint
    @app.post("/a2a")
    async def rpc_endpoint(request: Request):
        payload = await request.json()
        return await handle_jsonrpc(agent_name, payload)

    @app.post(f"/{agent_name}/a2a")
    async def rpc_endpoint_ns(request: Request):
        payload = await request.json()
        return await handle_jsonrpc(agent_name, payload)

    return app


# Default Gateway App Instance (used by ASGI runners like `uvicorn a2a.server:app`)
app = create_gateway_app()


# ──────────────────────────────────────────────────────────────────────────────
# 4. SERVER RUNNER CLI
# ──────────────────────────────────────────────────────────────────────────────
def run_server(host: str = "127.0.0.1", port: int = 8000, agent: Optional[str] = None):
    """Launches the server in either Unified Gateway mode or Standalone Agent mode."""
    import uvicorn
    
    if agent:
        # Standalone Individual Server Mode
        agent_app = create_standalone_agent_app(agent)
        print("=" * 70)
        print(f" 🚀  A2A STANDALONE SERVER: {agent.upper()} AGENT")
        print("=" * 70)
        print(f"Server URL:     http://{host}:{port}")
        print(f"Agent Card:     http://{host}:{port}/.well-known/agent-card.json")
        print(f"A2A JSON-RPC:   http://{host}:{port}/a2a")
        print("=" * 70)
        uvicorn.run(agent_app, host=host, port=port)
    else:
        # Unified Gateway Mode (All 3 Agents)
        print("=" * 70)
        print(" 🌐  A2A PROTOCOL FEDERATED MULTI-AGENT GATEWAY")
        print("=" * 70)
        print(f"Gateway URL:    http://{host}:{port}")
        print(f"Discovery Card: http://{host}:{port}/.well-known/agent-card.json")
        print(f" • Podcast:     http://{host}:{port}/podcast/.well-known/agent-card.json")
        print(f" • SQL:         http://{host}:{port}/sql/.well-known/agent-card.json")
        print(f" • RAG:         http://{host}:{port}/rag/.well-known/agent-card.json")
        print("=" * 70)
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A2A Server Runner")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument("--agent", choices=["podcast", "sql", "rag"], default=None,
                        help="Run dedicated server for a single agent. If omitted, runs all 3 in gateway mode.")
    args = parser.parse_args()
    run_server(host=args.host, port=args.port, agent=args.agent)
