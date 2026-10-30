"""RAG Agent Module with FAISS Vector Search and Gemini."""

from rag_agent.vectorstore import vector_store, get_vector_store
from rag_agent.tools import query_knowledge_base
from rag_agent.agent import create_rag_agent_instance, run_rag_agent_query, rag_agent

__all__ = [
    "vector_store",
    "get_vector_store",
    "query_knowledge_base",
    "create_rag_agent_instance",
    "run_rag_agent_query",
    "rag_agent",
]
