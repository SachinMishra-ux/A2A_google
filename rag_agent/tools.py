"""Knowledge Base Retrieval Tools for RAG Agent."""

from langchain.tools import tool
from rag_agent.vectorstore import vector_store, KNOWLEDGE_DOCUMENTS

@tool("query_knowledge_base", description="Queries the vector database knowledge base for information matching the search query and returns relevant documents with source citations.")
def query_knowledge_base(query: str) -> str:
    """Queries the knowledge base and formats retrieved documents."""
    try:
        results = vector_store.similarity_search(query, k=2)
        
        # If fallback embedding produced low-quality match, do keyword search match
        if not results:
            q_lower = query.lower()
            results = [d for d in KNOWLEDGE_DOCUMENTS if any(w in d.page_content.lower() for w in q_lower.split() if len(w) > 3)][:2]

        if not results:
            return f"No matching information found in the knowledge base for: '{query}'"
        
        output_str = f"Matching Documents found for '{query}':\n\n"
        for i, doc in enumerate(results, 1):
            output_str += f"Document {i}:\n"
            output_str += f"Content: {doc.page_content}\n"
            output_str += f"Source Metadata: {doc.metadata.get('source', 'Unknown')}\n\n"
        return output_str
    except Exception as e:
        return f"Error querying knowledge base: {str(e)}"
