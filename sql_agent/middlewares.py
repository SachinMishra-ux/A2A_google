"""Prebuilt Middlewares for SQL Agent: Human-in-the-Loop & PII Redaction.

This module encapsulates:
1. HumanInTheLoopMiddleware: Halts query_sql_db tool execution for human review.
2. PIIMiddleware: Automatically redacts credit cards and email addresses from tool results.
"""

from langchain.agents.middleware.human_in_the_loop import HumanInTheLoopMiddleware
from langchain.agents.middleware.pii import PIIMiddleware

def get_hitl_middleware() -> HumanInTheLoopMiddleware:
    """Configures HITL middleware interrupting SQL queries."""
    return HumanInTheLoopMiddleware(
        interrupt_on={
            "query_sql_db": {
                "allowed_decisions": ["approve", "reject", "edit"]
            }
        }
    )

def get_pii_middlewares() -> list[PIIMiddleware]:
    """Configures PII redaction for credit cards and emails."""
    cc_middleware = PIIMiddleware(
        pii_type="credit_card",
        strategy="redact",
        apply_to_tool_results=True
    )
    email_middleware = PIIMiddleware(
        pii_type="email",
        strategy="redact",
        apply_to_tool_results=True
    )
    return [cc_middleware, email_middleware]
