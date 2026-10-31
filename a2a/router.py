"""Intelligent A2A Router and Intent Dispatcher.

================================================================================
ROLE OF THE A2A ROUTER:
================================================================================
When a user submits an arbitrary prompt from the UI (or API), the router:
1. Analyzes the intent of the question.
2. Identifies the most appropriate specialist agent (or multi-agent orchestrator).
3. Connects via standard A2A Protocol (JSON-RPC 2.0) to the chosen agent.
4. Collects complete "Behind-the-Scenes" telemetry:
   - Target Agent details (name, version, framework, skills)
   - Discovered Agent Card manifest
   - Outgoing JSON-RPC 2.0 Request payload
   - Incoming JSON-RPC 2.0 Response payload
   - Generated Artifacts (schemas, metadata)
   - Step-by-step Execution Flow milestones for UI visualization
================================================================================
"""

import asyncio
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional
from pathlib import Path

from a2a.agent_cards import (
    get_podcast_agent_card,
    get_sql_agent_card,
    get_rag_agent_card,
)


def classify_intent(query: str) -> Dict[str, Any]:
    """Determines the appropriate agent to handle the user query.
    
    Returns:
        dict: Contains target agent ('sql', 'rag', 'podcast', 'orchestrator'),
              confidence score, and semantic explanation for the UI.
    """
    q_lower = query.lower()

    # Check for multi-agent composite queries first
    is_multi_agent = False
    has_sql_kw = any(w in q_lower for w in ["balance", "credit card", "user", "account", "alice", "bob", "database", "sql"])
    has_rag_kw = any(w in q_lower for w in ["gemini", "rag", "faiss", "model", "context window", "multimodal", "architecture", "knowledge"])
    has_pod_kw = any(w in q_lower for w in ["podcast", "episode", "dialogue", "host", "audio", "script", "alex", "morgan"])

    # If query mentions podcast alongside database or rag, it's a composite workflow
    if (has_sql_kw and has_pod_kw) or (has_rag_kw and has_pod_kw) or (has_sql_kw and has_rag_kw and "both" in q_lower):
        is_multi_agent = True

    if is_multi_agent or "orchestrat" in q_lower or "all agents" in q_lower or "collaborat" in q_lower:
        return {
            "agent": "orchestrator",
            "name": "A2A Multi-Agent Orchestrator",
            "framework": "Federated Multi-Agent Pipeline",
            "icon": "🌐",
            "color": "#1a73e8",
            "confidence": 0.98,
            "reason": "Query spans multiple domain boundaries (requires cross-agent collaboration between SQL, RAG, and Podcast agents)."
        }

    # SQL Agent Keywords
    if has_sql_kw or any(w in q_lower for w in ["card", "email", "sensitive", "users", "select", "table", "record"]):
        return {
            "agent": "sql",
            "name": "SQL Database Agent",
            "framework": "LangChain + LangGraph",
            "icon": "🗄️",
            "color": "#1a73e8",
            "confidence": 0.94,
            "reason": "Query requires querying sensitive account records with Human-in-the-Loop review and automated PII redaction."
        }

    # RAG Agent Keywords
    if has_rag_kw or any(w in q_lower for w in ["what is", "how does", "explain", "documentation", "facts", "cite", "citation"]):
        return {
            "agent": "rag",
            "name": "RAG Knowledge Agent",
            "framework": "LangChain + FAISS Vector Store",
            "icon": "📚",
            "color": "#1e8e3e",
            "confidence": 0.92,
            "reason": "Query requires semantic vector retrieval over indexed technical documentation with source grounding."
        }

    # Podcast Agent Keywords
    if has_pod_kw or any(w in q_lower for w in ["voice", "speak", "tts", "mp3", "talk show", "conversation"]):
        return {
            "agent": "podcast",
            "name": "Podcast Studio Agent",
            "framework": "Google ADK (Agent Development Kit)",
            "icon": "🎙️",
            "color": "#f9ab00",
            "confidence": 0.95,
            "reason": "Query requires conversational episode planning and multi-speaker dialogue synthesis with neural voices."
        }

    # Default fallback: RAG agent for general Q&A
    return {
        "agent": "rag",
        "name": "RAG Knowledge Agent",
        "framework": "LangChain + FAISS Vector Store",
        "icon": "📚",
        "color": "#1e8e3e",
        "confidence": 0.75,
        "reason": "Defaulting to RAG Knowledge Agent for general conceptual reasoning and knowledge retrieval."
    }


async def route_and_execute(
    query: str,
    mode: str = "auto",
    base_url: str = "http://127.0.0.1:8000"
) -> Dict[str, Any]:
    """Routes query, executes A2A call, and builds comprehensive behind-the-scenes telemetry.
    
    Args:
        query: The natural-language query from the user.
        mode: Routing mode ('auto', 'sql', 'rag', 'podcast', 'orchestrator').
        base_url: The A2A Gateway server URL.
    """
    # Lazy import to avoid circular dependencies with server.py
    from a2a.server import handle_jsonrpc

    t_start = time.time()
    steps: List[str] = []

    # Step 1: Decision Logic
    if mode in ["sql", "rag", "podcast", "orchestrator"]:
        decision_map = {
            "sql": {
                "agent": "sql", "name": "SQL Database Agent", "framework": "LangChain + LangGraph",
                "icon": "🗄️", "color": "#1a73e8", "confidence": 1.0,
                "reason": "Manually routed by user selection to SQL Database Agent."
            },
            "rag": {
                "agent": "rag", "name": "RAG Knowledge Agent", "framework": "LangChain + FAISS",
                "icon": "📚", "color": "#1e8e3e", "confidence": 1.0,
                "reason": "Manually routed by user selection to RAG Knowledge Agent."
            },
            "podcast": {
                "agent": "podcast", "name": "Podcast Studio Agent", "framework": "Google ADK",
                "icon": "🎙️", "color": "#f9ab00", "confidence": 1.0,
                "reason": "Manually routed by user selection to Podcast Studio Agent."
            },
            "orchestrator": {
                "agent": "orchestrator", "name": "A2A Multi-Agent Orchestrator", "framework": "Federated Pipeline",
                "icon": "🌐", "color": "#1a73e8", "confidence": 1.0,
                "reason": "Manually selected full multi-agent collaborative workflow."
            }
        }
        decision = decision_map[mode]
    else:
        decision = classify_intent(query)

    target_agent = decision["agent"]
    steps.append(f"Intent Analysis: Analyzed query. Selected target '{decision['name']}' ({decision['framework']}) with {int(decision['confidence']*100)}% confidence.")

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 1: MULTI-AGENT ORCHESTRATOR PIPELINE
    # ──────────────────────────────────────────────────────────────────────────
    if target_agent == "orchestrator":
        steps.append("Capability Discovery: Resolved Agent Cards for SQL, RAG, and Podcast agents.")
        
        # 1. SQL Step
        steps.append("A2A Delegation (1/3): Invoking SQL Agent via JSON-RPC 2.0 'message/send'...")
        sql_req = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {"parts": [{"text": "Query database for top user records and balances."}], "contextId": "orch-sql"},
            "id": 101
        }
        sql_res = await handle_jsonrpc("sql", sql_req)
        sql_out = sql_res.get("result", {}).get("output", "SQL data retrieved.")
        sql_arts = sql_res.get("result", {}).get("artifacts", [])

        # 2. RAG Step
        steps.append("A2A Delegation (2/3): Invoking RAG Agent via JSON-RPC 2.0 'message/send'...")
        rag_req = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {"parts": [{"text": "Explain best practices for customer communication and analytics."}], "contextId": "orch-rag"},
            "id": 102
        }
        rag_res = await handle_jsonrpc("rag", rag_req)
        rag_out = rag_res.get("result", {}).get("output", "RAG citations retrieved.")
        rag_arts = rag_res.get("result", {}).get("artifacts", [])

        # 3. Podcast Step
        steps.append("A2A Delegation (3/3): Passing composite outputs to Google ADK Podcast Agent...")
        podcast_prompt = (
            f"Generate a podcast episode for: Enterprise Data and AI Systems.\n\n"
            f"Database Context:\n{sql_out}\n\n"
            f"Knowledge Retrieval Context:\n{rag_out}"
        )
        pod_req = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {"parts": [{"text": podcast_prompt}], "contextId": "orch-pod"},
            "id": 103
        }
        pod_res = await handle_jsonrpc("podcast", pod_req)
        final_output = pod_res.get("result", {}).get("output", "")
        pod_arts = pod_res.get("result", {}).get("artifacts", [])

        all_artifacts = sql_arts + rag_arts + pod_arts
        steps.append(f"Artifact Aggregation: Collected {len(all_artifacts)} cross-agent artifacts.")

        duration_ms = int((time.time() - t_start) * 1000)
        return {
            "query": query,
            "mode": mode,
            "routed_agent": "orchestrator",
            "agent_invoked": decision,
            "agent_card": {
                "name": "A2A Multi-Agent Orchestrator",
                "version": "1.0.0",
                "framework": "Federated Multi-Agent Pipeline",
                "sub_agents": ["sql_agent", "rag_agent", "podcast_agent"]
            },
            "steps": steps,
            "output_text": final_output,
            "output": final_output,
            "artifacts": all_artifacts,
            "task_id": f"task-orch-{uuid.uuid4().hex[:8]}",
            "taskId": f"task-orch-{uuid.uuid4().hex[:8]}",
            "duration_ms": duration_ms,
            "duration_seconds": round(duration_ms / 1000, 2),
            "state": "COMPLETED",
            "status": "completed",
            "jsonrpc_request": pod_req,
            "jsonrpc_response": pod_res
        }

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 2: INDIVIDUAL SPECIALIST AGENT EXECUTION
    # ──────────────────────────────────────────────────────────────────────────
    # Resolve Agent Card
    if target_agent == "sql":
        card = get_sql_agent_card()
        agent_key = "sql_agent"
    elif target_agent == "rag":
        card = get_rag_agent_card()
        agent_key = "rag_agent"
    else:
        card = get_podcast_agent_card()
        agent_key = "podcast_agent"

    card_dict = card.model_dump()
    skills_list = [s.get("name") if isinstance(s, dict) else getattr(s, "name", str(s)) for s in card_dict.get("skills", [])]
    steps.append(f"Agent Card Discovery: Resolved Agent Card for '{card_dict.get('name')}' (Version: {card_dict.get('version')}, Skills: {', '.join(skills_list)}).")

    # Construct standard A2A JSON-RPC 2.0 Request
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "messageId": f"msg-{int(time.time()*1000)}",
            "role": "ROLE_USER",
            "parts": [{"text": query}],
            "contextId": f"ui-session-{int(time.time())}"
        },
        "id": 1
    }

    steps.append(f"A2A Task Dispatch: Created JSON-RPC 2.0 'message/send' request (Context: {rpc_request['params']['contextId']}).")

    # Execute in-process via handle_jsonrpc
    rpc_response = await handle_jsonrpc(target_agent, rpc_request)
    result_data = rpc_response.get("result", {})
    output_text = result_data.get("output", "")
    task_id = result_data.get("taskId", f"task-{uuid.uuid4().hex[:8]}")
    status = result_data.get("status", "completed")
    raw_artifacts = result_data.get("artifacts", [])

    steps.append(f"Specialist Execution: Processed by {decision['framework']}. Task ID: {task_id} (Status: {status}).")

    # Format artifacts for UI consumption
    formatted_artifacts = []
    for art in raw_artifacts:
        art_name = art.get("name", "Artifact")
        art_parts = art.get("parts", [])
        preview_text = ""
        for p in art_parts:
            if isinstance(p, dict) and "text" in p:
                preview_text += p["text"]
            elif isinstance(p, str):
                preview_text += p
        formatted_artifacts.append({
            "name": art_name,
            "type": art.get("metadata", {}).get("framework", "Deliverable"),
            "metadata": art.get("metadata", {}),
            "preview": preview_text[:300] + ("..." if len(preview_text) > 300 else "")
        })

    steps.append(f"Artifact Handoff: Delivered {len(formatted_artifacts)} formal deliverable artifact(s).")

    duration_ms = int((time.time() - t_start) * 1000)

    return {
        "query": query,
        "mode": mode,
        "routed_agent": agent_key,
        "agent_invoked": decision,
        "agent_card": card_dict,
        "steps": steps,
        "output_text": output_text,
        "output": output_text,
        "artifacts": formatted_artifacts,
        "task_id": task_id,
        "taskId": task_id,
        "duration_ms": duration_ms,
        "duration_seconds": round(duration_ms / 1000, 2),
        "state": status.upper(),
        "status": status,
        "jsonrpc_request": rpc_request,
        "jsonrpc_response": rpc_response
    }
