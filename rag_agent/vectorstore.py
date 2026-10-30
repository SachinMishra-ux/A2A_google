"""Vector Store and Embedding Initialization for RAG Agent.

Sets up FAISS in-memory vector store containing mock enterprise documentation:
- Google Gemini capabilities and model variants
- FAISS vector database architecture
- LangChain orchestration framework
- Retrieval-Augmented Generation (RAG) concepts
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

# Knowledge Base Documents
KNOWLEDGE_DOCUMENTS = [
    Document(
        page_content=(
            "Google Gemini is a family of highly capable multimodal AI models developed by Google. "
            "The latest generation includes gemini-3.1-flash, gemini-3.1-flash-lite, and gemini-3.1-pro. "
            "These models support text, image, audio, video, and code processing with a 1-million token context window."
        ),
        metadata={"source": "Gemini Fact Sheet"}
    ),
    Document(
        page_content=(
            "FAISS (Facebook AI Similarity Search) is a library for efficient similarity search and clustering "
            "of dense vectors. It contains algorithms that search in sets of vectors of any size, up to ones that "
            "possibly do not fit in RAM. It is widely used in vector databases and semantic search systems."
        ),
        metadata={"source": "FAISS Documentation"}
    ),
    Document(
        page_content=(
            "LangChain is an open-source framework designed to simplify the creation of applications "
            "using large language models (LLMs). It provides components like prompt templates, models, "
            "output parsers, vectorstores, and agents that can be composed to build complex applications."
        ),
        metadata={"source": "LangChain Overview"}
    ),
    Document(
        page_content=(
            "Retrieval-Augmented Generation (RAG) is a technique that enhances LLMs by retrieving relevant "
            "information from an external data source (like a vector database) and injecting it into the prompt. "
            "This helps reduce model hallucinations, provides up-to-date information, and leverages proprietary data."
        ),
        metadata={"source": "RAG Architecture Guide"}
    ),
    Document(
        page_content=(
            "The Agent-to-Agent (A2A) protocol is an open standard designed by Google and hosted under "
            "the Linux Foundation. It enables autonomous AI agents to collaborate across different frameworks "
            "(Google ADK, LangGraph, CrewAI) through standardized Agent Cards, JSON-RPC 2.0 messages, and tasks."
        ),
        metadata={"source": "A2A Specification Whitepaper"}
    )
]

def get_vector_store():
    """Initializes and returns the FAISS vector database."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    if api_key:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            class PatchedGoogleGenerativeAIEmbeddings(GoogleGenerativeAIEmbeddings):
                def embed_documents(self, texts: list[str]) -> list[list[float]]:
                    return [self.embed_query(t) for t in texts]

            embeddings = PatchedGoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-2",
                google_api_key=api_key
            )
            return FAISS.from_documents(KNOWLEDGE_DOCUMENTS, embeddings)
        except Exception as e:
            print(f"[Warning] Failed to initialize live Gemini embeddings ({e}). Using deterministic embedding fallback.")

    # Lightweight deterministic embedding fallback for offline / mock testing
    from langchain_core.embeddings import Embeddings

    class DeterministicLocalEmbeddings(Embeddings):
        def embed_query(self, text: str) -> List[float]:
            import hashlib
            h = hashlib.sha256(text.lower().encode("utf-8")).digest()
            # Generate a 32-dimensional float vector normalized
            vec = [(b - 128) / 128.0 for b in h]
            return vec

        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            return [self.embed_query(t) for t in texts]

    return FAISS.from_documents(KNOWLEDGE_DOCUMENTS, DeterministicLocalEmbeddings())

# Global vector store instance
vector_store = get_vector_store()
