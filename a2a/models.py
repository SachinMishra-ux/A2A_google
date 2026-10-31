"""Canonical Pydantic Data Models for Agent-to-Agent (A2A) Protocol v1.0.

================================================================================
WHAT IS THE A2A DATA MODEL?
================================================================================
The A2A protocol (standardized by Google and the Linux Foundation) defines a
universal language so that AI agents built on completely different frameworks
(e.g., Google ADK, LangChain, LangGraph, CrewAI, AutoGen) can exchange tasks,
stream real-time progress, and hand off structured artifacts without exposing
their internal prompts, private databases, or memory states.

This module defines the 5 Core Primitives of A2A:
1. Part:      The atomic multimodal building block (text, structured data, file URL).
2. Message:   A single conversational turn between a client and an agent.
3. Artifact:  A formal deliverable (report, dataset, code, audio) produced by a task.
4. Task:      The stateful lifecycle of a delegated job (submitted -> working -> completed).
5. AgentCard: The public "business card" / manifest (.well-known/agent-card.json)
              advertising an agent's identity, skills, endpoints, and security.
6. JSON-RPC:  The request/response envelope transporting these objects over HTTP.
================================================================================
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# 1. PART & CONTENT PRIMITIVES
# ──────────────────────────────────────────────────────────────────────────────
class Part(BaseModel):
    """An atomic content component within an A2A Message or Artifact.
    
    Why Parts?
    Real-world AI interactions are rarely just strings. An agent might return a
    markdown explanation (text), plus a structured JSON scorecard (data), plus
    an audio recording or PDF report (url/media_type). 'Part' allows combining
    multiple modalities in a single turn without breaking standard schemas.
    """
    text: Optional[str] = Field(
        default=None, 
        description="Human-readable text content or markdown explanation."
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Structured JSON payload (e.g., database rows, financial tables, configuration)."
    )
    media_type: Optional[str] = Field(
        default=None, 
        description="MIME type describing the payload (e.g. 'text/plain', 'application/json', 'audio/mpeg')."
    )
    url: Optional[str] = Field(
        default=None, 
        description="URI reference pointing to an external file, Cloud Storage bucket, or streaming endpoint."
    )


# ──────────────────────────────────────────────────────────────────────────────
# 2. MESSAGE PRIMITIVE
# ──────────────────────────────────────────────────────────────────────────────
class Message(BaseModel):
    """A conversational turn exchanged between client and agent.
    
    In A2A, communication is role-based:
    - 'ROLE_USER':  The client orchestrator formulating and dispatching a request.
    - 'ROLE_AGENT': The remote specialist agent responding with analysis or requests for clarification.
    
    The 'contextId' groups multiple message turns into a persistent conversational thread,
    similar to thread_id in LangGraph or session_id in Google ADK.
    """
    messageId: str = Field(
        default_factory=lambda: f"msg-{uuid.uuid4().hex[:12]}",
        description="Globally unique identifier for this message turn (used for idempotency & auditing)."
    )
    role: Literal["ROLE_USER", "ROLE_AGENT"] = Field(
        default="ROLE_USER",
        description="Identifies who originated this turn: the requester (ROLE_USER) or the agent (ROLE_AGENT)."
    )
    parts: List[Part] = Field(
        default_factory=list,
        description="One or more content blocks composing this message."
    )
    contextId: Optional[str] = Field(
        default=None, 
        description="Thread or session identifier linking multi-turn interactions together."
    )
    timestamp: float = Field(
        default_factory=time.time,
        description="Unix timestamp (in seconds) when the message was constructed."
    )


# ──────────────────────────────────────────────────────────────────────────────
# 3. ARTIFACT PRIMITIVE (STRUCTURED DELIVERABLES)
# ──────────────────────────────────────────────────────────────────────────────
class Artifact(BaseModel):
    """A formal deliverable produced by an agent upon completing a task.
    
    Why Artifacts?
    When an orchestrator delegates a subtask (e.g. 'Audit the users database' or
    'Write a podcast script'), it does not just want raw chat text—it wants a
    discrete deliverable it can pass to the next agent down the line.
    
    Examples:
    - SQL Agent generates: 'SQL_Query_Execution_Record' (audited, PII-redacted rows)
    - RAG Agent generates: 'Grounded_RAG_Citations' (retrieved facts + citations)
    - Podcast Agent generates: 'Podcast_Dialogue_Script.json' (multi-speaker script)
    """
    artifactId: str = Field(
        default_factory=lambda: f"art-{uuid.uuid4().hex[:12]}",
        description="Unique identifier for the generated artifact."
    )
    name: str = Field(
        description="Human-readable title or filename of the artifact (e.g. 'Podcast_Script.json')."
    )
    parts: List[Part] = Field(
        default_factory=list,
        description="The actual content components forming this deliverable."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual metadata (e.g. security policy, execution duration, tokens, timestamps)."
    )
    created_at: float = Field(
        default_factory=time.time,
        description="Timestamp when the artifact was minted."
    )


# ──────────────────────────────────────────────────────────────────────────────
# 4. TASK PRIMITIVE (STATEFUL LIFECYCLE)
# ──────────────────────────────────────────────────────────────────────────────
# In A2A, tasks are not just simple instantaneous function returns. Complex agentic
# work can take seconds, minutes, or even days (with human reviews).
# The task lifecycle tracks this progression through 6 canonical states:
TaskStatus = Literal[
    "submitted",    # Task received by the A2A server, queued for execution
    "working",      # Agent is actively running (reasoning, tool calls, processing)
    "completed",    # Execution finished successfully; output and artifacts ready
    "failed",       # Task encountered an unrecoverable exception
    "needs_input",  # Agent is blocked waiting for human approval or client response
    "cancelled"     # Task was aborted by client request (tasks/cancel)
]

class Task(BaseModel):
    """The stateful unit of work tracked across the A2A protocol.
    
    Instead of an orchestrator blocking synchronously on an HTTP socket for 60 seconds,
    A2A assigns a Task ID. The client can:
    - Await synchronous completion (message/send)
    - Stream thought tokens and updates (message/stream via SSE)
    - Poll the task later (tasks/get)
    - Push notifications to webhooks when status transitions to 'completed'
    """
    id: str = Field(
        default_factory=lambda: f"task-{uuid.uuid4().hex[:12]}",
        description="Globally unique Task ID assigned by the A2A server."
    )
    status: TaskStatus = Field(
        default="submitted",
        description="Current lifecycle status of the task."
    )
    history: List[Message] = Field(
        default_factory=list,
        description="Complete conversational log of messages exchanged during this task."
    )
    artifacts: List[Artifact] = Field(
        default_factory=list,
        description="Formal deliverables generated by the agent during this task."
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Diagnostic error explanation if status == 'failed'."
    )
    created_at: float = Field(
        default_factory=time.time,
        description="Timestamp when the task was created."
    )
    updated_at: float = Field(
        default_factory=time.time,
        description="Timestamp of the most recent state transition."
    )


# ──────────────────────────────────────────────────────────────────────────────
# 5. AGENT CARD PRIMITIVES (DISCOVERY & IDENTITY)
# ──────────────────────────────────────────────────────────────────────────────
class Skill(BaseModel):
    """A discrete capability advertised by an agent in its Agent Card.
    
    Allows an orchestrator LLM to read an agent's résumé and decide:
    'Can this agent execute my SQL query? Yes, it advertises the query_user_accounts skill.'
    """
    id: str = Field(description="Machine-readable unique skill identifier (e.g. 'generate_podcast_script').")
    name: str = Field(description="Human-readable title of the skill.")
    description: str = Field(description="Detailed explanation of what this skill does.")
    tags: List[str] = Field(default_factory=list, description="Categorization tags for semantic discovery.")
    examples: List[str] = Field(default_factory=list, description="Natural-language prompt examples triggering this skill.")

class SupportedInterface(BaseModel):
    """Protocol endpoint binding supported by this A2A agent server."""
    protocol: Literal["JSONRPC", "REST", "GRPC"] = "JSONRPC"
    version: str = "2.0"
    url: str = Field(description="Full HTTP endpoint URL where the agent accepts requests.")

class AgentCapabilities(BaseModel):
    """Feature flags indicating protocol capabilities supported by the server."""
    streaming: bool = Field(default=True, description="Supports Server-Sent Events (SSE) token streaming via message/stream.")
    pushNotifications: bool = Field(default=False, description="Supports sending asynchronous webhooks when long tasks finish.")
    statefulSessions: bool = Field(default=True, description="Maintains multi-turn memory across contextId threads.")

class AgentCard(BaseModel):
    """Machine-readable identity and capability manifest (agent-card.json).
    
    By standard convention, hosted at:
        https://{host}/.well-known/agent-card.json
        
    The Agent Card functions like a LinkedIn profile or OpenAPI spec for AI agents.
    It tells prospective clients:
    - Who I am (name, version, description, provider)
    - Where to talk to me (supportedInterfaces endpoint URLs)
    - What I can do (skills list)
    - What data formats I expect and return (defaultInputModes / defaultOutputModes)
    - How to authenticate (securitySchemes - OAuth2, API Keys, mTLS)
    """
    name: str = Field(description="Unique identifier name of the agent.")
    version: str = Field(default="1.0.0", description="Semantic version of the agent service.")
    description: str = Field(description="Executive summary of the agent's purpose and specialization.")
    supportedInterfaces: List[SupportedInterface] = Field(description="List of transport interfaces (JSON-RPC 2.0 URLs).")
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    defaultInputModes: List[str] = Field(
        default_factory=lambda: ["text/plain", "application/json"],
        description="MIME types the agent accepts as input."
    )
    defaultOutputModes: List[str] = Field(
        default_factory=lambda: ["text/plain", "application/json"],
        description="MIME types the agent produces as output."
    )
    skills: List[Skill] = Field(default_factory=list, description="List of discrete skills the agent provides.")
    securitySchemes: Dict[str, Any] = Field(
        default_factory=lambda: {"auth": {"type": "none"}},
        description="Authentication and security schemes (e.g. OAuth2, bearer token, API key)."
    )
    provider: Dict[str, str] = Field(
        default_factory=lambda: {
            "organization": "A2A Multi-Agent Enterprise Ecosystem",
            "standard": "Linux Foundation / Google A2A v1.0"
        },
        description="Metadata on the author or organization hosting the agent."
    )


# ──────────────────────────────────────────────────────────────────────────────
# 6. JSON-RPC 2.0 PROTOCOL ENVELOPE MODELS
# ──────────────────────────────────────────────────────────────────────────────
class JsonRpcError(BaseModel):
    """Standard JSON-RPC 2.0 error object."""
    code: int = Field(description="Standard error code (e.g. -32600 Invalid Request, -32601 Method Not Found).")
    message: str = Field(description="Short human-readable summary of the error.")
    data: Optional[Any] = Field(default=None, description="Detailed diagnostic data or stack trace.")

class JsonRpcRequest(BaseModel):
    """Incoming JSON-RPC 2.0 request envelope sent from client to agent server."""
    jsonrpc: Literal["2.0"] = "2.0"
    method: str = Field(description="A2A operation: 'message/send', 'message/stream', 'tasks/get', 'tasks/cancel'.")
    params: Dict[str, Any] = Field(default_factory=dict, description="Method parameters (parts, contextId, taskId, etc.).")
    id: Optional[Union[str, int]] = Field(default=1, description="Correlation identifier for matching response to request.")

class JsonRpcResponse(BaseModel):
    """Outgoing JSON-RPC 2.0 response envelope sent from agent server to client."""
    jsonrpc: Literal["2.0"] = "2.0"
    result: Optional[Any] = Field(default=None, description="Successful payload (Task object, status, output, artifacts).")
    error: Optional[Union[Dict[str, Any], JsonRpcError]] = Field(default=None, description="Error details if invocation failed.")
    id: Optional[Union[str, int]] = Field(default=1, description="Correlation identifier matching the request id.")
