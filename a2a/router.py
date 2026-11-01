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


def evaluate_agent_cards(query: str) -> Dict[str, Any]:
    """Evaluates the incoming user query against all registered A2A Agent Cards.
    
    This function demonstrates the core routing mechanism of Google's A2A Protocol:
    1. Reads Agent Cards from discovery metadata (names, descriptions, and advertised skills).
    2. Performs semantic capability matching against the user's mission.
    3. Calculates transparent match scores and returns candidate evaluations.
    """
    q_lower = query.lower()

    # 1. SQL Agent Card Evaluation
    sql_card = get_sql_agent_card()
    sql_skills = [s.name for s in sql_card.skills]
    sql_terms = ["balance", "credit card", "user", "account", "alice", "bob", "database", "sql", "select", "table", "record", "pii", "redact"]
    sql_matches = [w for w in sql_terms if w in q_lower]
    sql_score = min(95, 20 + len(sql_matches) * 25) if sql_matches else 5
    sql_eval = {
        "agent_id": "sql",
        "name": sql_card.name,
        "framework": "LangChain + LangGraph",
        "icon": "🗄️",
        "color": "#1a73e8",
        "advertised_skills": sql_skills,
        "match_score": sql_score,
        "matched_signals": sql_matches,
        "reason": f"Matches database records and sensitive account lookups ({', '.join(sql_matches)})" if sql_matches else "No database or user record keywords detected."
    }

    # 2. RAG Agent Card Evaluation
    rag_card = get_rag_agent_card()
    rag_skills = [s.name for s in rag_card.skills]
    rag_terms = ["gemini", "rag", "faiss", "model", "context window", "multimodal", "architecture", "knowledge", "explain", "what is", "how does", "documentation", "facts", "cite"]
    rag_matches = [w for w in rag_terms if w in q_lower]
    rag_score = min(95, 20 + len(rag_matches) * 20) if rag_matches else 10
    rag_eval = {
        "agent_id": "rag",
        "name": rag_card.name,
        "framework": "LangChain + FAISS Vector Store",
        "icon": "📚",
        "color": "#1e8e3e",
        "advertised_skills": rag_skills,
        "match_score": rag_score,
        "matched_signals": rag_matches,
        "reason": f"Matches semantic vector retrieval and technical documentation ({', '.join(rag_matches)})" if rag_matches else "No documentation or conceptual Q&A keywords detected."
    }

    # 3. Podcast Agent Card Evaluation
    pod_card = get_podcast_agent_card()
    pod_skills = [s.name for s in pod_card.skills]
    pod_terms = ["podcast", "episode", "dialogue", "host", "audio", "script", "alex", "morgan", "voice", "speak", "tts", "mp3", "talk show", "conversation"]
    pod_matches = [w for w in pod_terms if w in q_lower]
    pod_score = min(95, 25 + len(pod_matches) * 25) if pod_matches else 5
    pod_eval = {
        "agent_id": "podcast",
        "name": pod_card.name,
        "framework": "Google ADK (Agent Development Kit)",
        "icon": "🎙️",
        "color": "#f9ab00",
        "advertised_skills": pod_skills,
        "match_score": pod_score,
        "matched_signals": pod_matches,
        "reason": f"Matches spoken dialogue synthesis and episode audio production ({', '.join(pod_matches)})" if pod_matches else "No audio or podcast keywords detected."
    }

    # 4. Composite Multi-Agent Orchestrator Evaluation
    has_sql = len(sql_matches) > 0
    has_rag = len(rag_matches) > 0
    has_pod = len(pod_matches) > 0

    # Explicit podcast intent: requests that specifically ask to write/generate a podcast script or episode
    is_podcast_request = (
        ("podcast" in q_lower and ("script" in q_lower or "episode" in q_lower or "generate" in q_lower or "create" in q_lower))
        or q_lower.startswith("podcast:")
        or ("alex" in q_lower and "morgan" in q_lower)
    )

    # Composite mission requires combining SQL with Podcast, or explicit orchestration keywords
    is_composite = (
        (has_sql and has_pod)
        or (has_sql and has_rag and "both" in q_lower)
        or any(w in q_lower for w in ["orchestrat", "collaborat", "all agents", "pipeline", "cross-agent"])
    ) and not (is_podcast_request and not has_sql and not any(w in q_lower for w in ["orchestrat", "pipeline"]))

    orch_score = 98 if is_composite else (max(sql_score, rag_score, pod_score) - 30 if is_composite else 15)
    orch_eval = {
        "agent_id": "orchestrator",
        "name": "A2A Multi-Agent Orchestrator",
        "framework": "Federated Multi-Agent Pipeline",
        "icon": "🌐",
        "color": "#8430ce",
        "advertised_skills": ["Cross-Domain Task Delegation", "Dynamic Sub-Agent Synthesis", "Unified Audit Reporting"],
        "match_score": orch_score,
        "matched_signals": ["composite_cross_domain_mission"] if is_composite else [],
        "reason": "Mission crosses organizational agent boundaries; requires chaining SQL + RAG + Podcast agents." if is_composite else "Query is focused on a single domain; orchestrator unnecessary."
    }

    candidates = [sql_eval, rag_eval, pod_eval, orch_eval]
    
    # Pick winner
    if is_composite:
        winner = orch_eval
    else:
        # Sort by match score descending
        ranked = sorted(candidates[:3], key=lambda x: x["match_score"], reverse=True)
        winner = ranked[0]
        if winner["match_score"] < 20:
            # Fallback to RAG
            winner = rag_eval

    # Mark status
    for c in candidates:
        c["status"] = "Selected (Winner)" if c["agent_id"] == winner["agent_id"] else "Candidate Evaluated"

    return {
        "winner": {
            "agent": winner["agent_id"],
            "name": winner["name"],
            "framework": winner["framework"],
            "icon": winner["icon"],
            "color": winner["color"],
            "confidence": round(winner["match_score"] / 100.0, 2),
            "reason": winner["reason"],
            "skills": winner["advertised_skills"]
        },
        "candidates": candidates
    }


def classify_intent(query: str) -> Dict[str, Any]:
    """Determines the appropriate agent by evaluating Agent Cards."""
    eval_res = evaluate_agent_cards(query)
    return eval_res["winner"]


async def route_and_execute(
    query: str,
    mode: str = "auto",
    base_url: str = "http://127.0.0.1:8000",
    context_id: Optional[str] = None,
    action: Optional[str] = None,
    confirmation: Optional[dict] = None
) -> Dict[str, Any]:
    """Routes query, executes A2A call, and builds comprehensive behind-the-scenes telemetry.
    
    Args:
        query: The natural-language query from the user.
        mode: Routing mode ('auto', 'sql', 'rag', 'podcast', 'orchestrator').
        base_url: The A2A Gateway server URL.
        context_id: Stateful session context identifier.
        action: Optional HITL action trigger ('approve', 'revise', 'tool_confirm').
        confirmation: Optional tool confirmation payload.
    """
    # Lazy import to avoid circular dependencies with server.py
    from a2a.server import handle_jsonrpc

    t_start = time.time()
    steps: List[str] = []

    # Evaluate all Agent Cards against query
    card_eval = evaluate_agent_cards(query)
    candidates = card_eval["candidates"]

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
                "icon": "🌐", "color": "#8430ce", "confidence": 1.0,
                "reason": "Manually selected full multi-agent collaborative workflow."
            }
        }
        decision = decision_map[mode]
    else:
        decision = card_eval["winner"]

    target_agent = decision["agent"]
    steps.append(f"Intent & Capability Matching: Evaluated 4 Agent Cards. Selected '{decision['name']}' ({decision['framework']}) with {int(decision['confidence']*100)}% match confidence.")

    # ──────────────────────────────────────────────────────────────────────────
    # CASE 1: MULTI-AGENT ORCHESTRATOR PIPELINE
    # ──────────────────────────────────────────────────────────────────────────
    if target_agent == "orchestrator":
        steps.append("Capability Discovery: Resolved Agent Cards for SQL, RAG, and Podcast agents.")
        orch_session = context_id or f"orch-{uuid.uuid4().hex[:8]}"
        
        # 1. SQL Step
        steps.append("A2A Delegation (1/3): Invoking SQL Agent via JSON-RPC 2.0 'message/send'...")
        sql_req = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {"parts": [{"text": "Query database for top user records and balances."}], "contextId": f"{orch_session}-sql"},
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
            "params": {"parts": [{"text": "Explain best practices for customer communication and analytics."}], "contextId": f"{orch_session}-rag"},
            "id": 102
        }
        rag_res = await handle_jsonrpc("rag", rag_req)
        rag_out = rag_res.get("result", {}).get("output", "RAG citations retrieved.")
        rag_arts = rag_res.get("result", {}).get("artifacts", [])

        # 3. Podcast Step
        steps.append("A2A Delegation (3/3): Passing composite outputs to Google ADK Podcast Agent...")
        podcast_topic = query.strip() or "Enterprise Data and AI Systems"
        podcast_prompt = (
            f"Generate a podcast episode for: {podcast_topic}\n\n"
            f"Database Context:\n{sql_out}\n\n"
            f"Knowledge Retrieval Context:\n{rag_out}"
        )
        pod_req = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "parts": [{"text": podcast_prompt}],
                "contextId": orch_session,
                "confirmation": confirmation
            },
            "id": 103
        }
        pod_res = await handle_jsonrpc("podcast", pod_req)
        pod_result = pod_res.get("result", {})
        final_output = pod_result.get("output", "")
        pod_arts = pod_result.get("artifacts", [])

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
            "card_evaluations": candidates,
            "steps": steps,
            "output_text": final_output,
            "output": final_output,
            "artifacts": all_artifacts,
            "task_id": orch_session,
            "taskId": orch_session,
            "session_id": orch_session,
            "hitl_required": pod_result.get("hitl_required", False),
            "hitl_info": pod_result.get("hitl_info", ""),
            "tool_confirmation_required": pod_result.get("tool_confirmation_required", False),
            "tool_confirmation_details": pod_result.get("tool_confirmation_details", {}),
            "audio_info": pod_result.get("audio_info"),
            "duration_ms": duration_ms,
            "duration_seconds": round(duration_ms / 1000, 2),
            "state": pod_result.get("status", "COMPLETED").upper(),
            "status": pod_result.get("status", "completed"),
            "llm_called": True,
            "execution_mode": "multi_agent_pipeline",
            "model": "Multi-Framework (LangChain + Google ADK)",
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

    session_id = context_id or f"session-{agent_key}-{int(time.time())}"

    # Construct standard A2A JSON-RPC 2.0 Request
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "messageId": f"msg-{int(time.time()*1000)}",
            "role": "ROLE_USER",
            "parts": [{"text": query}],
            "contextId": session_id,
            "confirmation": confirmation
        },
        "id": 1
    }

    steps.append(f"A2A Task Dispatch: Created JSON-RPC 2.0 'message/send' request (Context: {session_id}).")

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
            "type": art.get("metadata", {}).get("framework", art.get("metadata", {}).get("type", "Deliverable")),
            "metadata": art.get("metadata", {}),
            "preview": preview_text[:300] + ("..." if len(preview_text) > 300 else "")
        })

    steps.append(f"Artifact Handoff: Delivered {len(formatted_artifacts)} formal deliverable artifact(s).")

    # Extract execution telemetry from artifacts metadata
    primary_meta = formatted_artifacts[0].get("metadata", {}) if formatted_artifacts else {}
    llm_called = primary_meta.get("llm_called", True)
    model_name = primary_meta.get("model", "gemini-3.1-flash-lite")
    execution_mode = primary_meta.get("execution_mode", "live_execution")
    llm_error = primary_meta.get("llm_error")

    duration_ms = int((time.time() - t_start) * 1000)

    return {
        "query": query,
        "mode": mode,
        "routed_agent": agent_key,
        "agent_invoked": decision,
        "agent_card": card_dict,
        "card_evaluations": candidates,
        "steps": steps,
        "output_text": output_text,
        "output": output_text,
        "artifacts": formatted_artifacts,
        "task_id": task_id,
        "taskId": task_id,
        "session_id": result_data.get("session_id", session_id),
        "hitl_required": result_data.get("hitl_required", False),
        "hitl_info": result_data.get("hitl_info", ""),
        "tool_confirmation_required": result_data.get("tool_confirmation_required", False),
        "tool_confirmation_details": result_data.get("tool_confirmation_details", {}),
        "audio_info": result_data.get("audio_info"),
        "duration_ms": duration_ms,
        "duration_seconds": round(duration_ms / 1000, 2),
        "state": status.upper(),
        "status": status,
        "llm_called": llm_called,
        "model": model_name,
        "execution_mode": execution_mode,
        "llm_error": llm_error,
        "jsonrpc_request": rpc_request,
        "jsonrpc_response": rpc_response
    }
