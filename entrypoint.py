#!/usr/bin/env python3
"""
Production Entrypoint for Google A2A Multi-Agent System.

Ensures that upon deployment (Docker, Cloud Run, Kubernetes, ECS, Azure Container Apps):
1. All three agents (SQL, RAG, Podcast) are automatically pre-initialized and ready.
2. The A2A Unified Gateway and Inspector UI start on the configured PORT (default: 8000).
3. If A2A_MODE=multi_process is configured, it automatically launches all 3 individual
   microservices (Ports 8001, 8002, 8003) alongside the Gateway.

Usage:
  python entrypoint.py
  python entrypoint.py --multi-process
"""

import os
import sys
import time
import signal
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

load_dotenv(WORKSPACE_ROOT / ".env")

def prewarm_agents():
    """Verifies and pre-warms all three agent runtimes on container startup."""
    print("=" * 75)
    print(" 🚀  PRE-WARMING GOOGLE A2A MULTI-AGENT CLUSTER")
    print("=" * 75)
    
    # 1. SQL Agent Pre-warm
    try:
        from sql_agent.database import init_database, query_sql_db
        init_database()
        sample_users = query_sql_db.invoke({"query": "SELECT COUNT(*) AS total_users FROM users"})
        print(f" ✅ [SQL Agent]     : SQLite Database initialized ({sample_users.strip()})")
        print("                     LangGraph + Human-in-the-Loop + PII Redaction active")
    except Exception as e:
        print(f" ⚠️  [SQL Agent]     : Initialization note: {e}")

    # 2. RAG Agent Pre-warm
    try:
        from rag_agent.vectorstore import get_vector_store, KNOWLEDGE_DOCUMENTS
        vs = get_vector_store()
        print(f" ✅ [RAG Agent]     : FAISS Vector Store active ({len(KNOWLEDGE_DOCUMENTS)} document chunks indexed)")
        print("                     Semantic search & citation grounding ready")
    except Exception as e:
        print(f" ⚠️  [RAG Agent]     : Initialization note: {e}")

    # 3. Podcast Agent Pre-warm
    try:
        from podcast_agent.agent import root_agent
        print(f" ✅ [Podcast Agent] : Google ADK Studio active (Coordinator: {root_agent.name})")
        print(f"                     Model: {root_agent.model} • Subagents: {[sa.name for sa in root_agent.sub_agents]}")
    except Exception as e:
        print(f" ⚠️  [Podcast Agent] : Initialization note: {e}")

    print("=" * 75 + "\n")

def run_unified_mode(host: str, port: int):
    """Runs the unified multi-agent server hosting all 3 agents simultaneously on port 8000."""
    import uvicorn
    from a2a.server import create_gateway_app

    print("🌟 MODE: UNIFIED MULTI-AGENT FEDERATION (Single Port)")
    print(f"📡 A2A Gateway Endpoint : http://{host}:{port}/a2a")
    print(f"🗄️ SQL Agent Endpoint   : http://{host}:{port}/sql/a2a")
    print(f"📚 RAG Agent Endpoint   : http://{host}:{port}/rag/a2a")
    print(f"🎙️ Podcast Agent Endpoint: http://{host}:{port}/podcast/a2a")
    print(f"🖥️ Interactive Web UI   : http://{host}:{port}/ui/")
    print(f"📋 Discovery Manifest   : http://{host}:{port}/.well-known/agent-card.json")
    print("=" * 75)
    print("Server ready to accept requests.\n")

    app = create_gateway_app()
    uvicorn.run(app, host=host, port=port, log_level="info")

def run_multiprocess_mode(host: str, gateway_port: int):
    """Runs 3 separate microservice server processes (8001, 8002, 8003) + Gateway (8000)."""
    import uvicorn
    from a2a.server import create_gateway_app

    py_exe = sys.executable
    procs = []

    print("🌟 MODE: MULTI-PROCESS MICROSERVICES")
    print("Spawning 3 background agent microservices:")
    
    # Port 8001: Podcast Agent
    p_pod = subprocess.Popen([py_exe, str(WORKSPACE_ROOT / "a2a" / "server.py"), "--agent", "podcast", "--port", "8001"])
    procs.append(p_pod)
    print(" • [PID %d] Podcast Agent on http://127.0.0.1:8001/a2a" % p_pod.pid)

    # Port 8002: SQL Agent
    p_sql = subprocess.Popen([py_exe, str(WORKSPACE_ROOT / "a2a" / "server.py"), "--agent", "sql", "--port", "8002"])
    procs.append(p_sql)
    print(" • [PID %d] SQL Agent on http://127.0.0.1:8002/a2a" % p_sql.pid)

    # Port 8003: RAG Agent
    p_rag = subprocess.Popen([py_exe, str(WORKSPACE_ROOT / "a2a" / "server.py"), "--agent", "rag", "--port", "8003"])
    procs.append(p_rag)
    print(" • [PID %d] RAG Agent on http://127.0.0.1:8003/a2a" % p_rag.pid)

    time.sleep(1.5)

    def cleanup(sig=None, frame=None):
        print("\nShutting down all agent processes...")
        for p in procs:
            p.terminate()
        for p in procs:
            p.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print(f"\nLaunching Master Gateway & Web UI on http://{host}:{gateway_port}/ui/...")
    print("=" * 75)

    app = create_gateway_app()
    try:
        uvicorn.run(app, host=host, port=gateway_port, log_level="info")
    finally:
        cleanup()

def main():
    parser = argparse.ArgumentParser(description="Google A2A Production Cluster Entrypoint")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"), help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")), help="Port to bind (default: 8000)")
    parser.add_argument("--multi-process", action="store_true", default=(os.environ.get("A2A_MODE", "").lower() == "multi_process"),
                        help="Launch separate microservice processes on ports 8001, 8002, 8003")
    args = parser.parse_args()

    prewarm_agents()

    if args.multi-process:
        run_multiprocess_mode(args.host, args.port)
    else:
        run_unified_mode(args.host, args.port)

if __name__ == "__main__":
    main()
