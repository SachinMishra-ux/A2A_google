# Agent-to-Agent (A2A) Federated Multi-Agent System

This repository provides an enterprise implementation of Google's **Agent-to-Agent (A2A)** Protocol, orchestrating three heterogeneous AI agents built across different frameworks (**Google ADK** and **LangChain**):

1. **Podcast Agent** (`podcast_agent/`): Executive Producer system built on **Google ADK** (Agent Development Kit). Coordinates topic research, multi-speaker dialogue scriptwriting (Alex & Morgan personas), and neural TTS audio synthesis.
2. **SQL Database Agent** (`sql_agent/`): Enterprise database assistant built on **LangChain** and **LangGraph**. Executes read-only SQLite queries strictly governed by **Human-in-the-Loop (HITL)** approvals and automated **PII redaction** (Credit Cards & Emails).
3. **RAG Knowledge Agent** (`rag_agent/`): Retrieval-Augmented Generation agent built on **LangChain** and **FAISS** vector store. Retrieves grounded technical documentation and provides cited answers without hallucinations.
4. **A2A Protocol Gateway & Orchestrator** (`a2a/`): Standardized communication layer implementing the official **A2A v1.0 Specification** (JSON-RPC 2.0, Agent Cards, stateful Tasks, and Artifact handoffs) connecting all three agents.

Also included is the complete Google-styled executive briefing document:
📄 **[`Google_A2A_Protocol_Comprehensive_Guide.docx`](Google_A2A_Protocol_Comprehensive_Guide.docx)**

---

## 📁 Repository Directory Structure

```text
A2A_google/
├── podcast_agent/                # Agent 1: Google ADK Podcast Studio
│   ├── main.py                  # CLI Entry point (inspection & script generation)
│   ├── agent.py                 # Coordinator root_agent definition
│   ├── prompt.py                # System instructions & context caching prompts
│   ├── schemas.py               # Pydantic schemas (PodcastPlan, Script, DialogueTurn)
│   ├── subagents/               # Sub-agents: researcher, scriptwriter, audio_producer
│   └── tools/                   # Tools: audio_generator (Edge TTS), document_reader
│
├── sql_agent/                    # Agent 2: LangChain SQL Agent with HITL & PII
│   ├── main.py                  # CLI Entry point (approval & rejection tests)
│   ├── agent.py                 # LangGraph agent compilation & checkpointer memory
│   ├── database.py              # SQLite in-memory database & SELECT tool
│   ├── middlewares.py           # HumanInTheLoopMiddleware & PIIMiddleware
│   └── __init__.py
│
├── rag_agent/                    # Agent 3: LangChain RAG Agent with FAISS
│   ├── main.py                  # CLI Entry point (grounded Q&A & citations)
│   ├── agent.py                 # Agent definition & prompt with source citation rules
│   ├── tools.py                 # query_knowledge_base vector similarity tool
│   ├── vectorstore.py           # FAISS store initialization & mock knowledge base
│   └── __init__.py
│
├── a2a/                          # A2A Protocol Implementation & Orchestration
│   ├── main.py                  # Main CLI entry point for A2A operations
│   ├── server.py                # FastAPI A2A JSON-RPC 2.0 Server & Agent Card host
│   ├── client.py                # Reusable A2A Client (discovery, message/send, tasks/get)
│   ├── router.py                # Intelligent Intent Routing & A2A Trace Collector
│   ├── orchestrator.py          # End-to-end 3-agent collaboration workflow
│   ├── models.py                # Canonical A2A v1.0 models (AgentCard, Task, Message, Artifact)
│   ├── agent_cards.py           # Agent Card declarations for all 3 agents
│   └── cards/                   # Exported static JSON Agent Cards
│
├── ui/                           # Interactive Web UI & Live A2A Inspector
│   ├── index.html               # Google Material UI layout & split-view workspace
│   ├── styles.css               # Google design tokens, card styles & animations
│   ├── app.js                   # Client controller, live trace stepper & JSON-RPC viewer
│   ├── run.py                   # One-command server and UI launcher
│   └── README.md                # UI guide & test walkthroughs
│
├── Google_A2A_Protocol_Comprehensive_Guide.docx  # Google-styled Word report
├── A2A_Architecture_Visualization.html           # Standalone interactive architecture guide
├── diagram1_mcp_vs_a2a.png                       # Architectural boundary diagram
├── diagram2_a2a_lifecycle.png                    # 4-step task lifecycle diagram
├── diagram3_local_multiagent.png                 # Local communication architecture
├── diagram4_cloud_deployment.png                 # Enterprise cloud deployment diagram
└── pyproject.toml                                # Project dependencies & configuration
```

---

## ⚙️ Environment Setup & Installation

The project uses `uv` for fast, deterministic Python virtual environment management.

### 1. Install Dependencies

```bash
uv sync
```

*(Or install via pip if not using uv):*

```bash
pip install -r pyproject.toml
```

### 2. Configure API Keys (Optional)

Create a `.env` file in the project root if you want to use live Gemini models:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

> **Note:** If no API key is provided, all agents automatically switch to intelligent offline/mock demonstration modes so you can test and run the entire multi-agent pipeline immediately!

---

## 🖥️ Interactive Web UI & Live Protocol Inspector

You can launch and interact with all agents via a visual Google Material Design web interface:

```bash
uv run python ui/run.py
```
*(Or `uv run python ui/run.py --open` to automatically launch your default browser).*

Open `http://127.0.0.1:8000/ui/` in your browser. From here you can:
- **Type any query** and watch the A2A intent classifier automatically route it to the right agent (`SQL`, `RAG`, `Podcast`, or `Multi-Agent Orchestrator`).
- **Inspect Behind the Scenes in Real Time**:
  - Step-by-step milestone timeline.
  - Raw **JSON-RPC 2.0 Request** payload (`tasks/send` / `tasks/create`).
  - Raw **JSON-RPC 2.0 Response** payload with state, status, and message parts.
  - Complete **Agent Card** schema defining capabilities, skills, and I/O contracts.
  - Generated **Artifacts** (e.g. podcast scripts, query tables).
- **Interactive Architecture Documentation**: View the full interactive guide at `http://127.0.0.1:8000/A2A_Architecture_Visualization.html`.

---

## 🚀 How to Run Each Component

### 1. Run the Podcast Agent (Google ADK)

Test the Podcast Agent standalone:

```bash
# Run agent inspection & dry-run podcast script generation
uv run python podcast_agent/main.py --dry-run

# Run with a custom topic
uv run python podcast_agent/main.py --topic "Decentralized AI Agents"
```

### 2. Run the SQL Agent (LangChain + HITL + PII)

Test the SQL Agent standalone with human review controls:

```bash
# Run query with Human-in-the-Loop APPROVAL (Redacts credit card & email)
uv run python sql_agent/main.py --query "Can you fetch Alice Smith's credit card and balance?" --decision approve

# Run query with Human-in-the-Loop REJECTION
uv run python sql_agent/main.py --query "What is Bob Jones's balance?" --decision reject

# Test direct SQL tool execution
uv run python sql_agent/main.py --raw-sql "SELECT id, name, balance FROM users"
```

### 3. Run the RAG Agent (LangChain + FAISS)

Test the RAG Agent standalone:

```bash
# Run grounded Q&A query citing sources
uv run python rag_agent/main.py --query "Can you explain what Google Gemini is and list some of the latest models?"

# Directly view raw retrieved documents from FAISS
uv run python rag_agent/main.py --query "Explain FAISS similarity search" --raw-retrieve
```

---

## 🌐 A2A Protocol Communication & Orchestration

The `a2a/` package connects all three agents over standard **JSON-RPC 2.0 over HTTP**.

### 1. Run the End-to-End Multi-Agent Collaboration Demo

This command boots the A2A server and executes the full cross-agent workflow:

```bash
uv run python a2a/main.py --demo
```

**What happens during the demo:**

1. **Discovery:** The Orchestrator inspects the Agent Cards from `/.well-known/agent-card.json` for all three agents.
2. **SQL Delegation:** Dispatches a query to `sql_agent` via A2A `message/send` $\rightarrow$ verifies HITL approval and extracts PII-redacted balance.
3. **RAG Delegation:** Dispatches a technical query to `rag_agent` via A2A `message/send` $\rightarrow$ retrieves grounded Google Gemini architectural facts with citations.
4. **Podcast Synthesis:** Passes the outputs from both the SQL and RAG agents to `podcast_agent` via A2A $\rightarrow$ synthesizes a complete 2-speaker dialogue script artifact between Alex (Host) and Morgan (Expert).

---

### 2. Run the A2A Federated Server Standalone

Launch the server hosting all three agent endpoints on port 8000:

```bash
uv run python a2a/main.py --server --port 8000
```

While running, you can explore the following live URLs in your browser or curl:

* **Gateway Status:** `http://127.0.0.1:8000/`
* **Root Federation Card:** `http://127.0.0.1:8000/.well-known/agent-card.json`
* **Podcast Agent Card:** `http://127.0.0.1:8000/podcast/.well-known/agent-card.json`
* **SQL Agent Card:** `http://127.0.0.1:8000/sql/.well-known/agent-card.json`
* **RAG Agent Card:** `http://127.0.0.1:8000/rag/.well-known/agent-card.json`

---

### 3. Query an Individual Agent Directly over A2A

With the server running (or via direct invocation):

```bash
# Query SQL Agent via A2A
uv run python a2a/main.py --query-agent sql --prompt "Show Bob Jones's balance"

# Query RAG Agent via A2A
uv run python a2a/main.py --query-agent rag --prompt "Explain FAISS similarity search"

# Query Podcast Agent via A2A
uv run python a2a/main.py --query-agent podcast --prompt "Multi-Agent Security Architecture"
```

---

### 4. Inspect or Export Agent Cards

```bash
# Inspect all Agent Cards in terminal
uv run python a2a/main.py --inspect-cards

# Export Agent Cards as static JSON files to a2a/cards/
uv run python a2a/main.py --export-cards
```

---

## 📊 Architectural Diagrams

| Diagram            | Focus                                                         | Description                                                                                                                       |
| :----------------- | :------------------------------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------- |
| **Figure 1** | [diagram1_mcp_vs_a2a.png](diagram1_mcp_vs_a2a.png)             | **A2A vs. MCP**: MCP for agent-to-tool integration vs. A2A for agent-to-agent collaboration.                                |
| **Figure 2** | [diagram2_a2a_lifecycle.png](diagram2_a2a_lifecycle.png)       | **A2A Task Lifecycle**: Discovery $\rightarrow$ Task Dispatch $\rightarrow$ Execution $\rightarrow$ Artifact Handoff. |
| **Figure 3** | [diagram3_local_multiagent.png](diagram3_local_multiagent.png) | **Local Communication**: Localhost JSON-RPC 2.0 communication between client and server agents.                             |
| **Figure 4** | [diagram4_cloud_deployment.png](diagram4_cloud_deployment.png) | **Production Cloud Topology**: Google Cloud Run, Vertex AI Agent Engine, Apigee, OAuth2, and multi-cloud federation.        |

---

## 📜 Deliverable Research Report

The deep-dive architectural Word document is formatted in **Google Material Design** (Arial typography, Google Blue `#1A73E8` headings, subtle callout cards, styled tables, and high-DPI visual diagrams):

📄 **[Google_A2A_Protocol_Comprehensive_Guide.docx](Google_A2A_Protocol_Comprehensive_Guide.docx)**
