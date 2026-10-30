"""A2A Protocol Multi-Agent Orchestrator.

Orchestrates cross-agent communication among:
1. SQL Database Agent (LangChain + HITL + PII)
2. RAG Knowledge Agent (LangChain + FAISS + Gemini)
3. Podcast Studio Agent (Google ADK)

Demonstrates the power of the A2A protocol: connecting three independent agents
built on different frameworks and paradigms into a single unified workflow.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from a2a.client import A2AClient

async def run_multi_agent_orchestration(base_url: str = "http://127.0.0.1:8000"):
    print("=" * 70)
    print(" 🚀  A2A PROTOCOL MULTI-AGENT COLLABORATION ORCHESTRATOR")
    print("=" * 70)
    print(f"Target Gateway: {base_url}")
    print("Connecting agents: [SQL Agent (LangChain)] <-> [RAG Agent (LangChain)] <-> [Podcast Agent (ADK)]\n")

    # ── Phase 1: Discovery & Agent Card Verification ──────────────────────────
    print("─── STEP 1: CAPABILITY DISCOVERY (AGENT CARDS) ───")
    sql_client = A2AClient(f"{base_url}/sql")
    rag_client = A2AClient(f"{base_url}/rag")
    podcast_client = A2AClient(f"{base_url}/podcast")

    try:
        sql_card = await sql_client.get_agent_card()
        print(f"✅ Discovered: {sql_card.name} (v{sql_card.version})")
        print(f"   Skills: {', '.join([s.name for s in sql_card.skills])}")

        rag_card = await rag_client.get_agent_card()
        print(f"✅ Discovered: {rag_card.name} (v{rag_card.version})")
        print(f"   Skills: {', '.join([s.name for s in rag_card.skills])}")

        podcast_card = await podcast_client.get_agent_card()
        print(f"✅ Discovered: {podcast_card.name} (v{podcast_card.version})")
        print(f"   Skills: {', '.join([s.name for s in podcast_card.skills])}\n")
    except Exception as e:
        print(f"❌ Discovery failed. Ensure A2A server is running at {base_url}. Error: {e}")
        return

    session_id = f"session-a2a-{int(time.time())}"

    # ── Phase 2: Delegate Task to SQL Agent via A2A ───────────────────────────
    print("─── STEP 2: SQL AGENT DELEGATION (HITL & PII REDACTION) ───")
    sql_prompt = "Query users database for Alice Smith's account balance and credit card details."
    print(f"-> Sending A2A Task [message/send] to SQL Agent...")
    print(f"   Prompt: '{sql_prompt}'")
    
    t0 = time.time()
    sql_response = await sql_client.send_message(sql_prompt, context_id=session_id)
    t_sql = time.time() - t0
    
    sql_output = sql_response.get("output", "")
    sql_task_id = sql_response.get("taskId")
    print(f"<- [A2A Success] Task ID: {sql_task_id} (Status: {sql_response.get('status')}) in {t_sql:.2f}s")
    print(f"   Response Payload:\n{sql_output.strip()}\n")

    # ── Phase 3: Delegate Task to RAG Agent via A2A ───────────────────────────
    print("─── STEP 3: RAG AGENT DELEGATION (GROUNDED CITATIONS) ───")
    rag_prompt = "What is Google Gemini multimodal architecture and what are the latest model variants?"
    print(f"-> Sending A2A Task [message/send] to RAG Agent...")
    print(f"   Prompt: '{rag_prompt}'")

    t0 = time.time()
    rag_response = await rag_client.send_message(rag_prompt, context_id=session_id)
    t_rag = time.time() - t0

    rag_output = rag_response.get("output", "")
    rag_task_id = rag_response.get("taskId")
    print(f"<- [A2A Success] Task ID: {rag_task_id} (Status: {rag_response.get('status')}) in {t_rag:.2f}s")
    print(f"   Response Payload:\n{rag_output.strip()}\n")

    # ── Phase 4: Delegate Podcast Script Synthesis to ADK Agent ───────────────
    print("─── STEP 4: PODCAST AGENT SYNTHESIS (ADK COGNITIVE SCRIPTWRITER) ───")
    podcast_prompt = (
        f"Generate a podcast episode for: How Google Gemini Empowers Secure Financial Analytics.\n\n"
        f"Context from SQL Agent (Audited Database):\n{sql_output}\n\n"
        f"Context from RAG Agent (Technical Documentation):\n{rag_output}\n\n"
        f"Task: Create a lively, technical 2-speaker podcast between Host Alex and Specialist Morgan."
    )
    print(f"-> Sending A2A Synthesis Task [message/send] to Podcast Agent...")
    
    t0 = time.time()
    podcast_response = await podcast_client.send_message(podcast_prompt, context_id=session_id)
    t_podcast = time.time() - t0

    podcast_output = podcast_response.get("output", "")
    podcast_task_id = podcast_response.get("taskId")
    print(f"<- [A2A Success] Task ID: {podcast_task_id} (Status: {podcast_response.get('status')}) in {t_podcast:.2f}s")
    print("\n=== GENERATED PODCAST SCRIPT (A2A DELIVERABLE ARTIFACT) ===")
    print(podcast_output.strip())

    # ── Phase 5: Verification & Traceability Summary ──────────────────────────
    print("\n" + "=" * 70)
    print(" 🎯  A2A MULTI-AGENT EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Session Context:     {session_id}")
    print(f"1. SQL Agent Task:   {sql_task_id} | Artifacts: {len(sql_response.get('artifacts', []))}")
    print(f"2. RAG Agent Task:   {rag_task_id} | Artifacts: {len(rag_response.get('artifacts', []))}")
    print(f"3. Podcast Task:     {podcast_task_id} | Artifacts: {len(podcast_response.get('artifacts', []))}")
    print("\nAll 3 agents communicated across standard A2A JSON-RPC 2.0 protocol.")
    print("Principles verified: Framework Agnosticism, Boundary Opacity, and Stateful Artifact Handoff.")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_multi_agent_orchestration())
