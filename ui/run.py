#!/usr/bin/env python3
"""
Launcher for Google A2A Protocol Interactive UI.
Runs the FastAPI unified gateway server on port 8000 and serves the UI.

Usage:
  uv run python ui/run.py
  uv run python ui/run.py --open   (automatically opens browser)
"""

import sys
import os
import argparse
import webbrowser
from dotenv import load_dotenv

# Ensure workspace root is in python path
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

load_dotenv(os.path.join(WORKSPACE_ROOT, ".env"))

import uvicorn
from a2a.server import create_app

def main():
    parser = argparse.ArgumentParser(description="Google A2A Protocol UI Gateway")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--open", action="store_true", help="Automatically open browser on launch")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}/ui/"
    print("=" * 70)
    print("🚀 Google Agent2Agent (A2A) Interactive Protocol Gateway & UI")
    print("=" * 70)
    print(f"📡 A2A Server Endpoint : http://{args.host}:{args.port}/tasks/send")
    print(f"🖥️ Interactive Web UI   : {url}")
    print(f"📋 Agent Cards Metadata: http://{args.host}:{args.port}/api/agents")
    print(f"🏛️ Architecture Guide  : http://{args.host}:{args.port}/A2A_Architecture_Visualization.html")
    print("=" * 70)
    print("Press Ctrl+C to stop the server.\n")

    if args.open:
        webbrowser.open(url)

    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")

if __name__ == "__main__":
    main()
