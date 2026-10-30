"""Entry Point for A2A Multi-Agent Framework.

Usage Options:
  1. Start A2A Federated Server:
     uv run python a2a/main.py --server [--port 8000]

  2. Run End-to-End Multi-Agent Orchestration Demo:
     uv run python a2a/main.py --demo [--port 8000]

  3. Inspect Advertised Agent Cards:
     uv run python a2a/main.py --inspect-cards

  4. Query a Specific Agent directly over A2A:
     uv run python a2a/main.py --query-agent sql --prompt "Show Alice's balance"
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

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

def print_cards_inspection():
    print("=" * 70)
    print(" 📇  A2A AGENT CARDS (OFFICIAL v1.0 MANIFESTS)")
    print("=" * 70)
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
    print("=" * 70)

async def query_single_agent(agent_name: str, prompt: str, port: int = 8000):
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

async def run_demo_with_server_check(port: int = 8000):
    """Checks if server is running; if not, informs user or executes orchestrator directly."""
    base_url = f"http://127.0.0.1:{port}"
    import httpx
    server_online = False
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get(f"{base_url}/")
            if resp.status_code == 200:
                server_online = True
    except Exception:
        server_online = False

    if not server_online:
        print(f"⚠️ A2A Server is not running on {base_url}.")
        print("Starting in-process test runner for multi-agent demonstration...")
        import uvicorn
        import multiprocessing
        
        # Start server in background thread / process
        from a2a.server import app
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
        server = uvicorn.Server(config)
        server_task = asyncio.create_task(server.serve())
        
        # Give server a moment to bind
        await asyncio.sleep(1.0)
        try:
            await run_multi_agent_orchestration(base_url)
        finally:
            server.should_exit = True
            await server_task
    else:
        await run_multi_agent_orchestration(base_url)

def main():
    parser = argparse.ArgumentParser(description="A2A Multi-Agent Framework CLI")
    parser.add_argument("--server", action="store_true", help="Launch the A2A federated FastAPI server")
    parser.add_argument("--demo", action="store_true", help="Execute the 3-agent collaboration demo")
    parser.add_argument("--inspect-cards", action="store_true", help="Print all Agent Cards")
    parser.add_argument("--export-cards", action="store_true", help="Export Agent Cards as JSON files to a2a/cards")
    parser.add_argument("--query-agent", choices=["podcast", "sql", "rag"], help="Directly query a specific agent via A2A")
    parser.add_argument("--prompt", type=str, default="Can you provide an overview of your capabilities?", help="Prompt for --query-agent")
    parser.add_argument("--port", type=int, default=8000, help="Port for A2A server (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host for A2A server (default: 127.0.0.1)")
    args = parser.parse_args()

    if args.server:
        run_server(host=args.host, port=args.port)
    elif args.demo:
        asyncio.run(run_demo_with_server_check(port=args.port))
    elif args.inspect_cards:
        print_cards_inspection()
    elif args.export_cards:
        cards_dir = PROJECT_ROOT / "a2a" / "cards"
        export_all_cards(cards_dir, f"http://{args.host}:{args.port}")
    elif args.query_agent:
        asyncio.run(query_single_agent(args.query_agent, args.prompt, port=args.port))
    else:
        # Default behavior: run inspection and then execute demo
        print_cards_inspection()
        print("\nExecuting multi-agent demo...\n")
        asyncio.run(run_demo_with_server_check(port=args.port))

if __name__ == "__main__":
    main()
