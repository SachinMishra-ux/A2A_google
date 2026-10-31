"""Agent Card Declarations for Podcast Agent, SQL Agent, and RAG Agent.

================================================================================
WHAT IS AN AGENT CARD?
================================================================================
An Agent Card is the foundational discovery mechanism in the A2A protocol.
Think of it as:
- An OpenAPI / Swagger specification, but tailored specifically for AI Agents.
- A "business card" or "resume" hosted at a standardized web address:
    https://{host}/.well-known/agent-card.json

HOW ORCHESTRATION USES AGENT CARDS:
1. When an Orchestrator agent starts, it doesn't hardcode how other agents work.
2. It fetches the Agent Card from each agent server via HTTP GET.
3. The Orchestrator inspects the `skills` array (e.g. `query_user_accounts` or
   `synthesize_podcast_audio`) and the `supportedInterfaces` (JSON-RPC URL).
4. When a user goal arrives, the Orchestrator dynamically routes the subtask
   to whichever agent advertises the matching skill.

This module builds official A2A v1.0 Agent Cards for our three agents:
1. Podcast Studio Agent (Google ADK)
2. SQL Database Agent (LangChain + HITL + PII)
3. RAG Knowledge Agent (LangChain + FAISS)
================================================================================
"""

import json
from pathlib import Path
from a2a.models import AgentCard, SupportedInterface, AgentCapabilities, Skill

BASE_URL_DEFAULT = "http://127.0.0.1:8000"


# ──────────────────────────────────────────────────────────────────────────────
# 1. PODCAST AGENT CARD (GOOGLE ADK)
# ──────────────────────────────────────────────────────────────────────────────
def get_podcast_agent_card(base_url: str = BASE_URL_DEFAULT, standalone: bool = False) -> AgentCard:
    """Returns the Agent Card manifest for the Google ADK Podcast Studio Agent.
    
    Args:
        base_url: The base HTTP address of the server (e.g. http://127.0.0.1:8000 or http://127.0.0.1:8001).
        standalone: If True, endpoint is at /a2a. If False (gateway), endpoint is at /podcast/a2a.
    """
    rpc_url = f"{base_url}/a2a" if standalone else f"{base_url}/podcast/a2a"
    return AgentCard(
        name="podcast_studio_agent",
        version="1.0.0",
        description=(
            "Executive Producer multi-agent system built on Google ADK. Orchestrates topic research, "
            "dialogue scriptwriting across specialized host personas (Alex, Morgan, Taylor), "
            "and neural audio synthesis via Microsoft Edge TTS."
        ),
        # Advertises where clients can reach this agent via JSON-RPC 2.0
        supportedInterfaces=[
            SupportedInterface(protocol="JSONRPC", version="2.0", url=rpc_url)
        ],
        capabilities=AgentCapabilities(
            streaming=True,             # Supports real-time SSE token streaming
            pushNotifications=False,    # Long tasks don't require external webhooks
            statefulSessions=True       # Supports persistent episode threads
        ),
        defaultInputModes=["text/plain", "application/json"],
        defaultOutputModes=["application/json", "audio/mpeg", "text/markdown"],
        skills=[
            Skill(
                id="generate_podcast_script",
                name="Multi-Speaker Dialogue Scriptwriting",
                description=(
                    "Writes engaging conversational dialogue turns between 2 or 3 host personas. "
                    "Integrates external research briefings and audited database statistics into spoken dialogue."
                ),
                tags=["podcast", "scriptwriting", "creative-writing", "adk"],
                examples=[
                    "Write a podcast episode discussing AI Agents",
                    "Create a technical debate script between Host Alex and Specialist Morgan"
                ]
            ),
            Skill(
                id="synthesize_podcast_audio",
                name="Neural Multi-Speaker MP3 Audio Synthesis",
                description="Generates continuous multi-speaker audio tracks using Microsoft Neural voices.",
                tags=["audio", "tts", "mp3", "speech-synthesis"],
                examples=["Generate speech audio for dialogue script"]
            )
        ]
    )


# ──────────────────────────────────────────────────────────────────────────────
# 2. SQL AGENT CARD (LANGCHAIN + HITL + PII REDACTION)
# ──────────────────────────────────────────────────────────────────────────────
def get_sql_agent_card(base_url: str = BASE_URL_DEFAULT, standalone: bool = False) -> AgentCard:
    """Returns the Agent Card manifest for the LangChain SQL Database Agent.
    
    Args:
        base_url: The base HTTP address of the server (e.g. http://127.0.0.1:8000 or http://127.0.0.1:8002).
        standalone: If True, endpoint is at /a2a. If False (gateway), endpoint is at /sql/a2a.
    """
    rpc_url = f"{base_url}/a2a" if standalone else f"{base_url}/sql/a2a"
    return AgentCard(
        name="sql_database_agent",
        version="1.0.0",
        description=(
            "Enterprise database assistant built on LangChain and LangGraph. Executes read-only SQL queries "
            "against user account databases, strictly governed by Human-in-the-Loop (HITL) approval "
            "and automated PII redaction (Credit Cards & Emails)."
        ),
        supportedInterfaces=[
            SupportedInterface(protocol="JSONRPC", version="2.0", url=rpc_url)
        ],
        capabilities=AgentCapabilities(
            streaming=False,
            pushNotifications=False,
            statefulSessions=True
        ),
        defaultInputModes=["text/plain", "application/json"],
        defaultOutputModes=["text/plain", "application/json"],
        skills=[
            Skill(
                id="query_user_accounts",
                name="Secure Read-Only SQL Querying",
                description="Executes SELECT queries against users database and returns tabular reports.",
                tags=["database", "sql", "sqlite", "langchain"],
                examples=[
                    "What is Alice Smith's balance?",
                    "Fetch account records for user audit"
                ]
            ),
            Skill(
                id="hitl_pii_governance",
                name="HITL Verification & PII Redaction",
                description=(
                    "Interrupts sensitive queries for human approval and automatically redacts "
                    "Credit Cards and Email addresses before outputting data."
                ),
                tags=["governance", "security", "hitl", "pii-redaction"],
                examples=["Verify authorization for financial data queries"]
            )
        ]
    )


# ──────────────────────────────────────────────────────────────────────────────
# 3. RAG AGENT CARD (LANGCHAIN + FAISS + GEMINI)
# ──────────────────────────────────────────────────────────────────────────────
def get_rag_agent_card(base_url: str = BASE_URL_DEFAULT, standalone: bool = False) -> AgentCard:
    """Returns the Agent Card manifest for the LangChain RAG Knowledge Agent.
    
    Args:
        base_url: The base HTTP address of the server (e.g. http://127.0.0.1:8000 or http://127.0.0.1:8003).
        standalone: If True, endpoint is at /a2a. If False (gateway), endpoint is at /rag/a2a.
    """
    rpc_url = f"{base_url}/a2a" if standalone else f"{base_url}/rag/a2a"
    return AgentCard(
        name="rag_knowledge_agent",
        version="1.0.0",
        description=(
            "Retrieval-Augmented Generation agent built on LangChain and FAISS vector database. "
            "Performs semantic similarity search over indexed enterprise documentation and provides "
            "factually grounded answers with mandatory source citations."
        ),
        supportedInterfaces=[
            SupportedInterface(protocol="JSONRPC", version="2.0", url=rpc_url)
        ],
        capabilities=AgentCapabilities(
            streaming=True,
            pushNotifications=False,
            statefulSessions=True
        ),
        defaultInputModes=["text/plain", "application/json"],
        defaultOutputModes=["text/plain", "application/json"],
        skills=[
            Skill(
                id="semantic_knowledge_retrieval",
                name="FAISS Vector Similarity Search",
                description="Retrieves relevant documentation passages based on semantic embedding similarity.",
                tags=["rag", "faiss", "vector-search", "embeddings"],
                examples=["Explain Google Gemini architecture", "How does FAISS work?"]
            ),
            Skill(
                id="grounded_qa_with_citations",
                name="Grounded QA with Citations",
                description="Answers technical queries citing specific indexed source materials without hallucinations.",
                tags=["qa", "citations", "grounding"],
                examples=["What are the latest Gemini models and their token limits?"]
            )
        ]
    )


# ──────────────────────────────────────────────────────────────────────────────
# 4. CARD EXPORT UTILITY
# ──────────────────────────────────────────────────────────────────────────────
def export_all_cards(output_dir: Path, base_url: str = BASE_URL_DEFAULT):
    """Exports all three Agent Cards as static, machine-readable JSON files.
    
    Useful for:
    - Publishing to static HTTP file servers or S3/Cloud Storage buckets
    - Enterprise internal service catalog registrations
    - Offline inspection by architects and engineers
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cards = {
        "podcast_agent_card.json": get_podcast_agent_card(base_url),
        "sql_agent_card.json": get_sql_agent_card(base_url),
        "rag_agent_card.json": get_rag_agent_card(base_url),
    }
    for filename, card in cards.items():
        filepath = output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(card.model_dump(), f, indent=2)
    print(f"Exported {len(cards)} Agent Cards to {output_dir}")
