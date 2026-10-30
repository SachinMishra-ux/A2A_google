"""A2A (Agent-to-Agent) Protocol Package.

Implements Google & Linux Foundation A2A specification v1.0:
- Data models (AgentCard, Task, Message, Artifact)
- FastAPI A2A Server
- A2A Client (JSON-RPC 2.0)
- Multi-Agent Orchestrator
"""

from a2a.models import AgentCard, Task, Message, Artifact, Part
from a2a.agent_cards import (
    get_podcast_agent_card,
    get_sql_agent_card,
    get_rag_agent_card,
)
from a2a.client import A2AClient
from a2a.server import app, run_server
from a2a.orchestrator import run_multi_agent_orchestration

__all__ = [
    "AgentCard",
    "Task",
    "Message",
    "Artifact",
    "Part",
    "get_podcast_agent_card",
    "get_sql_agent_card",
    "get_rag_agent_card",
    "A2AClient",
    "app",
    "run_server",
    "run_multi_agent_orchestration",
]
