"""SQLite In-Memory Database and Query Tools for SQL Agent.

This module initializes a database containing sensitive user records
and exposes a read-only SELECT tool.
"""

import sqlite3
from typing import Optional
from langchain.tools import tool

# 1. Initialize SQLite Database Connection
db_conn = sqlite3.connect(":memory:", check_same_thread=False)

def init_database(conn: sqlite3.Connection = db_conn):
    """Creates the users table and seeds sensitive test records."""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        credit_card TEXT,
        balance REAL
    )
    """)
    
    # Clean and re-seed
    cursor.execute("DELETE FROM users")
    
    users_data = [
        (1, "Alice Smith", "alice.smith@example.com", "4111-1111-1111-1111", 1250.00),
        (2, "Bob Jones", "bob.jones@gmail.com", "5555-5555-5555-4444", 3500.50),
        (3, "Charlie Davis", "charlie.d@company.org", "3782-8224-6310-0050", 890.25)
    ]
    cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?)", users_data)
    conn.commit()

# Seed database on import
init_database()

# 2. Define SELECT-only query tool
@tool("query_sql_db", description="Executes a read-only SQL SELECT query against the users database and returns tabular results. Input must be a valid SQL SELECT query.")
def query_sql_db(query: str) -> str:
    """Query the SQL database with read-only constraint."""
    try:
        clean_query = query.strip().upper()
        if not clean_query.startswith("SELECT"):
            return "Error: Security Violation. Only read-only SELECT queries are allowed."
        
        cursor = db_conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            return "Query executed successfully. No rows returned."
        
        columns = [desc[0] for desc in cursor.description]
        output = " | ".join(columns) + "\n" + "-" * 55 + "\n"
        for row in rows:
            output += " | ".join(str(val) for val in row) + "\n"
        return output
    except Exception as e:
        return f"SQL Query execution failed with error: {str(e)}"
