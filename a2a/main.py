"""Entry Point for A2A Multi-Agent Framework.

================================================================================
A2A MULTI-AGENT CLI & RUNNER
================================================================================
This script provides the central management interface for:
1. Running the Unified A2A Gateway (all 3 agents on port 8000)
2. Running Individual Dedicated Servers (e.g. podcast on 8001, sql on 8002, rag on 8003)
3. Running all 3 Individual Servers simultaneously in background processes
4. Executing the end-to-end multi-agent orchestration demo
5. Querying specific agents directly over A2A JSON-RPC 2.0
6. Inspecting and exporting Agent Cards

QUICK COMMANDS:
- Start Unified Gateway (Port 8000):
    uv run python a2a/main.py --server --port 8000

- Start 3 Individual Servers (Ports 8001, 8002, 8003):
    uv run python a2a/main.py --start-individual-servers

- Run End-to-End Collaboration Demo:
    uv run python a2a/main.py --demo

- Query a Single Agent:
    uv run python a2a/main.py --query-agent sql --prompt "Show Alice's balance"
================================================================================
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from a2a.agent_cards import (
    get_podcast_agent_card,
    get_sql_agent_card,
    get_rag_agent_card,
    export_all_cards,
)
from a2a.client import A2AClient
from a2a.orchestrator import run_multi_agent_orchestration
from a2a.server import run_server


# ──────────────────────────────────────────────────────────────────────────────
# 1. INSPECTION & DISPLAY HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def print_cards_inspection():
    """Prints a structured summary of all three advertised Agent Cards."""
    print("=" * 75)
    print(" 📇  A2A AGENT CARDS (OFFICIAL v1.0 MANIFESTS)")
    print("=" * 75)
    for name, card_fn in [
        ("PODCAST AGENT (GOOGLE ADK)", get_podcast_agent_card),
        ("SQL DATABASE AGENT (LANGCHAIN + HITL)", get_sql_agent_card),
        ("RAG KNOWLEDGE AGENT (LANGCHAIN + FAISS)", get_rag_agent_card),
    ]:
        card = card_fn()
        print(f"\n[{name}]")
        print(f"Name:        {card.name}")
        print(f"Version:     {card.version}")
        print(f"Description: {card.description}")
        print(f"Endpoints:   {[i.url for i in card.supportedInterfaces]}")
        print("Skills:")
        for s in card.skills:
            print(f"  • {s.name} ({s.id})")
            print(f"    Tags: {s.tags}")
            print(f"    Description: {s.description}")
    print("=" * 75)


# ──────────────────────────────────────────────────────────────────────────────
# 2. DIRECT A2A QUERY FUNCTION
# ──────────────────────────────────────────────────────────────────────────────
async def query_single_agent(agent_name: str, prompt: str, port: int = 8000):
    """Sends a direct task query to an individual agent via A2A JSON-RPC 2.0."""
    base_url = f"http://127.0.0.1:{port}/{agent_name}"
    print(f"\n[A2A DIRECT QUERY] Dispatching task to '{agent_name}' at {base_url}...")
    client = A2AClient(base_url)
    try:
        card = await client.get_agent_card()
        print(f"Target Agent: {card.name} (v{card.version})")
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch Agent Card from {base_url}. Ensure server is running on port {port}.")
        print(f"Error: {e}")
        return

    print(f"Prompt: '{prompt}'")
    t0 = time.time()
    try:
        res = await client.send_message(prompt)
        dt = time.time() - t0
        print(f"\n[SUCCESS] Response received in {dt:.2f}s:")
        print(f"Task ID: {res.get('taskId')}")
        print(f"Status:  {res.get('status')}")
        print("\n=== OUTPUT ===")
        print(res.get("output"))
        if res.get("artifacts"):
            print(f"\nArtifacts ({len(res['artifacts'])}):")
            for art in res["artifacts"]:
                print(f"  • {art.get('name')}")
    except Exception as e:
        print(f"❌ Failed to execute query over A2A: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# 3. INDIVIDUAL SERVERS LAUNCHER
# ──────────────────────────────────────────────────────────────────────────────
def start_individual_servers():
    """Launches all 3 agents as separate standalone microservices on separate ports.
    
    Port 8001: Podcast Agent (Google ADK)
    Port 8002: SQL Agent (LangChain + HITL)
    Port 8003: RAG Agent (LangChain + FAISS)
    """
    print("=" * 75)
    print(" 🚀  LAUNCHING 3 INDIVIDUAL STANDALONE A2A SERVERS")
    print("=" * 75)
    print("Starting microservices:")
    print(" • Podcast Agent: http://127.0.0.1:8001 (Card: http://127.0.0.1:8001/.well-known/agent-card.json)")
    print(" • SQL Agent:     http://127.0.0.1:8002 (Card: http://127.0.0.1:8002/.well-known/agent-card.json)")
    print(" • RAG Agent:     http://127.0.0.1:8003 (Card: http://127.0.0.1:8003/.well-known/agent-card.json)")
    print("\nPress Ctrl+C to stop all servers.")
    print("=" * 75)

    py_exe = sys.executable
    procs = []
    try:
        p_podcast = subprocess.Popen([py_exe, str(PROJECT_ROOT / "a2a" / "server.py"), "--agent", "podcast", "--port", "8001"])
        p_sql = subprocess.Popen([py_exe, str(PROJECT_ROOT / "a2a" / "server.py"), "--agent", "sql", "--port", "8002"])
        p_rag = subprocess.Popen([py_exe, str(PROJECT_ROOT / "a2a" / "server.py"), "--agent", "rag", "--port", "8003"])
        procs = [p_podcast, p_sql, p_rag]
        
        # Keep process alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down all individual servers...")
        for p in procs:
            p.terminate()
        for p in procs:
            p.wait()
        print("All servers stopped cleanly.")


# ──────────────────────────────────────────────────────────────────────────────
# 4. ORCHESTRATION DEMO WITH AUTO SERVER CHECK
# ──────────────────────────────────────────────────────────────────────────────
async def run_demo_with_server_check(port: int = 8000, use_individual: bool = False):
    """Executes the orchestrator, auto-starting an in-process server if none is currently active."""
    import httpx

    if use_individual:
        # Check individual microservice ports
        print("Checking individual servers on ports 8001, 8002, 8003...")
        await run_multi_agent_orchestration(
            sql_url="http://127.0.0.1:8002",
            rag_url="http://127.0.0.1:8003",
            podcast_url="http://127.0.0.1:8001",
        )
        return

    base_url = f"http://127.0.0.1:{port}"
    server_online = False
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get(f"{base_url}/")
            if resp.status_code == 200:
                server_online = True
    except Exception:
        server_online = False

    if not server_online:
        print(f"⚠️ A2A Gateway is not running on {base_url}.")
        print("Starting in-process test runner for multi-agent demonstration...")
        import uvicorn
        
        from a2a.server import app
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
        server = uvicorn.Server(config)
        server_task = asyncio.create_task(server.serve())
        
        # Wait a moment for the server socket to bind
        await asyncio.sleep(1.0)
        try:
            await run_multi_agent_orchestration(base_url)
        finally:
            server.should_exit = True
            await server_task
    else:
        await run_multi_agent_orchestration(base_url)


# ──────────────────────────────────────────────────────────────────────────────
# 5. MAIN CLI ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="A2A Multi-Agent Framework CLI")
    parser.add_argument("--server", action="store_true", help="Launch the A2A server")
    parser.add_argument("--agent", choices=["podcast", "sql", "rag"], default=None,
                        help="When used with --server, runs a dedicated server for that agent only")
    parser.add_argument("--start-individual-servers", action="store_true",
                        help="Launch all 3 agents simultaneously on separate ports (8001, 8002, 8003)")
    parser.add_argument("--demo", action="store_true", help="Execute the 3-agent collaboration demo")
    parser.add_argument("--demo-individual", action="store_true",
                        help="Execute the collaboration demo targeting individual servers (8001, 8002, 8003)")
    parser.add_argument("--inspect-cards", action="store_true", help="Print all Agent Cards in terminal")
    parser.add_argument("--export-cards", action="store_true", help="Export Agent Cards as JSON files to a2a/cards")
    parser.add_argument("--query-agent", choices=["podcast", "sql", "rag"], help="Directly query a specific agent via A2A")
    parser.add_argument("--prompt", type=str, default="Can you provide an overview of your capabilities?", help="Prompt for --query-agent")
    parser.add_argument("--port", type=int, default=8000, help="Port for A2A server (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host for A2A server (default: 127.0.0.1)")
    args = parser.parse_args()

    if args.start_individual_servers:
        start_individual_servers()
    elif args.server:
        run_server(host=args.host, port=args.port, agent=args.agent)
    elif args.demo:
        asyncio.run(run_demo_with_server_check(port=args.port, use_individual=False))
    elif args.demo_individual:
        asyncio.run(run_demo_with_server_check(port=args.port, use_individual=True))
    elif args.inspect_cards:
        print_cards_inspection()
    elif args.export_cards:
        cards_dir = PROJECT_ROOT / "a2a" / "cards"
        export_all_cards(cards_dir, f"http://{args.host}:{args.port}")
    elif args.query_agent:
        asyncio.run(query_single_agent(args.query_agent, args.prompt, port=args.port))
    else:
        # Default behavior: print inspection and execute demo
        print_cards_inspection()
        print("\nExecuting multi-agent demo...\n")
        asyncio.run(run_demo_with_server_check(port=args.port, use_individual=False))


if __name__ == "__main__":
    main()
