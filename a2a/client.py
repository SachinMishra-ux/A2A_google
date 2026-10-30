"""A2A Protocol Client Implementation (HTTP / JSON-RPC 2.0).

Allows any agent or orchestrator to discover remote agents via their Agent Card
and interact with them using standard A2A JSON-RPC 2.0 operations.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List, Optional
import httpx

from a2a.models import AgentCard, Artifact, Message, Part, Task

class A2AClient:
    """Client for interacting with any A2A v1.0 compliant agent server."""

    def __init__(self, agent_base_url: str, rpc_path: str = "/a2a", timeout: float = 30.0):
        """
        Args:
            agent_base_url: Base URL of the agent namespace (e.g., http://127.0.0.1:8000/sql)
            rpc_path: Relative RPC path (defaults to '/a2a')
        """
        self.base_url = agent_base_url.rstrip("/")
        self.rpc_url = f"{self.base_url}{rpc_path}"
        self.timeout = timeout
        self.card: Optional[AgentCard] = None

    async def get_agent_card(self) -> AgentCard:
        """Retrieves and parses the Agent Card from /.well-known/agent-card.json."""
        card_url = f"{self.base_url}/.well-known/agent-card.json"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(card_url)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch Agent Card from {card_url}: {resp.status_code} {resp.text}")
            data = resp.json()
            self.card = AgentCard(**data)
            return self.card

    async def send_message(
        self,
        text: str,
        context_id: Optional[str] = None,
        role: str = "ROLE_USER"
    ) -> Dict[str, Any]:
        """Dispatches a task message via A2A message/send JSON-RPC 2.0.
        
        Returns the parsed JSON-RPC result payload including task details and artifacts.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "messageId": f"msg-{uuid.uuid4().hex[:8]}",
                "role": role,
                "parts": [{"text": text}],
                "contextId": context_id,
            },
            "id": 1,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.rpc_url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"A2A Request failed ({resp.status_code}): {resp.text}")
            
            res_json = resp.json()
            if "error" in res_json and res_json["error"]:
                raise RuntimeError(f"A2A JSON-RPC Error: {res_json['error']}")
            
            return res_json.get("result", {})

    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Retrieves state of a task via A2A tasks/get JSON-RPC 2.0."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/get",
            "params": {"id": task_id},
            "id": 1,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.rpc_url, json=payload)
            res_json = resp.json()
            if "error" in res_json and res_json["error"]:
                raise RuntimeError(f"A2A tasks/get Error: {res_json['error']}")
            return res_json.get("result", {})

    # Synchronous convenience wrappers
    def get_agent_card_sync(self) -> AgentCard:
        return asyncio.run(self.get_agent_card())

    def send_message_sync(self, text: str, context_id: Optional[str] = None) -> Dict[str, Any]:
        return asyncio.run(self.send_message(text, context_id))
