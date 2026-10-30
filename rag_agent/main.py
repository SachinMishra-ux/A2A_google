"""Entry Point for RAG Agent (LangChain + FAISS + Gemini).

Demonstrates:
1. Retrieval of grounded documents from FAISS vector store.
2. Grounded question answering citing sources.
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_agent.agent import run_rag_agent_query
from rag_agent.tools import query_knowledge_base

def main():
    parser = argparse.ArgumentParser(description="RAG Agent Entry Point (LangChain + FAISS)")
    parser.add_argument("--query", type=str, default="Can you explain what Google Gemini is and list some of the latest models?", help="Question for the RAG agent")
    parser.add_argument("--raw-retrieve", action="store_true", help="Directly query vector store and display raw retrieved documents")
    args = parser.parse_args()

    print("=" * 65)
    print(" 📚  LANGCHAIN RAG AGENT (FAISS + GROUNDED CITATIONS)")
    print("=" * 65)

    if args.raw_retrieve:
        print(f"\n[RAW RETRIEVAL] Query: '{args.query}'\n")
        output = query_knowledge_base.invoke({"query": args.query})
        print(output)
        return

    print(f"User Query: '{args.query}'\n")
    result = run_rag_agent_query(args.query)

    print("=== RAG AGENT RESPONSE ===")
    print(result.get("content"))
    print(f"\n[Execution Mode: {result.get('mode')}]")
    print("\n✅ Execution completed successfully.")

if __name__ == "__main__":
    main()
