"""SQL Agent Definition and Compilation (LangChain + LangGraph).

This module compiles the SQL Agent equipped with HITL approvals,
PII redaction middlewares, and conversational checkpointer state memory.
"""

import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from sql_agent.database import query_sql_db
from sql_agent.middlewares import get_hitl_middleware, get_pii_middlewares

SYSTEM_PROMPT = (
    "You are a database assistant. Your goal is to run query_sql_db to retrieve user "
    "account details. The database contains a single table: "
    "users(id INTEGER, name TEXT, email TEXT, credit_card TEXT, balance REAL). "
    "Always use the exact column names: id, name, email, credit_card, balance. "
    "Synthesize and report the query results. "
    "Always respect redactions (e.g. [REDACTED_CREDIT_CARD]) in your final response."
)

def create_sql_agent_instance(model_name: str = "gemini-3.1-flash-lite"):
    """Instantiates and compiles the LangGraph SQL Agent."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None
    
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0, google_api_key=api_key)
    memory = MemorySaver()
    middlewares = [get_hitl_middleware()] + get_pii_middlewares()
    
    agent = create_agent(
        model=llm,
        tools=[query_sql_db],
        system_prompt=SYSTEM_PROMPT,
        middleware=middlewares,
        checkpointer=memory
    )
    return agent

# Cached default instance
sql_agent = create_sql_agent_instance()

def _format_content_to_str(content: Any) -> str:
    """Helper to ensure agent message content is always returned as a clean string."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        extracted = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                extracted.append(str(item["text"]))
            elif isinstance(item, str):
                extracted.append(item)
            elif hasattr(item, "text"):
                extracted.append(str(item.text))
            else:
                extracted.append(str(item))
        return "\n".join(extracted)
    return str(content)

def run_sql_agent_query(
    query_text: str,
    thread_id: str = "default_thread",
    decision: str = "approve",
    rejection_message: str = "Query rejected by human reviewer."
) -> Dict[str, Any]:
    """Executes a query through the SQL Agent, demonstrating HITL handling.
    
    Returns a structured dictionary containing the final response,
    interrupt details (if any), execution telemetry, and status.
    """
    agent = sql_agent or create_sql_agent_instance()
    llm_error = None
    
    if agent is not None:
        try:
            config = {"configurable": {"thread_id": thread_id}}
            # 1. First invocation (expecting HITL interrupt if query_sql_db is called)
            result = agent.invoke({"messages": [{"role": "user", "content": query_text}]}, config=config)
            
            state = agent.get_state(config)
            interrupt_info = None
            
            if state.next:
                for task in state.tasks:
                    if task.interrupts:
                        interrupt_val = task.interrupts[0].value
                        interrupt_info = {
                            "action_requests": interrupt_val.get("action_requests"),
                            "allowed_decisions": interrupt_val.get("review_configs")
                        }
                        break
                
                # 2. Resume execution based on decision
                if decision == "approve":
                    resume_cmd = Command(resume={"decisions": [{"type": "approve"}]})
                else:
                    resume_cmd = Command(resume={"decisions": [{"type": "reject", "message": rejection_message}]})
                    
                final_result = agent.invoke(resume_cmd, config=config)
                content = _format_content_to_str(final_result["messages"][-1].content)
                return {
                    "status": "completed",
                    "content": content,
                    "hitl_triggered": True,
                    "decision": decision,
                    "interrupt_info": interrupt_info,
                    "llm_called": True,
                    "execution_mode": "live_gemini_success",
                    "model": "gemini-3.1-flash-lite"
                }
            else:
                content = _format_content_to_str(result["messages"][-1].content)
                return {
                    "status": "completed",
                    "content": content,
                    "hitl_triggered": False,
                    "decision": None,
                    "interrupt_info": None,
                    "llm_called": True,
                    "execution_mode": "live_gemini_success",
                    "model": "gemini-3.1-flash-lite"
                }
        except Exception as e:
            llm_error = str(e)

    # Deterministic Real Database Fallback with actual SQLite query and PII redaction
    offline_res = run_offline_sql_query(query_text, decision, rejection_message)
    offline_res["llm_called"] = True if agent is not None else False
    offline_res["llm_error"] = llm_error
    offline_res["execution_mode"] = "live_gemini_billing_blocked" if (llm_error and "PERMISSION_DENIED" in llm_error) else "deterministic_sqlite"
    offline_res["model"] = "gemini-3.1-flash-lite (Google AI Studio Billing Blocked)" if (llm_error and "PERMISSION_DENIED" in llm_error) else "sqlite_direct"
    return offline_res

def run_offline_sql_query(
    query_text: str,
    decision: str = "approve",
    rejection_message: str = "Access denied by human reviewer."
) -> Dict[str, Any]:
    """Deterministic offline simulation for testing without active Gemini credentials."""
    import re
    # Extract name or table request
    lower = query_text.lower()
    sql_to_run = "SELECT * FROM users"
    if "alice" in lower:
        sql_to_run = "SELECT * FROM users WHERE name LIKE '%Alice%'"
    elif "bob" in lower:
        sql_to_run = "SELECT * FROM users WHERE name LIKE '%Bob%'"
    elif "balance" in lower:
        sql_to_run = "SELECT name, balance FROM users"

    interrupt_info = {
        "action_requests": [{"tool": "query_sql_db", "args": {"query": sql_to_run}}],
        "allowed_decisions": ["approve", "reject", "edit"]
    }

    if decision == "reject":
        return {
            "status": "completed",
            "content": f"[Human Reviewer Action] {rejection_message}",
            "hitl_triggered": True,
            "decision": "reject",
            "interrupt_info": interrupt_info
        }

    raw_result = query_sql_db.invoke({"query": sql_to_run})
    
    # Redact PII (Credit Cards & Emails)
    redacted = re.sub(r"\d{4}-\d{4}-\d{4}-\d{4}", "[REDACTED_CREDIT_CARD]", raw_result)
    redacted = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]", redacted)

    return {
        "status": "completed",
        "content": f"Database Query Executed (PII Redacted):\n\n{redacted}",
        "hitl_triggered": True,
        "decision": "approve",
        "interrupt_info": interrupt_info
    }
