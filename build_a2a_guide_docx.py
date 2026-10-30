import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

# Colors
C_GOOGLE_BLUE = RGBColor(26, 115, 232)      # #1A73E8
C_GOOGLE_DARK = RGBColor(32, 33, 36)        # #202124
C_GOOGLE_MUTED = RGBColor(95, 99, 104)      # #5F6368
C_GOOGLE_GREEN = RGBColor(30, 142, 62)      # #1E8E3E
C_GOOGLE_RED = RGBColor(234, 67, 53)        # #EA4335
C_GOOGLE_AMBER = RGBColor(176, 96, 0)       # #B06000
C_WHITE = RGBColor(255, 255, 255)

HEX_GOOGLE_BLUE = "1A73E8"
HEX_LIGHT_BLUE = "E8F0FE"
HEX_LIGHT_GRAY = "F8F9FA"
HEX_CODE_BG = "F1F3F4"
HEX_BORDER = "DADCE0"
HEX_GREEN = "1E8E3E"
HEX_LIGHT_GREEN = "E6F4EA"
HEX_AMBER = "FBBC04"
HEX_LIGHT_AMBER = "FEF7E0"

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_cell_borders(cell, top="none", bottom="none", left="none", right="none", 
                     color="DADCE0", sz="4"):
    tcPr = cell._tc.get_or_add_tcPr()
    borders_xml = f'<w:tcBorders {nsdecls("w")}>'
    
    for side, val in [("top", top), ("left", left), ("bottom", bottom), ("right", right)]:
        if val == "none":
            borders_xml += f'<w:{side} w:val="none"/>'
        elif val == "single":
            borders_xml += f'<w:{side} w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
    borders_xml += '</w:tcBorders>'
    tcPr.append(parse_xml(borders_xml))

def add_callout(doc, text, title="NOTE", callout_type="info"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.8)
    
    bg_color = HEX_LIGHT_BLUE if callout_type == "info" else (HEX_LIGHT_GREEN if callout_type == "success" else HEX_LIGHT_AMBER)
    border_color = HEX_GOOGLE_BLUE if callout_type == "info" else (HEX_GREEN if callout_type == "success" else "B06000")
    title_color = C_GOOGLE_BLUE if callout_type == "info" else (C_GOOGLE_GREEN if callout_type == "success" else C_GOOGLE_AMBER)
    
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    set_cell_borders(cell, left="single", color=border_color, sz="24") # 3pt left bar
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    
    run_title = p.add_run(f"[{title}] ")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(9.5)
    run_title.font.bold = True
    run_title.font.color.rgb = title_color
    
    run_text = p.add_run(text)
    run_text.font.name = "Arial"
    run_text.font.size = Pt(9.5)
    run_text.font.color.rgb = C_GOOGLE_DARK
    
    # spacing after callout
    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_before = Pt(0)
    p_spacer.paragraph_format.space_after = Pt(4)

def add_code_block(doc, code_str, caption=None):
    if caption:
        p_cap = doc.add_paragraph()
        p_cap.paragraph_format.space_before = Pt(6)
        p_cap.paragraph_format.space_after = Pt(2)
        r_cap = p_cap.add_run(f"Code Snippet: {caption}")
        r_cap.font.name = "Arial"
        r_cap.font.size = Pt(9)
        r_cap.font.bold = True
        r_cap.font.color.rgb = C_GOOGLE_MUTED

    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.8)
    set_cell_background(cell, HEX_CODE_BG)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    set_cell_borders(cell, top="single", bottom="single", left="single", right="single", color=HEX_BORDER, sz="6")
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    
    run = p.add_run(code_str)
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = C_GOOGLE_DARK
    
    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_before = Pt(0)
    p_spacer.paragraph_format.space_after = Pt(4)

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(15)
    run.font.bold = True
    run.font.color.rgb = C_GOOGLE_BLUE
    return p

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = C_GOOGLE_DARK
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(9)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(10.5)
    run.font.bold = True
    run.font.color.rgb = C_GOOGLE_MUTED
    return p

def add_body_p(doc, text, bold_prefix=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Arial"
        r_pre.font.size = Pt(10)
        r_pre.font.bold = True
        r_pre.font.color.rgb = C_GOOGLE_DARK
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(10)
    run.font.color.rgb = C_GOOGLE_DARK
    return p

def add_bullet_p(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Arial"
        r_pre.font.size = Pt(9.8)
        r_pre.font.bold = True
        r_pre.font.color.rgb = C_GOOGLE_DARK
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(9.8)
    run.font.color.rgb = C_GOOGLE_DARK
    return p

def add_image_figure(doc, img_path, caption):
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(2)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=Inches(6.6))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(0)
        p_cap.paragraph_format.space_after = Pt(8)
        run_cap = p_cap.add_run(f"Figure: {caption}")
        run_cap.font.name = "Arial"
        run_cap.font.size = Pt(8.5)
        run_cap.font.italic = True
        run_cap.font.color.rgb = C_GOOGLE_MUTED

def add_styled_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    # Header row
    hdr_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        hdr_cells[i].text = ""
        p = hdr_cells[i].paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(header_text)
        run.font.name = "Arial"
        run.font.size = Pt(9.5)
        run.font.bold = True
        run.font.color.rgb = C_WHITE
        set_cell_background(hdr_cells[i], HEX_GOOGLE_BLUE)
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
        set_cell_borders(hdr_cells[i], top="single", bottom="single", left="single", right="single", color=HEX_BORDER, sz="4")
        if col_widths and i < len(col_widths):
            hdr_cells[i].width = Inches(col_widths[i])
            
    # Body rows
    for r_idx, row_data in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        bg_col = HEX_LIGHT_GRAY if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, cell_value in enumerate(row_data):
            row_cells[c_idx].text = ""
            p = row_cells[c_idx].paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            run = p.add_run(cell_value)
            run.font.name = "Arial"
            run.font.size = Pt(9)
            run.font.color.rgb = C_GOOGLE_DARK
            set_cell_background(row_cells[c_idx], bg_col)
            set_cell_margins(row_cells[c_idx], top=100, bottom=100, left=140, right=140)
            set_cell_borders(row_cells[c_idx], top="single", bottom="single", left="single", right="single", color=HEX_BORDER, sz="4")
            if col_widths and c_idx < len(col_widths):
                row_cells[c_idx].width = Inches(col_widths[c_idx])

    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_before = Pt(0)
    p_spacer.paragraph_format.space_after = Pt(4)

def build_document():
    doc = docx.Document()
    
    # Page Setup (0.75 in margins for modern Google Docs look)
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        
        # Header & Footer
        header = section.header
        p_hdr = header.paragraphs[0]
        p_hdr.text = "Google Research & Open Source Technical Briefing | A2A Protocol Architecture"
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_hdr.runs[0].font.name = "Arial"
        p_hdr.runs[0].font.size = Pt(8)
        p_hdr.runs[0].font.color.rgb = C_GOOGLE_MUTED
        
        footer = section.footer
        p_ftr = footer.paragraphs[0]
        p_ftr.text = "Confidential & Technical Guidance • Powered by Google ADK & A2A Open Specification"
        p_ftr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ftr.runs[0].font.name = "Arial"
        p_ftr.runs[0].font.size = Pt(8)
        p_ftr.runs[0].font.color.rgb = C_GOOGLE_MUTED

    # Document Header Box (Google Docs Style Header Block)
    hdr_table = doc.add_table(rows=1, cols=1)
    hdr_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_table.autofit = False
    hdr_cell = hdr_table.cell(0, 0)
    hdr_cell.width = Inches(6.8)
    set_cell_background(hdr_cell, HEX_LIGHT_BLUE)
    set_cell_margins(hdr_cell, top=180, bottom=180, left=220, right=220)
    set_cell_borders(hdr_cell, top="none", bottom="single", left="single", right="none", color=HEX_GOOGLE_BLUE, sz="24")
    
    p_title = hdr_cell.paragraphs[0]
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    r_tag = p_title.add_run("GOOGLE CLOUD & OPEN-SOURCE ECOSYSTEMS • ARCHITECTURAL REPORT\n")
    r_tag.font.name = "Arial"
    r_tag.font.size = Pt(8.5)
    r_tag.font.bold = True
    r_tag.font.color.rgb = C_GOOGLE_BLUE
    
    r_title = p_title.add_run("Agent-to-Agent (A2A) Protocol: The Complete Architectural & Implementation Guide")
    r_title.font.name = "Arial"
    r_title.font.size = Pt(17)
    r_title.font.bold = True
    r_title.font.color.rgb = C_GOOGLE_DARK
    
    p_sub = hdr_cell.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(4)
    p_sub.paragraph_format.space_after = Pt(4)
    r_sub = p_sub.add_run("A deep architectural analysis of the A2A open standard: cross-framework orchestration, local multi-agent setup, and enterprise cloud production deployment.")
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(10)
    r_sub.font.color.rgb = C_GOOGLE_MUTED
    
    p_meta = hdr_cell.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(4)
    p_meta.paragraph_format.space_after = Pt(0)
    r_meta = p_meta.add_run("Target Audience: AI Architects & Engineers | Specification: A2A v1.0 | Status: Production Guide")
    r_meta.font.name = "Arial"
    r_meta.font.size = Pt(8.5)
    r_meta.font.bold = True
    r_meta.font.color.rgb = C_GOOGLE_DARK

    p_sep = doc.add_paragraph()
    p_sep.paragraph_format.space_before = Pt(4)
    p_sep.paragraph_format.space_after = Pt(4)

    # Executive Summary
    add_heading_1(doc, "Executive Summary")
    add_body_p(doc, "The artificial intelligence landscape is undergoing a monumental transition: moving rapidly from monolithic single-agent chat applications to distributed, collaborative multi-agent systems. However, as enterprise teams adopt heterogeneous frameworks—such as LangGraph, Google Agent Development Kit (ADK), CrewAI, Semantic Kernel, and Microsoft Copilot Studio—they encounter an integration bottleneck. Connecting N independent agents requires N*(N-1)/2 custom adapters, creating brittle, siloed architectures.")
    add_body_p(doc, "The Agent-to-Agent (A2A) protocol is an open-source standard pioneered by Google and hosted under the Linux Foundation. A2A establishes a universal communication layer that enables autonomous AI agents to discover capabilities, exchange tasks, stream status updates, and transfer structured artifacts seamlessly across framework, corporate, and cloud boundaries.")
    
    add_callout(doc, "Key Philosophy: The Principle of Opacity. In A2A, interacting agents remain black boxes to each other. An agent does not expose its internal prompt engineering, memory state, model weights, or private databases. Instead, it exposes an explicit public contract via an Agent Card, ensuring enterprise privacy, security, and IP protection.", title="CORE ARCHITECTURAL PRINCIPLE", callout_type="info")

    # Section 1: What is A2A & What is it Used For?
    add_heading_1(doc, "1. What is A2A and What Problem Does It Solve?")
    add_body_p(doc, "A2A stands for Agent-to-Agent Protocol. It defines a vendor-neutral, protocol-level communication contract enabling independent software agents to collaborate on complex, multi-step workflows. Unlike traditional web APIs that expect deterministic parameters and immediate synchronous responses, A2A is specifically tailored to the nondeterministic, asynchronous, and iterative nature of autonomous generative agents.")
    
    add_heading_2(doc, "The O(N²) Fragmentation Dilemma")
    add_body_p(doc, "Prior to A2A, connecting an agent built with Google ADK to another agent built in LangChain required writing custom glue code, mapping internal schemas, and handling token streaming manually. If a company operated five different agentic platforms, they required 10 bespoke point-to-point connectors. As the number of agents reaches dozens across departments and external partners, maintaining these integrations becomes computationally and operationally unsustainable.")
    add_body_p(doc, "A2A reduces this complexity from O(N²) to O(N). By standardizing the communication protocol, any agent that speaks A2A can immediately discover, interact with, and delegate tasks to any other A2A-compliant agent in the world.")

    add_heading_2(doc, "Primary Use Cases of A2A")
    add_bullet_p(doc, "Enterprises frequently develop agents using different internal toolchains. A2A allows a LangGraph-based customer support agent to delegate billing disputes to a Google ADK-powered financial accounting agent without rewriting either codebase.", bold_prefix="Cross-Framework Interoperability: ")
    add_bullet_p(doc, "A customer's procurement agent can securely negotiate purchase orders with a vendor's sales agent across organizational firewalls without exposing either company's proprietary data or internal prompts.", bold_prefix="Inter-Enterprise Collaboration: ")
    add_bullet_p(doc, "Many agentic tasks (such as deep competitive research, compliance reviews, or code audits) require minutes or hours to finish. A2A natively models long-running lifecycles with state tracking, token streaming, and asynchronous webhook notifications.", bold_prefix="Long-Running Stateful Delegation: ")
    add_bullet_p(doc, "Agents can pause execution when requiring managerial approval or missing information, transitioning to a 'needs_input' state until human feedback is provided.", bold_prefix="Human-in-the-Loop & Multi-Turn Interactions: ")

    # Section 2: A2A vs MCP
    add_heading_1(doc, "2. A2A vs. MCP: The Two Layers of Modern Agentic Architecture")
    add_body_p(doc, "A common source of confusion in modern AI development is the relationship between the Model Context Protocol (MCP, developed by Anthropic) and the Agent-to-Agent (A2A) Protocol (developed by Google and open-sourced under Linux Foundation). Rather than competing, these two standards are deeply complementary and address fundamentally different tiers of the agent stack.")

    add_styled_table(
        doc,
        headers=["Dimension", "Model Context Protocol (MCP)", "Agent-to-Agent Protocol (A2A)"],
        rows=[
            ["Primary Scope", "Agent-to-Tool & Agent-to-Resource", "Agent-to-Agent & System-to-System"],
            ["Interaction Target", "Databases, local files, Git repos, APIs", "Independent, autonomous AI agents"],
            ["Execution Model", "Synchronous, client-invoked RPC tools", "Asynchronous, stateful, multi-turn tasks"],
            ["State Awareness", "Stateless tool execution", "Full task lifecycle (submitted, working, completed)"],
            ["Boundary & Opacity", "Tool logic transparently injected into agent", "Opaque black-box contract via Agent Cards"],
            ["Streaming & Webhooks", "Token stream from host to user", "Bidirectional token streaming, SSE, & push webhooks"],
            ["Deployment Scope", "Usually within single host/container boundary", "Across networks, clouds, and enterprise perimeters"]
        ],
        col_widths=[1.5, 2.65, 2.65]
    )

    add_image_figure(doc, "/Users/sachinmishra/Desktop/A2A_google/diagram1_mcp_vs_a2a.png", 
                     "Architectural Boundary Separation: MCP for Tool Integration vs. A2A for Cross-Agent Collaboration")

    add_body_p(doc, "As visualized in Figure 1, an enterprise Orchestrator Agent utilizes MCP internally to query private PostgreSQL databases and local document stores. When it requires specialized financial modeling beyond its domain, it dispatches an A2A task across the corporate network to an external Financial Specialist Agent. The Financial Specialist executes the task using its own private tools and returns the finalized output (Artifact) via A2A.")

    # Section 3: Core Architecture & Building Blocks
    add_heading_1(doc, "3. Core Architecture & Building Blocks of A2A")
    add_body_p(doc, "The A2A specification is organized into three distinct layers: the Identity & Discovery Layer, the Canonical Data Model, and the Transport Protocol Bindings.")

    add_heading_2(doc, "3.1 The Agent Card: The Digital Passport of AI Agents")
    add_body_p(doc, "Every A2A server publishes a standardized JSON document known as an Agent Card. Located by standard convention at the root endpoint:")
    
    add_code_block(doc, "https://{agent-host-domain}/.well-known/agent-card.json", caption="Well-Known Discovery Endpoint")
    
    add_body_p(doc, "The Agent Card acts as a machine-readable résumé and service manifest. When an orchestrator agent encounters a new subtask, it queries the target server's Agent Card to inspect its skills, schema expectations, and authentication requirements before dispatching requests.")

    add_code_block(doc, """{
  "name": "financial_risk_analyst",
  "version": "1.2.0",
  "description": "Analyzes balance sheets, cash flows, and SEC 10-K filings for credit risks.",
  "supportedInterfaces": [
    {
      "protocol": "JSONRPC",
      "version": "2.0",
      "url": "https://risk-agent.internal.enterprise.com/a2a/v1"
    }
  ],
  "capabilities": {
    "streaming": true,
    "pushNotifications": true
  },
  "defaultInputModes": ["text/plain", "application/json"],
  "defaultOutputModes": ["application/json", "application/pdf"],
  "skills": [
    {
      "id": "evaluate_credit_risk",
      "name": "Corporate Credit Risk Assessment",
      "description": "Calculates Altman Z-Score and assesses liquidity risks.",
      "tags": ["finance", "risk", "sec-filings"]
    }
  ],
  "securitySchemes": {
    "oauth2": {
      "type": "oauth2",
      "flows": { "clientCredentials": { "tokenUrl": "https://auth.enterprise.com/oauth/token" } }
    }
  }
}""", caption="Standard Agent Card JSON Manifest (agent-card.json)")

    add_heading_2(doc, "3.2 The Canonical Data Primitives")
    add_body_p(doc, "A2A defines four foundational data structures:")
    add_bullet_p(doc, "A discrete, conversational input or output exchanged between agents. A Message contains an identifier (messageId), a role ('ROLE_USER' or 'ROLE_AGENT'), a thread context (contextId), and an array of content parts (supporting text, JSON blobs, or file references).", bold_prefix="1. Message: ")
    add_bullet_p(doc, "The fundamental stateful unit of work in A2A. Tasks possess a unique task ID, an execution status ('submitted', 'working', 'completed', 'failed', or 'needs_input'), an exchange history, and pointers to resulting artifacts.", bold_prefix="2. Task: ")
    add_bullet_p(doc, "The tangible output generated by the specialist agent upon completing its task. Artifacts can include structured JSON payloads, generated PDF reports, executable code, or dataset files.", bold_prefix="3. Artifact: ")
    add_bullet_p(doc, "Atomic content blocks within messages and artifacts, allowing multi-modal payloads without breaking protocol parsing.", bold_prefix="4. Part: ")

    add_heading_2(doc, "3.3 Protocol Bindings & JSON-RPC 2.0 Mapping")
    add_body_p(doc, "A2A communicates over standard HTTP/HTTPS using JSON-RPC 2.0. The standard maps four primary operations:")
    add_bullet_p(doc, "Dispatches a message/task to the remote agent. Can return immediately with task status or block until completion.", bold_prefix="message/send: ")
    add_bullet_p(doc, "Initiates task execution while opening a Server-Sent Events (SSE) stream to stream real-time thought tokens, intermediate steps, and final artifacts.", bold_prefix="message/stream: ")
    add_bullet_p(doc, "Polls the current status, progress percentage, or generated artifacts of an active or completed task.", bold_prefix="tasks/get: ")
    add_bullet_p(doc, "Instructs the remote agent to safely abort a running task, freeing cloud compute and memory resources.", bold_prefix="tasks/cancel: ")

    add_image_figure(doc, "/Users/sachinmishra/Desktop/A2A_google/diagram2_a2a_lifecycle.png", 
                     "The 4-Step A2A Communication Lifecycle: Discovery, Dispatch, Execution, and Handoff")

    # Section 4: Hands-On Local Setup
    add_heading_1(doc, "4. Hands-On Guide: Creating Multiple Agents & Communicating Locally")
    add_body_p(doc, "To understand how A2A works in practice, let us examine a real local implementation. In this scenario, we create two distinct agents running on localhost:")
    add_bullet_p(doc, "A specialist agent that exposes an A2A service on port 8001. It defines its capabilities in an Agent Card and executes analytical queries.", bold_prefix="Agent 1 (Specialist / A2A Server): ")
    add_bullet_p(doc, "An orchestrating agent running on port 8000. It discovers Agent 1 via HTTP, dispatches analytical tasks, and integrates the resulting artifacts.", bold_prefix="Agent 2 (Orchestrator / A2A Client): ")

    add_image_figure(doc, "/Users/sachinmishra/Desktop/A2A_google/diagram3_local_multiagent.png", 
                     "Local Multi-Agent Communication Architecture via A2A Protocol")

    add_heading_2(doc, "Step 1: Implementing the Specialist Agent (Server)")
    add_body_p(doc, "Using Google ADK (`google-adk`) and the A2A SDK (`a2a-sdk`), we define the specialist logic and wrap it with `to_a2a`, which automatically launches a FastAPI/Starlette server serving both the `.well-known/agent-card.json` endpoint and the JSON-RPC methods.")

    add_code_block(doc, """# specialist_agent.py
import uvicorn
from a2a.types import AgentCard, Skill
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# 1. Define the internal specialist execution logic
def analyze_market_trends(query: str) -> dict:
    # Simulated financial analysis computation
    return {
        "status": "success",
        "market_sentiment": "Bullish",
        "confidence_score": 0.89,
        "key_drivers": ["AI infrastructure demand", "Strong enterprise earnings", "Fed rate cuts"],
        "recommendation": "Overweight Technology Sector"
    }

# 2. Declare the Agent Card
specialist_card = AgentCard(
    name="market_analyst_agent",
    url="http://127.0.0.1:8001",
    description="Specialist agent providing macroeconomic market sentiment analysis.",
    version="1.0.0",
    capabilities={"streaming": False, "pushNotifications": False},
    skills=[
        Skill(
            id="market_sentiment_analysis",
            name="Market Sentiment Analysis",
            description="Analyzes equity and macroeconomic trends.",
            tags=["finance", "markets", "stocks"]
        )
    ],
    default_input_modes=["text/plain"],
    default_output_modes=["application/json"],
    supports_authenticated_extended_card=False,
)

# 3. Expose as A2A-compliant ASGI application on port 8001
app = to_a2a(
    agent=analyze_market_trends, 
    port=8001, 
    agent_card=specialist_card
)

if __name__ == "__main__":
    print("Starting A2A Specialist Agent on http://127.0.0.1:8001 ...")
    uvicorn.run(app, host="127.0.0.1", port=8001)""", caption="Specialist Agent Server Implementation (specialist_agent.py)")

    add_heading_2(doc, "Step 2: Implementing the Orchestrator Agent (Client)")
    add_body_p(doc, "The orchestrator agent uses `RemoteA2aAgent` to bind to the specialist agent. Notice that the orchestrator does not need to know how the specialist is implemented; it only requires the endpoint URL.")

    add_code_block(doc, """# orchestrator_agent.py
import asyncio
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

async def run_orchestration():
    print("Initializing Orchestrator Client...")
    
    # 1. Connect to the local specialist agent via A2A endpoint
    # The client automatically discovers capabilities from /.well-known/agent-card.json
    specialist = RemoteA2aAgent(
        name="local_market_specialist",
        endpoint="http://127.0.0.1:8001"
    )
    
    user_prompt = "Perform sentiment analysis for Q4 enterprise software trends."
    print(f"Dispatching task to Specialist Agent: '{user_prompt}'")
    
    # 2. Send task via A2A JSON-RPC (message/send)
    response = await specialist.send_message(
        content=user_prompt,
        context_id="portfolio-review-2026"
    )
    
    # 3. Process the returned task result and artifacts
    print("\\n[SUCCESS] Response received from A2A Specialist Agent:")
    print(f"Task ID: {response.task_id}")
    print(f"Status:  {response.status}")
    print(f"Payload: {response.content}")

if __name__ == "__main__":
    asyncio.run(run_orchestration())""", caption="Orchestrator Client Implementation (orchestrator_agent.py)")

    add_callout(doc, "Local Testing Execution: Open two terminal windows. In Terminal 1, execute `python specialist_agent.py`. The server starts and hosts its Agent Card at `http://127.0.0.1:8001/.well-known/agent-card.json`. In Terminal 2, execute `python orchestrator_agent.py`. The orchestrator queries the Agent Card, sends the task via HTTP POST, and prints the verified response payload.", title="HOW TO RUN LOCALLY", callout_type="success")

    # Section 5: Enterprise Deployment
    add_heading_1(doc, "5. Enterprise Cloud Deployment: Why A2A is Essential in Production")
    add_body_p(doc, "While simple multi-agent scripts can run within a single Python process in a Jupyter Notebook, enterprise production systems face severe operational requirements that monolithic architectures cannot support.")

    add_heading_2(doc, "Why Monolithic Multi-Agent Deployments Fail")
    add_bullet_p(doc, "If five agents live in the same container or codebase, updating the prompt or dependencies of Agent 3 requires redeploying the entire multi-agent monolith.", bold_prefix="Coupled Deployments: ")
    add_bullet_p(doc, "A resource-heavy agent (e.g. document OCR or code execution) forces the entire application to scale out, drastically increasing cloud infrastructure costs.", bold_prefix="Inefficient Compute Scaling: ")
    add_bullet_p(doc, "In monolithic agents, memory and tools are shared globally. A compromised sub-agent can leak secrets or access database credentials meant for other agents.", bold_prefix="Security & Blast Radius: ")

    add_heading_2(doc, "How A2A Solves Production Scaling")
    add_bullet_p(doc, "Each agent runs as an isolated microservice (e.g. on Google Cloud Run or Kubernetes). They scale independently from 0 to N instances based on incoming task volume.", bold_prefix="Microservice Decoupling: ")
    add_bullet_p(doc, "Agents communicate over zero-trust HTTPS channels. A client agent only has permission to invoke specific A2A endpoints; it has no access to the remote agent's private memory or storage.", bold_prefix="Zero-Trust Boundary Isolation: ")
    add_bullet_p(doc, "Enterprises are not locked into a single cloud or framework. An agent running on Google Cloud Vertex AI can effortlessly orchestrate workflows with an agent deployed in Microsoft Azure or an on-premises data center.", bold_prefix="Vendor & Cloud Agnosticism: ")

    add_image_figure(doc, "/Users/sachinmishra/Desktop/A2A_google/diagram4_cloud_deployment.png", 
                     "Enterprise Production Deployment Topology: Cross-Cloud Interoperability with Centralized Governance")

    add_heading_2(doc, "Recommended Production Topology on Google Cloud")
    add_body_p(doc, "When deploying A2A agents into Google Cloud enterprise environments, the recommended reference architecture incorporates:")
    add_bullet_p(doc, "Deploy specialist agents as containerized services on Google Cloud Run or Vertex AI Agent Engine. Cloud Run offers instant scaling, built-in HTTPS endpoints, and pay-per-use efficiency.", bold_prefix="Serverless Container Compute: ")
    add_bullet_p(doc, "Place Google Cloud Armor and Apigee in front of the A2A endpoints to enforce DDoS protection, rate limiting, and web application firewall policies.", bold_prefix="API Gateway & Security: ")
    add_bullet_p(doc, "A2A supports OAuth 2.0 client credentials flows and mutual TLS (mTLS). Agents authenticate using Google Cloud Workload Identity Federation, ensuring tamper-proof cryptographic identity.", bold_prefix="Enterprise Authentication: ")
    add_bullet_p(doc, "Centralized logging of every A2A JSON-RPC request and task ID via Google Cloud Logging and Cloud Trace for end-to-end multi-agent observability and cost attribution.", bold_prefix="Auditability & Observability: ")

    # Section 6: Beginner's Checklist & Best Practices
    add_heading_1(doc, "6. Beginner's Implementation Checklist & Best Practices")
    add_body_p(doc, "For teams embarking on their first A2A implementations, adhere to the following best practices:")

    add_styled_table(
        doc,
        headers=["Category", "Best Practice Recommendation", "Common Pitfall to Avoid"],
        rows=[
            ["Agent Card Design", "Keep skill descriptions concise, semantically clear, and keyword-rich.", "Vague descriptions that cause orchestrator routing errors."],
            ["State Handling", "Use task IDs and persist state in Redis/PostgreSQL for long tasks.", "Relying on in-memory task queues that fail during container restarts."],
            ["Streaming", "Implement Server-Sent Events (SSE) via message/stream for user interfaces.", "Blocking HTTP connections during 60+ second agent reasoning."],
            ["Security", "Enforce OAuth2 Bearer tokens and validate JWS Agent Card signatures.", "Exposing unprotected public endpoints on localhost or cloud."],
            ["Error Handling", "Return standard JSON-RPC 2.0 error codes with descriptive diagnostics.", "Returning HTTP 200 with error tracebacks hidden inside strings."]
        ],
        col_widths=[1.5, 2.7, 2.6]
    )

    add_heading_1(doc, "7. Conclusion")
    add_body_p(doc, "The Agent-to-Agent (A2A) protocol represents the foundational missing link in modern artificial intelligence systems. By decoupling agent-to-tool integration (MCP) from agent-to-agent collaboration (A2A), developers gain the freedom to build specialized, modular, and secure multi-agent networks that scale across framework and organizational boundaries.")
    add_body_p(doc, "As the AI ecosystem matures from experimental prototypes into mission-critical enterprise infrastructure, standardizing on A2A guarantees that your multi-agent architecture remains future-proof, interoperable, and ready for global federation.")

    # Save document
    output_filename = "/Users/sachinmishra/Desktop/A2A_google/Google_A2A_Protocol_Comprehensive_Guide.docx"
    doc.save(output_filename)
    print(f"Document saved successfully as '{output_filename}'")

if __name__ == "__main__":
    build_document()
