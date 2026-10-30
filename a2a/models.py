"""Canonical Pydantic Data Models for Agent-to-Agent (A2A) Protocol v1.0.

Defines schemas for:
- Agent Card (Identity & Discovery)
- Task (Stateful Lifecycle Management)
- Message & Part (Conversational Exchange)
- Artifact (Structured Handoff Deliverables)
- JSON-RPC 2.0 Request & Response Wrappers
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

# ── 1. Part & Content Models ──────────────────────────────────────────────────

class Part(BaseModel):
    """An atomic content component within a Message or Artifact."""
    text: Optional[str] = Field(default=None, description="Plain text content")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Structured JSON payload")
    media_type: Optional[str] = Field(default=None, description="MIME type of data or file")
    url: Optional[str] = Field(default=None, description="Reference URL to external data or file")

# ── 2. Message Models ─────────────────────────────────────────────────────────

class Message(BaseModel):
    """A conversational turn exchanged between client and agent."""
    messageId: str = Field(default_factory=lambda: f"msg-{uuid.uuid4().hex[:12]}")
    role: Literal["ROLE_USER", "ROLE_AGENT"] = Field(default="ROLE_USER")
    parts: List[Part] = Field(default_factory=list)
    contextId: Optional[str] = Field(default=None, description="Thread or session identifier")
    timestamp: float = Field(default_factory=time.time)

# ── 3. Artifact Models ────────────────────────────────────────────────────────

class Artifact(BaseModel):
    """A formal deliverable produced by an agent upon task execution."""
    artifactId: str = Field(default_factory=lambda: f"art-{uuid.uuid4().hex[:12]}")
    name: str = Field(description="Human-readable title or filename of the artifact")
    parts: List[Part] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)

# ── 4. Task Models ────────────────────────────────────────────────────────────

TaskStatus = Literal["submitted", "working", "completed", "failed", "needs_input", "cancelled"]

class Task(BaseModel):
    """Stateful unit of work tracked across the A2A protocol."""
    id: str = Field(default_factory=lambda: f"task-{uuid.uuid4().hex[:12]}")
    status: TaskStatus = Field(default="submitted")
    history: List[Message] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    error_message: Optional[str] = Field(default=None)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

# ── 5. Agent Card Models ──────────────────────────────────────────────────────

class Skill(BaseModel):
    """Discrete capability advertised by an agent."""
    id: str
    name: str
    description: str
    tags: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)

class SupportedInterface(BaseModel):
    """Protocol endpoint binding supported by the agent server."""
    protocol: Literal["JSONRPC", "REST", "GRPC"] = "JSONRPC"
    version: str = "2.0"
    url: str

class AgentCapabilities(BaseModel):
    """Flags describing agent capabilities."""
    streaming: bool = True
    pushNotifications: bool = False
    statefulSessions: bool = True

class AgentCard(BaseModel):
    """Machine-readable identity and capability manifest (agent-card.json)."""
    name: str
    version: str = "1.0.0"
    description: str
    supportedInterfaces: List[SupportedInterface]
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    defaultInputModes: List[str] = Field(default_factory=lambda: ["text/plain", "application/json"])
    defaultOutputModes: List[str] = Field(default_factory=lambda: ["text/plain", "application/json"])
    skills: List[Skill] = Field(default_factory=list)
    securitySchemes: Dict[str, Any] = Field(default_factory=lambda: {"auth": {"type": "none"}})
    provider: Dict[str, str] = Field(default_factory=lambda: {
        "organization": "A2A Multi-Agent Enterprise Ecosystem",
        "standard": "Linux Foundation / Google A2A v1.0"
    })

# ── 6. JSON-RPC 2.0 Envelope Models ───────────────────────────────────────────

class JsonRpcError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

class JsonRpcRequest(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[Union[str, int]] = 1

class JsonRpcResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    result: Optional[Any] = None
    error: Optional[Union[Dict[str, Any], JsonRpcError]] = None
    id: Optional[Union[str, int]] = 1
