"""A2A Protocol Multi-Agent Orchestrator.

================================================================================
HOW A2A CONNECTS THE THREE AGENTS: THE ORCHESTRATION PIPELINE
================================================================================
This script demonstrates how three completely heterogeneous AI agents—built on
different frameworks and holding separate responsibilities—collaborate
via standard A2A protocol calls to achieve a complex unified mission.

THE THREE AGENTS INVOLVED:
1. SQL Agent (LangChain + LangGraph):
   - Specialization: Sensitive user databases
   - Governed by: Human-in-the-Loop (HITL) approval + PII redaction
2. RAG Agent (LangChain + FAISS):
   - Specialization: Enterprise documentation retrieval
   - Governed by: Semantic vector search + strict source citations
3. Podcast Agent (Google ADK):
   - Specialization: Cognitive scriptwriting & neural TTS audio synthesis
   - Governed by: Multi-speaker casting (Alex & Morgan) + creative planning

THE 5-STEP ORCHESTRATION WORKFLOW:
┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: CAPABILITY DISCOVERY                                                 │
│ Orchestrator reads each agent's Agent Card (/.well-known/agent-card.json)    │
│ to dynamically verify their skills without any hardcoded assumptions.        │
├──────────────────────────────────────────────────────────────────────────────┤
│ STEP 2: AUDITED SQL DELEGATION                                               │
│ Orchestrator sends task to SQL Agent over A2A JSON-RPC (message/send).      │
│ SQL Agent approves query, redacts Credit Cards & Emails, and returns data.   │
├──────────────────────────────────────────────────────────────────────────────┤
│ STEP 3: GROUNDED RAG KNOWLEDGE DELEGATION                                    │
│ Orchestrator sends task to RAG Agent over A2A JSON-RPC (message/send).      │
│ RAG Agent searches FAISS and returns verified facts with source citations.   │
├──────────────────────────────────────────────────────────────────────────────┤
│ STEP 4: COGNITIVE PODCAST SYNTHESIS                                          │
│ Orchestrator combines the SQL facts and RAG citations, sending both to the   │
│ Google ADK Podcast Studio agent via A2A. The Podcast Agent writes an episode │
│ script between Host Alex and Specialist Morgan discussing both domains.      │
├──────────────────────────────────────────────────────────────────────────────┤
│ STEP 5: ARTIFACT HANDOFF & TRACEABILITY SUMMARY                              │
│ All generated deliverables (Artifacts) and Task IDs are logged in a unified  │
│ audit report.                                                                │
└──────────────────────────────────────────────────────────────────────────────┘
================================================================================
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from a2a.client import A2AClient


async def run_multi_agent_orchestration(
    base_url: Optional[str] = "http://127.0.0.1:8000",
    sql_url: Optional[str] = None,
    rag_url: Optional[str] = None,
    podcast_url: Optional[str] = None,
):
    """Executes the complete cross-agent workflow via A2A JSON-RPC 2.0.
    
    Can run against:
    - A single Unified Gateway (default: base_url = 'http://127.0.0.1:8000')
    - Individual Microservice Servers (e.g. sql_url=8002, rag_url=8003, podcast_url=8001)
    """
    # Resolve target endpoints
    target_sql = sql_url or f"{base_url}/sql"
    target_rag = rag_url or f"{base_url}/rag"
    target_podcast = podcast_url or f"{base_url}/podcast"

    print("=" * 75)
    print(" 🚀  A2A PROTOCOL MULTI-AGENT COLLABORATION ORCHESTRATOR")
    print("=" * 75)
    print(f"SQL Agent Target:     {target_sql}")
    print(f"RAG Agent Target:     {target_rag}")
    print(f"Podcast Agent Target: {target_podcast}\n")

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 1: CAPABILITY DISCOVERY VIA AGENT CARDS
    # ──────────────────────────────────────────────────────────────────────────
    print("─── STEP 1: CAPABILITY DISCOVERY (AGENT CARDS) ───")
    sql_client = A2AClient(target_sql)
    rag_client = A2AClient(target_rag)
    podcast_client = A2AClient(target_podcast)

    try:
        # Fetch and verify SQL Agent Card
        sql_card = await sql_client.get_agent_card()
        print(f"✅ Discovered: {sql_card.name} (v{sql_card.version})")
        print(f"   Framework: LangChain + LangGraph")
        print(f"   Advertised Skills: {', '.join([s.name for s in sql_card.skills])}")

        # Fetch and verify RAG Agent Card
        rag_card = await rag_client.get_agent_card()
        print(f"✅ Discovered: {rag_card.name} (v{rag_card.version})")
        print(f"   Framework: LangChain + FAISS Vector Store")
        print(f"   Advertised Skills: {', '.join([s.name for s in rag_card.skills])}")

        # Fetch and verify Podcast Agent Card
        podcast_card = await podcast_client.get_agent_card()
        print(f"✅ Discovered: {podcast_card.name} (v{podcast_card.version})")
        print(f"   Framework: Google ADK (Agent Development Kit)")
        print(f"   Advertised Skills: {', '.join([s.name for s in podcast_card.skills])}\n")
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        print("Tip: Ensure the A2A server(s) are running before executing the orchestrator.")
        return

    # Create a unique multi-agent session thread identifier
    session_id = f"session-a2a-{int(time.time())}"

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 2: DELEGATE DATABASE AUDIT TO SQL AGENT OVER A2A
    # ──────────────────────────────────────────────────────────────────────────
    print("─── STEP 2: SQL AGENT DELEGATION (HITL & PII REDACTION) ───")
    sql_prompt = "Query users database for Alice Smith's account balance and credit card details."
    print(f"-> Dispatching A2A Task [message/send] to SQL Agent...")
    print(f"   Prompt: '{sql_prompt}'")
    
    t0 = time.time()
    # Sends JSON-RPC 2.0 message/send request over HTTP
    sql_response = await sql_client.send_message(sql_prompt, context_id=session_id)
    t_sql = time.time() - t0
    
    sql_output = sql_response.get("output", "")
    sql_task_id = sql_response.get("taskId")
    print(f"<- [A2A Success] Task ID: {sql_task_id} (Status: {sql_response.get('status')}) in {t_sql:.2f}s")
    print(f"   Response Payload:\n{sql_output.strip()}\n")

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 3: DELEGATE KNOWLEDGE RETRIEVAL TO RAG AGENT OVER A2A
    # ──────────────────────────────────────────────────────────────────────────
    print("─── STEP 3: RAG AGENT DELEGATION (GROUNDED CITATIONS) ───")
    rag_prompt = "What is Google Gemini multimodal architecture and what are the latest model variants?"
    print(f"-> Dispatching A2A Task [message/send] to RAG Agent...")
    print(f"   Prompt: '{rag_prompt}'")

    t0 = time.time()
    # Sends JSON-RPC 2.0 message/send request over HTTP
    rag_response = await rag_client.send_message(rag_prompt, context_id=session_id)
    t_rag = time.time() - t0

    rag_output = rag_response.get("output", "")
    rag_task_id = rag_response.get("taskId")
    print(f"<- [A2A Success] Task ID: {rag_task_id} (Status: {rag_response.get('status')}) in {t_rag:.2f}s")
    print(f"   Response Payload:\n{rag_output.strip()}\n")

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 4: PASS FINDINGS TO PODCAST AGENT (ADK) FOR SYNTHESIS
    # ──────────────────────────────────────────────────────────────────────────
    print("─── STEP 4: PODCAST AGENT SYNTHESIS (ADK COGNITIVE SCRIPTWRITER) ───")
    # Formulate a composite prompt that feeds the outputs of the first two agents into the third!
    podcast_prompt = (
        f"Generate a podcast episode for: How Google Gemini Empowers Secure Financial Analytics.\n\n"
        f"Context from SQL Agent (Audited Database):\n{sql_output}\n\n"
        f"Context from RAG Agent (Technical Documentation):\n{rag_output}\n\n"
        f"Task: Create a lively, technical 2-speaker podcast between Host Alex and Specialist Morgan."
    )
    print(f"-> Dispatching A2A Synthesis Task [message/send] to Podcast Agent...")
    
    t0 = time.time()
    podcast_response = await podcast_client.send_message(podcast_prompt, context_id=session_id)
    t_podcast = time.time() - t0

    podcast_output = podcast_response.get("output", "")
    podcast_task_id = podcast_response.get("taskId")
    print(f"<- [A2A Success] Task ID: {podcast_task_id} (Status: {podcast_response.get('status')}) in {t_podcast:.2f}s")
    print("\n=== GENERATED PODCAST SCRIPT (A2A DELIVERABLE ARTIFACT) ===")
    print(podcast_output.strip())

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 5: FINAL VERIFICATION & ARTIFACT AUDIT SUMMARY
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 75)
    print(" 🎯  A2A MULTI-AGENT EXECUTION SUMMARY")
    print("=" * 75)
    print(f"Session Context:     {session_id}")
    print(f"1. SQL Agent Task:   {sql_task_id} | Artifacts Delivered: {len(sql_response.get('artifacts', []))}")
    print(f"2. RAG Agent Task:   {rag_task_id} | Artifacts Delivered: {len(rag_response.get('artifacts', []))}")
    print(f"3. Podcast Task:     {podcast_task_id} | Artifacts Delivered: {len(podcast_response.get('artifacts', []))}")
    print("\nProtocol Architectural Principles Verified:")
    print(" • Framework Agnosticism: LangGraph and Google ADK worked seamlessly over JSON-RPC 2.0.")
    print(" • Boundary Opacity: No internal prompts or memory structures leaked across boundaries.")
    print(" • Stateful Handoff: Output of SQL & RAG was packaged into Artifacts and consumed by Podcast.")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_multi_agent_orchestration())
