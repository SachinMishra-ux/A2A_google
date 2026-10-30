"""Agent Card Declarations for Podcast Agent, SQL Agent, and RAG Agent.

Provides official A2A v1.0 Agent Cards hosted under /.well-known/agent-card.json
"""

import json
from pathlib import Path
from a2a.models import AgentCard, SupportedInterface, AgentCapabilities, Skill

BASE_URL_DEFAULT = "http://127.0.0.1:8000"

def get_podcast_agent_card(base_url: str = BASE_URL_DEFAULT) -> AgentCard:
    return AgentCard(
        name="podcast_studio_agent",
        version="1.0.0",
        description=(
            "Executive Producer multi-agent system built on Google ADK. Orchestrates topic research, "
            "dialogue scriptwriting across specialized host personas (Alex, Morgan, Taylor), "
            "and neural audio synthesis via Microsoft Edge TTS."
        ),
        supportedInterfaces=[
            SupportedInterface(protocol="JSONRPC", version="2.0", url=f"{base_url}/podcast/a2a")
        ],
        capabilities=AgentCapabilities(streaming=True, pushNotifications=False),
        defaultInputModes=["text/plain", "application/json"],
        defaultOutputModes=["application/json", "audio/mpeg", "text/markdown"],
        skills=[
            Skill(
                id="generate_podcast_script",
                name="Multi-Speaker Dialogue Scriptwriting",
                description="Writes natural conversational dialogue turns between 2 or 3 host personas.",
                tags=["podcast", "scriptwriting", "creative-writing", "adk"],
                examples=["Write a podcast episode discussing AI Agents", "Create a technical debate script"]
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

def get_sql_agent_card(base_url: str = BASE_URL_DEFAULT) -> AgentCard:
    return AgentCard(
        name="sql_database_agent",
        version="1.0.0",
        description=(
            "Enterprise database assistant built on LangChain and LangGraph. Executes read-only SQL queries "
            "against user account databases, strictly governed by Human-in-the-Loop (HITL) approval "
            "and automated PII redaction (Credit Cards & Emails)."
        ),
        supportedInterfaces=[
            SupportedInterface(protocol="JSONRPC", version="2.0", url=f"{base_url}/sql/a2a")
        ],
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
        defaultInputModes=["text/plain", "application/json"],
        defaultOutputModes=["text/plain", "application/json"],
        skills=[
            Skill(
                id="query_user_accounts",
                name="Secure Read-Only SQL Querying",
                description="Executes SELECT queries against users database and returns tabular reports.",
                tags=["database", "sql", "sqlite", "langchain"],
                examples=["What is Alice Smith's balance?", "Fetch account records"]
            ),
            Skill(
                id="hitl_pii_governance",
                name="HITL Verification & PII Redaction",
                description="Interrupts queries for human approval and automatically redacts credit cards and emails.",
                tags=["governance", "security", "hitl", "pii-redaction"],
                examples=["Verify authorization for financial data queries"]
            )
        ]
    )

def get_rag_agent_card(base_url: str = BASE_URL_DEFAULT) -> AgentCard:
    return AgentCard(
        name="rag_knowledge_agent",
        version="1.0.0",
        description=(
            "Retrieval-Augmented Generation agent built on LangChain and FAISS vector database. "
            "Performs semantic similarity search over indexed enterprise documentation and provides "
            "factually grounded answers with mandatory source citations."
        ),
        supportedInterfaces=[
            SupportedInterface(protocol="JSONRPC", version="2.0", url=f"{base_url}/rag/a2a")
        ],
        capabilities=AgentCapabilities(streaming=True, pushNotifications=False),
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
                examples=["What are the latest Gemini models?"]
            )
        ]
    )

def export_all_cards(output_dir: Path, base_url: str = BASE_URL_DEFAULT):
    """Exports Agent Cards as static JSON files into the specified directory."""
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
