"""A2A (Agent-to-Agent) Protocol Package.

================================================================================
A2A PROTOCOL SPECIFICATION v1.0 IMPLEMENTATION
================================================================================
This package implements the open Agent-to-Agent standard:
- Models:       Canonical data structures (AgentCard, Task, Message, Artifact, Part)
- Agent Cards:  Standardized machine-readable manifests (.well-known/agent-card.json)
- Server:       FastAPI JSON-RPC 2.0 implementation supporting Gateway & Standalone modes
- Client:       Reusable HTTP / JSON-RPC 2.0 client for discovering and calling agents
- Orchestrator: Multi-agent collaboration engine connecting ADK and LangChain agents
================================================================================
"""

from a2a.models import AgentCard, Task, Message, Artifact, Part, JsonRpcRequest, JsonRpcResponse, JsonRpcError
from a2a.agent_cards import (
    get_podcast_agent_card,
    get_sql_agent_card,
    get_rag_agent_card,
    export_all_cards,
)
from a2a.client import A2AClient
from a2a.server import app, run_server, create_gateway_app, create_standalone_agent_app
from a2a.orchestrator import run_multi_agent_orchestration

__all__ = [
    "AgentCard",
    "Task",
    "Message",
    "Artifact",
    "Part",
    "JsonRpcRequest",
    "JsonRpcResponse",
    "JsonRpcError",
    "get_podcast_agent_card",
    "get_sql_agent_card",
    "get_rag_agent_card",
    "export_all_cards",
    "A2AClient",
    "app",
    "run_server",
    "create_gateway_app",
    "create_standalone_agent_app",
    "run_multi_agent_orchestration",
]
