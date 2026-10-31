# Google A2A Protocol — Interactive Web UI & Inspector

A clean, modern Google Material Design interface designed to demonstrate, test, and inspect the **Google Agent2Agent (A2A) Protocol** communicating with three specialized autonomous agents:
1. **SQL Agent** (built with LangChain + LangGraph + Human-in-the-Loop + PII masking)
2. **RAG Agent** (built with LangChain + FAISS Vector Store + Grounded Citations)
3. **Podcast Agent** (built with Google Agent Development Kit - ADK)
4. **A2A Orchestrator** (Multi-agent supervisor routing cross-domain missions across all agents)

---

## 🌟 Key Features

- **Automatic Intent Routing**: Enter any prompt in natural language; the A2A gateway analyzes the query and dispatches it to the best-suited agent.
- **Manual Mode Override**: Easily force a query to run through a specific agent (`SQL`, `RAG`, `Podcast`, or `Multi-Agent Orchestrator`).
- **Live Behind-the-Scenes Trace**:
  - Step-by-step lifecycle milestone tracker (Query Ingestion -> Card Resolution -> JSON-RPC 2.0 Dispatch -> Runtime Execution -> Artifact Delivery).
  - Complete **JSON-RPC 2.0 Request** inspector (`tasks/send` / `tasks/create`).
  - Complete **JSON-RPC 2.0 Response** inspector (`status`, `state`, `message`, `artifacts`).
  - Complete **Agent Card** schema inspector (`capabilities`, `skills`, `input_modes`, `version`).
- **Deliverables & Artifacts**: Live display and inspection of generated outputs (SQL tables, RAG answers with citations, and full multi-speaker podcast scripts).
- **Zero External Frontend Build Steps**: Pure HTML, CSS, and Vanilla JavaScript—no npm, node, or webpack needed!

---

## 🚀 How to Run the UI

### 1. Make sure your `.env` is configured
Ensure your Google Gemini API key is set:
```bash
GEMINI_API_KEY="your-gemini-api-key"
```

### 2. Start the Gateway and UI Server
Run the UI launcher:
```bash
uv run python ui/run.py
```
Or to automatically open the browser upon launch:
```bash
uv run python ui/run.py --open
```

### 3. Open in Your Browser
Navigate to:
```text
http://127.0.0.1:8000/ui/
```
*(Also accessible directly at `http://127.0.0.1:8000/` which automatically redirects to `/ui/`).*

---

## 🧪 Sample Prompts to Try in the UI

1. **SQL Agent Test**:
   > *"Show all users with a balance greater than $1,000 from the SQLite database."*
   - Behind the Scenes: The router identifies tabular/database intent, resolves `sql_agent` card, checks human-in-the-loop and PII masking, queries the database, and returns formatted rows.

2. **RAG Agent Test**:
   > *"Explain how Retrieval Augmented Generation works, including chunking, embedding, vector search, and citation grounding."*
   - Behind the Scenes: The router identifies research/documentation intent, queries FAISS vector store, grounds facts, and returns an answer with source citations.

3. **Podcast Agent Test**:
   > *"Generate a punchy 3-minute podcast script discussing the architectural differences between Google ADK and LangChain for production agents."*
   - Behind the Scenes: Dispatched to the Google ADK Podcast agent, generating structured speaker dialogue and emitting a podcast script artifact.

4. **Multi-Agent Orchestrator Mission**:
   > *"Check the database for top users, retrieve RAG best practices for customer communication, and create a podcast episode discussing data-driven customer loyalty."*
   - Behind the Scenes: Dispatched to the A2A Orchestrator, which splits the mission and invokes all 3 sub-agents sequentially over the A2A protocol.

---

## 📁 Folder Structure

```
ui/
├── index.html     # Google Material Design layout & component structure
├── styles.css     # Clean Google design system styling, responsive split view
├── app.js         # Reactive UI controller, JSON-RPC inspector, live stepper
├── run.py         # One-command server runner with automatic browser opening
└── README.md      # UI usage guide and documentation
```
