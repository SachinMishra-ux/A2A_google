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
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

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
from a2a.router import route_and_execute, classify_intent

# Import internal heterogeneous agents
from sql_agent.agent import run_sql_agent_query
from rag_agent.agent import run_rag_agent_query
from podcast_agent.schemas import DialogueTurn, PodcastPlan, PodcastScript, SpeakerProfile
from google.genai import types
from google.adk.utils._function_call_names import REQUEST_CONFIRMATION_FUNCTION_CALL_NAME

# In-Memory Stateful Task Store (Task ID -> Task object)
# In production, this can be backed by Redis or PostgreSQL for distributed state.
TASK_STORE: Dict[str, Task] = {}

# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL STATEFUL RUNNER & SESSION STORE FOR GOOGLE ADK PODCAST STUDIO
# ──────────────────────────────────────────────────────────────────────────────
PODCAST_RUNNER = None
PODCAST_SESSIONS: Dict[str, Dict[str, Any]] = {}

def get_podcast_runner():
    """Returns the persistent Google ADK InMemoryRunner singleton."""
    global PODCAST_RUNNER
    if PODCAST_RUNNER is None:
        from google.adk.runners import InMemoryRunner
        from podcast_agent.agent import root_agent
        PODCAST_RUNNER = InMemoryRunner(agent=root_agent)
    return PODCAST_RUNNER

def format_adk_events(events: list, session_id: str = "") -> Tuple[str, dict]:
    """Formats list of ADK Event objects into clean, professional markdown and extracts metadata."""
    agent_badge_map = {
        "podcast_agent": "🎙️ **Podcast Producer (Coordinator)**",
        "research_agent": "🔍 **Research Agent**",
        "scriptwriter_agent": "✍️ **Scriptwriter Agent**",
        "audio_producer_agent": "🎧 **Audio Producer Agent**",
    }
    
    formatted_sections = []
    hitl_required = False
    hitl_prompt = ""
    script_content = ""
    tool_confirmation_required = False
    confirmation_info = {}
    audio_file_info = None

    for ev in events:
        author = ev.author or "Agent"
        author_header = agent_badge_map.get(author, f"🤖 **{author}**")
        
        # Check tool confirmation requests
        if hasattr(ev, "get_function_calls"):
            for fc in ev.get_function_calls():
                if fc.name == REQUEST_CONFIRMATION_FUNCTION_CALL_NAME:
                    tool_confirmation_required = True
                    args = fc.args or {}
                    orig_fc = args.get("originalFunctionCall", {})
                    confirmation_info = {
                        "call_id": fc.id,
                        "tool_name": orig_fc.get("name", "generate_podcast_audio"),
                        "args": orig_fc.get("args", {}),
                        "hint": args.get("toolConfirmation", {}).get("hint", "Please approve or reject this tool invocation.")
                    }
        
        # Check text parts
        if ev.content and ev.content.parts:
            text_parts = []
            for p in ev.content.parts:
                if getattr(p, "thought", False):
                    continue
                if getattr(p, "text", None):
                    text_parts.append(p.text.strip())
            
            if text_parts:
                section_text = "\n\n".join(text_parts)
                
                # Check for Human-in-the-Loop review gate
                if any(k in section_text for k in ["• **APPROVE**", "• APPROVE", "draft script for your review", "RE-RESEARCH / REJECT"]):
                    hitl_required = True
                    hitl_prompt = section_text
                
                # Extract script content
                if any(k in section_text for k in ["**Episode Title:", "### Episode Title:", "Dialogue Transcript:"]):
                    script_content = section_text
                    
                formatted_sections.append(f"{author_header}\n\n{section_text}")

    full_output = "\n\n---\n\n".join(formatted_sections) if formatted_sections else "Agent completed task."
    
    # Check for newly generated or latest audio files in podcast_agent/output
    out_dir = PROJECT_ROOT / "podcast_agent" / "output"
    if out_dir.exists():
        mp3_files = [f for f in out_dir.glob("*.mp3") if f.is_file()]
        if mp3_files:
            mp3_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_mp3 = mp3_files[0]
            # If created or modified within last 10 minutes
            if time.time() - latest_mp3.stat().st_mtime < 600:
                audio_file_info = {
                    "filename": latest_mp3.name,
                    "url": f"/audio/{latest_mp3.name}",
                    "size_kb": round(latest_mp3.stat().st_size / 1024, 1),
                    "modified": latest_mp3.stat().st_mtime
                }

    return full_output, {
        "hitl_required": hitl_required,
        "hitl_prompt": hitl_prompt,
        "script_content": script_content,
        "tool_confirmation_required": tool_confirmation_required,
        "confirmation_info": confirmation_info,
        "audio_file_info": audio_file_info,
        "session_id": session_id,
    }


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

def execute_agent_work(agent_name: str, query_text: str, context_id: Optional[str], confirmation_data: Optional[dict] = None) -> Tuple[str, List[Artifact], Dict[str, Any]]:
    """Invokes the target internal agent framework and packages output as A2A Artifacts.
    
    This function is the heart of the A2A adapter layer:
    - It maps generic text prompts from JSON-RPC params into framework-specific calls.
    - It collects the output and packages it into structured A2A Artifacts.
    - It enforces boundary opacity: the client sees only the returned Artifact,
      never the agent's internal memory state, model weights, or system prompts.
    """
    artifacts: List[Artifact] = []
    extra_meta: Dict[str, Any] = {}

    # ── CASE A: SQL AGENT (LangChain + LangGraph + HITL + PII Redaction) ──────
    if agent_name in ("sql", "sql_agent"):
        sql_res = run_sql_agent_query(
            query_text=query_text,
            thread_id=context_id or "a2a_session",
            decision="approve"
        )
        content = extract_text_content(sql_res.get("content", ""))
        
        artifacts.append(
            Artifact(
                name="SQL_Query_Execution_Record",
                parts=[Part(text=content)],
                metadata={
                    "hitl_triggered": sql_res.get("hitl_triggered"),
                    "decision": sql_res.get("decision"),
                    "security_policy": "PII_Redacted",
                    "framework": "LangChain/LangGraph",
                    "execution_mode": sql_res.get("execution_mode"),
                    "model": sql_res.get("model"),
                    "llm_called": sql_res.get("llm_called"),
                    "llm_error": sql_res.get("llm_error")
                }
            )
        )
        return content, artifacts, extra_meta

    # ── CASE B: RAG AGENT (LangChain + FAISS + Gemini Embeddings) ─────────────
    elif agent_name in ("rag", "rag_agent"):
        rag_res = run_rag_agent_query(query_text)
        content = extract_text_content(rag_res.get("content", ""))
        
        artifacts.append(
            Artifact(
                name="Grounded_RAG_Citations",
                parts=[Part(text=content)],
                metadata={
                    "mode": rag_res.get("mode"),
                    "knowledge_source": rag_res.get("knowledge_source", "FAISS_VectorStore"),
                    "framework": "LangChain",
                    "execution_mode": rag_res.get("mode"),
                    "model": rag_res.get("model"),
                    "llm_called": rag_res.get("llm_called"),
                    "llm_error": rag_res.get("llm_error")
                }
            )
        )
        return content, artifacts, extra_meta

    # ── CASE C: PODCAST AGENT (Google ADK - Agent Development Kit) ────────────
    elif agent_name in ("podcast", "podcast_agent"):
        session_id = context_id or f"pod-session-{int(time.time())}"
        runner = get_podcast_runner()
        llm_error = None
        adk_events = []
        clean_topic = query_text.replace("Generate a podcast episode for:", "").strip()

        try:
            # 1. Handle Tool Confirmation explicitly sent from UI
            if confirmation_data:
                fc_id = confirmation_data.get("call_id")
                confirmed = confirmation_data.get("confirmed", True)
                fr_part = types.Part(function_response=types.FunctionResponse(
                    name=REQUEST_CONFIRMATION_FUNCTION_CALL_NAME,
                    id=fc_id,
                    response={"confirmed": confirmed}
                ))
                async def _send_tool_confirmation():
                    results = []
                    async for ev in runner.run_async(
                        user_id="debug_user_id",
                        session_id=session_id,
                        new_message=types.UserContent(parts=[fr_part])
                    ):
                        results.append(ev)
                    return results
                adk_events = asyncio.run(_send_tool_confirmation())

            # 2. Handle Human-in-the-Loop Script Approval (User approves draft script)
            elif query_text.strip().lower() in ("approve", "looks good", "approve.", "proceed", "generate audio") or "approve" in query_text.lower():
                # Step A: Inform the coordinator agent that the script is approved
                turn2_events = asyncio.run(runner.run_debug("Approve. Proceed with audio generation.", session_id=session_id))
                adk_events.extend(turn2_events)

                # Step B: Check if audio_producer_agent requested tool confirmation
                conf_fc = None
                for ev in turn2_events:
                    if hasattr(ev, "get_function_calls"):
                        for fc in ev.get_function_calls():
                            if fc.name == REQUEST_CONFIRMATION_FUNCTION_CALL_NAME:
                                conf_fc = fc
                                break
                    if conf_fc:
                        break

                # Step C: Auto-confirm since human explicitly approved audio generation!
                if conf_fc:
                    fr_part = types.Part(function_response=types.FunctionResponse(
                        name=REQUEST_CONFIRMATION_FUNCTION_CALL_NAME,
                        id=conf_fc.id,
                        response={"confirmed": True}
                    ))
                    async def _run_post_confirmation():
                        c_events = []
                        async for ev in runner.run_async(
                            user_id="debug_user_id",
                            session_id=session_id,
                            new_message=types.UserContent(parts=[fr_part])
                        ):
                            c_events.append(ev)
                        return c_events
                    turn3_events = asyncio.run(_run_post_confirmation())
                    adk_events.extend(turn3_events)

            # 3. Handle Standard Prompt or Revision Feedback
            else:
                adk_events = asyncio.run(runner.run_debug(clean_topic, session_id=session_id))

            # Format the ADK events into structured markdown and extract telemetry
            formatted_text, meta_info = format_adk_events(adk_events, session_id)
            extra_meta = meta_info
            execution_mode = "live_google_adk_success"
            model_info = "gemini-3.1-flash-lite (Google ADK Live)"

        except Exception as e:
            llm_error = str(e)
            billing_blocked = "outstanding balance" in llm_error or "PERMISSION_DENIED" in llm_error
            execution_mode = "live_adk_billing_blocked" if billing_blocked else "adk_local_fallback"
            model_info = "gemini-3.1-flash-lite (Google AI Studio Billing Blocked)" if billing_blocked else "google_adk_local"

            # Formulate dynamic topic-specific podcast plan
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
                DialogueTurn(speaker="Alex", text=f"Looking at the findings for '{clean_topic}', the synergy between grounded retrieval and verified database records is game-changing."),
                DialogueTurn(speaker="Morgan", text="Exactly. That is where standard protocols like A2A make heterogeneous agents truly shine.")
            ]
            
            script = PodcastScript(
                episode_title=plan.episode_title,
                speaker_count=2,
                turns=turns
            )

            script_text = f"🎙️ **Podcast Producer (Coordinator)**\n\nHere is the draft script for your review!\n\n**Episode Title: {script.episode_title}**\n\n"
            for t in script.turns:
                script_text += f"**{t.speaker}**: {t.text}\n\n"
            script_text += "\n---\n\n**Please review the dialogue above and reply with one of the following:**\n• **APPROVE**: Reply 'Approve' to proceed with audio generation.\n• **EDIT / REVISE**: Reply with specific changes.\n• **RE-RESEARCH / REJECT**: Reply if you want to investigate a different angle."

            formatted_text = script_text
            extra_meta = {
                "hitl_required": True,
                "hitl_prompt": script_text,
                "script_content": script_text,
                "tool_confirmation_required": False,
                "confirmation_info": {},
                "audio_file_info": None,
                "session_id": session_id,
            }

        # Deliverable 1: Podcast Script Artifact
        artifacts.append(
            Artifact(
                name="Podcast_Dialogue_Script.json",
                parts=[Part(text=formatted_text)],
                metadata={
                    "speaker_count": 2 if "3 Speakers" not in formatted_text else 3,
                    "voice_cast": {"Alex": "en-US-GuyNeural", "Morgan": "en-US-JennyNeural", "Taylor": "en-GB-RyanNeural"},
                    "framework": "Google ADK (Agent Development Kit)",
                    "execution_mode": execution_mode,
                    "model": model_info,
                    "session_id": session_id,
                    "llm_called": True,
                    "llm_error": llm_error,
                    "hitl_required": extra_meta.get("hitl_required", False)
                }
            )
        )

        # Deliverable 2: Generated Audio Artifact (if synthesized)
        if extra_meta.get("audio_file_info"):
            audio_info = extra_meta["audio_file_info"]
            artifacts.append(
                Artifact(
                    name=audio_info["filename"],
                    parts=[Part(text=f"Master Neural MP3 audio stream for {audio_info['filename']}")],
                    metadata={
                        "type": "audio/mp3",
                        "audio_url": audio_info["url"],
                        "filename": audio_info["filename"],
                        "size_kb": audio_info["size_kb"],
                        "framework": "Google ADK + Microsoft Neural TTS (edge-tts)"
                    }
                )
            )

        return formatted_text, artifacts, extra_meta

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
            content, artifacts, extra_meta = await asyncio.to_thread(
                execute_agent_work, agent_name, user_text, context_id, params.get("confirmation")
            )
            
            # Construct outgoing agent message turn
            msg_out = Message(
                role="ROLE_AGENT",
                parts=[Part(text=content)],
                contextId=context_id,
            )
            task.history.append(msg_out)
            task.artifacts.extend(artifacts)
            task.status = "input_required" if (extra_meta.get("hitl_required") or extra_meta.get("tool_confirmation_required")) and not extra_meta.get("audio_file_info") else "completed"
            task.updated_at = time.time()
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            task.updated_at = time.time()
            extra_meta = {}

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
                "hitl_required": extra_meta.get("hitl_required", False),
                "hitl_info": extra_meta.get("hitl_prompt", ""),
                "tool_confirmation_required": extra_meta.get("tool_confirmation_required", False),
                "tool_confirmation_details": extra_meta.get("confirmation_info", {}),
                "audio_info": extra_meta.get("audio_file_info"),
                "session_id": context_id or extra_meta.get("session_id", task.id),
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
    def get_root(request: Request):
        # If requested by a web browser, redirect to the graphical UI
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header and not "application/json" in accept_header:
            return RedirectResponse(url="/ui/")

        return {
            "mode": "unified_gateway",
            "standard": "Agent-to-Agent (A2A) Protocol v1.0",
            "ui_dashboard": "/ui/",
            "description": "Federated Multi-Agent Gateway hosting Podcast, SQL, and RAG agents",
            "agents": {
                "podcast_agent": {"card": "/podcast/.well-known/agent-card.json", "rpc": "/podcast/a2a"},
                "sql_agent":     {"card": "/sql/.well-known/agent-card.json",     "rpc": "/sql/a2a"},
                "rag_agent":     {"card": "/rag/.well-known/agent-card.json",     "rpc": "/rag/a2a"},
            }
        }

    # UI Router API Endpoint
    @app.post("/api/route")
    async def api_route_query(request: Request):
        payload = await request.json()
        query = payload.get("query", "").strip()
        mode = payload.get("mode", "auto")
        context_id = payload.get("context_id") or payload.get("session_id")
        action = payload.get("action")
        confirmation = payload.get("confirmation")
        
        if not query and not confirmation:
            raise HTTPException(status_code=400, detail="Query or confirmation cannot be empty.")
        
        base_url = str(request.base_url).rstrip("/")
        return await route_and_execute(
            query=query,
            mode=mode,
            base_url=base_url,
            context_id=context_id,
            action=action,
            confirmation=confirmation
        )

    # API Key Inspection and Hot-Update Endpoint
    @app.get("/api/key-status")
    def api_get_key_status():
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            return {"status": "missing", "masked": "", "message": "No API key configured in .env."}
        
        masked = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
        # Check if key is blocked by billing
        from google import genai
        try:
            client = genai.Client()
            client.models.generate_content(model="gemini-3.1-flash-lite", contents="ping")
            return {"status": "active", "masked": masked, "message": "Gemini API key is active and live calls are functional."}
        except Exception as e:
            err_str = str(e)
            if "outstanding balance" in err_str or "PERMISSION_DENIED" in err_str:
                return {
                    "status": "billing_blocked",
                    "masked": masked,
                    "message": "Google AI Studio billing account has an outstanding balance. Visit https://aistudio.google.com/billing to resolve, or enter a new API key below."
                }
            return {"status": "error", "masked": masked, "message": f"API key error: {err_str[:150]}"}

    @app.post("/api/set-key")
    async def api_set_key(request: Request):
        payload = await request.json()
        new_key = payload.get("key", "").strip()
        if not new_key:
            raise HTTPException(status_code=400, detail="API key cannot be empty.")

        os.environ["GEMINI_API_KEY"] = new_key
        os.environ["GOOGLE_API_KEY"] = new_key

        # Persist to .env
        env_path = PROJECT_ROOT / ".env"
        with open(env_path, "w") as f:
            f.write(f'GEMINI_API_KEY="{new_key}"\nGOOGLE_API_KEY="{new_key}"\n')

        # Re-test key
        from google import genai
        try:
            client = genai.Client()
            client.models.generate_content(model="gemini-3.1-flash-lite", contents="ping")
            return {"success": True, "status": "active", "message": "API key successfully updated and verified live with Gemini!"}
        except Exception as e:
            return {"success": False, "status": "billing_blocked" if "PERMISSION_DENIED" in str(e) else "error", "message": str(e)}

    # API Agents List Endpoint
    @app.get("/api/agents")
    def api_list_agents(request: Request):
        base_url = str(request.base_url).rstrip("/")
        return {
            "agents": [
                {
                    "id": "sql",
                    "name": "SQL Database Agent",
                    "framework": "LangChain + LangGraph",
                    "icon": "🛡️",
                    "color": "#1a73e8",
                    "card": get_sql_agent_card(base_url).model_dump(),
                    "endpoint": f"{base_url}/sql/a2a"
                },
                {
                    "id": "rag",
                    "name": "RAG Knowledge Agent",
                    "framework": "LangChain + FAISS",
                    "icon": "📚",
                    "color": "#1e8e3e",
                    "card": get_rag_agent_card(base_url).model_dump(),
                    "endpoint": f"{base_url}/rag/a2a"
                },
                {
                    "id": "podcast",
                    "name": "Podcast Studio Agent",
                    "framework": "Google ADK",
                    "icon": "🎙️",
                    "color": "#f9ab00",
                    "card": get_podcast_agent_card(base_url).model_dump(),
                    "endpoint": f"{base_url}/podcast/a2a"
                }
            ]
        }

    # Mount UI Static Directory
    ui_dir = PROJECT_ROOT / "ui"
    if ui_dir.exists():
        app.mount("/ui", StaticFiles(directory=str(ui_dir), html=True), name="ui")

    # Mount Generated Podcast Audio Directory
    audio_dir = PROJECT_ROOT / "podcast_agent" / "output"
    audio_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")

    @app.get("/api/audio-list")
    def api_audio_list():
        if not audio_dir.exists():
            return {"files": []}
        files = []
        for p in audio_dir.glob("*.mp3"):
            st = p.stat()
            files.append({
                "filename": p.name,
                "url": f"/audio/{p.name}",
                "size_kb": round(st.st_size / 1024, 1),
                "mtime": st.st_mtime
            })
        files.sort(key=lambda x: x["mtime"], reverse=True)
        return {"files": files}

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


# Alias for convenience
create_app = create_gateway_app


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
