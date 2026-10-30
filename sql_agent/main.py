"""Entry Point for SQL Agent (LangChain + LangGraph).

Demonstrates:
1. Tool-based query execution against the SQLite database.
2. Human-in-the-Loop (HITL) interrupt handling with Approval & Rejection flows.
3. Automated PII Redaction of Credit Card and Email fields.
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sql_agent.agent import run_sql_agent_query
from sql_agent.database import query_sql_db

def main():
    parser = argparse.ArgumentParser(description="SQL Agent Entry Point (LangChain + LangGraph)")
    parser.add_argument("--query", type=str, default="Can you fetch Alice Smith's credit card, email, and balance?", help="Natural language query for the SQL database")
    parser.add_argument("--decision", choices=["approve", "reject"], default="approve", help="HITL decision (approve or reject)")
    parser.add_argument("--reject-msg", type=str, default="Access to financial balance denied by security policy.", help="Custom rejection message if decision is reject")
    parser.add_argument("--raw-sql", type=str, default=None, help="Directly test the read-only SQL tool with a raw SELECT query")
    args = parser.parse_args()

    print("=" * 65)
    print(" 🛡️  LANGCHAIN SQL AGENT (HITL + PII REDACTION)")
    print("=" * 65)

    if args.raw_sql:
        print(f"\n[DIRECT TOOL EXECUTION] Running SQL: '{args.raw_sql}'")
        output = query_sql_db.invoke({"query": args.raw_sql})
        print("\n=== RAW TOOL RESULT ===")
        print(output)
        return

    print(f"User Query:      '{args.query}'")
    print(f"HITL Decision:   {args.decision.upper()}")
    
    result = run_sql_agent_query(
        query_text=args.query,
        thread_id="cli_session_1",
        decision=args.decision,
        rejection_message=args.reject_msg
    )

    if result.get("hitl_triggered"):
        print("\n🛑 [HITL Middleware Triggered]")
        info = result.get("interrupt_info") or {}
        print(f"   Action Requests: {info.get('action_requests')}")
        print(f"   Allowed Decisions: {info.get('allowed_decisions')}")
        print(f"--> Human Decision Applied: {args.decision.upper()}")

    print("\n=== FINAL AGENT RESPONSE ===")
    print(result.get("content"))
    print("\n✅ Execution completed successfully.")

if __name__ == "__main__":
    main()
