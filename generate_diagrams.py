import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ArrowStyle

# Set high DPI and aesthetic styling
plt.rcParams['font.sans-serif'] = 'Helvetica, Arial, DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

# Google Palette
G_BLUE = '#1A73E8'
G_LIGHT_BLUE = '#E8F0FE'
G_BLUE_BORDER = '#8AB4F8'
G_RED = '#EA4335'
G_LIGHT_RED = '#FCE8E6'
G_GREEN = '#1E8E3E'
G_LIGHT_GREEN = '#E6F4EA'
G_YELLOW = '#F9AB00'
G_LIGHT_YELLOW = '#FEF7E0'
G_DARK = '#202124'
G_MUTED = '#5F6368'
G_BG = '#F8F9FA'
G_BORDER = '#DADCE0'
WHITE = '#FFFFFF'

def create_mcp_vs_a2a_diagram(output_path):
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    ax.set_facecolor(WHITE)
    fig.patch.set_facecolor(WHITE)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title & Subtitle
    ax.text(50, 94, "A2A vs. MCP: Complementary Interoperability Layers", 
            ha='center', va='center', fontsize=15, fontweight='bold', color=G_DARK)
    ax.text(50, 89, "MCP standardizes Agent-to-Tool integration; A2A standardizes Agent-to-Agent collaboration", 
            ha='center', va='center', fontsize=10, color=G_MUTED)

    # Agent A Box (Boundary)
    box_a = FancyBboxPatch((4, 18), 38, 64, boxstyle="round,pad=1.5,rounding_size=3",
                           facecolor=G_BG, edgecolor=G_BORDER, linewidth=1.5)
    ax.add_patch(box_a)
    ax.text(23, 78, "System A: Client / Orchestrator", ha='center', va='center', 
            fontsize=11, fontweight='bold', color=G_DARK)
    ax.text(23, 74, "(Framework: LangGraph / Custom)", ha='center', va='center', 
            fontsize=8.5, color=G_MUTED)

    # Core Agent A
    agent_a = FancyBboxPatch((8, 48), 30, 20, boxstyle="round,pad=1,rounding_size=2.5",
                             facecolor=G_LIGHT_BLUE, edgecolor=G_BLUE, linewidth=2)
    ax.add_patch(agent_a)
    ax.text(23, 60, "Orchestrator Agent", ha='center', va='center', 
            fontsize=11, fontweight='bold', color=G_BLUE)
    ax.text(23, 53, "• Manages High-Level Goals\n• A2A Client Dispatcher", ha='center', va='center', 
            fontsize=8.5, color=G_DARK)

    # MCP Tool connection in Agent A
    mcp_box_a = FancyBboxPatch((8, 22), 30, 18, boxstyle="round,pad=1,rounding_size=2",
                               facecolor=G_LIGHT_YELLOW, edgecolor=G_YELLOW, linewidth=1.5)
    ax.add_patch(mcp_box_a)
    ax.text(23, 33, "Local Tools & APIs", ha='center', va='center', 
            fontsize=9.5, fontweight='bold', color='#B06000')
    ax.text(23, 27, "PostgreSQL, Google Drive, Local FS", ha='center', va='center', 
            fontsize=8, color=G_DARK)

    # MCP Arrow inside System A
    ax.annotate("", xy=(23, 40), xytext=(23, 48),
                arrowprops=dict(arrowstyle="<->", color='#B06000', lw=2))
    ax.text(32, 44, "MCP Protocol\n(Agent-to-Tool)", ha='left', va='center', 
            fontsize=7.5, fontweight='bold', color='#B06000')

    # Agent B Box (Boundary)
    box_b = FancyBboxPatch((58, 18), 38, 64, boxstyle="round,pad=1.5,rounding_size=3",
                           facecolor=G_BG, edgecolor=G_BORDER, linewidth=1.5)
    ax.add_patch(box_b)
    ax.text(77, 78, "System B: Remote Specialist", ha='center', va='center', 
            fontsize=11, fontweight='bold', color=G_DARK)
    ax.text(77, 74, "(Framework: Google ADK / FastAPI)", ha='center', va='center', 
            fontsize=8.5, color=G_MUTED)

    # Core Agent B
    agent_b = FancyBboxPatch((62, 48), 30, 20, boxstyle="round,pad=1,rounding_size=2.5",
                             facecolor=G_LIGHT_GREEN, edgecolor=G_GREEN, linewidth=2)
    ax.add_patch(agent_b)
    ax.text(77, 60, "Financial Analyst Agent", ha='center', va='center', 
            fontsize=11, fontweight='bold', color=G_GREEN)
    ax.text(77, 53, "• Exposes Agent Card\n• Executes Complex Subtasks", ha='center', va='center', 
            fontsize=8.5, color=G_DARK)

    # MCP Tool connection in Agent B
    mcp_box_b = FancyBboxPatch((62, 22), 30, 18, boxstyle="round,pad=1,rounding_size=2",
                               facecolor=G_LIGHT_YELLOW, edgecolor=G_YELLOW, linewidth=1.5)
    ax.add_patch(mcp_box_b)
    ax.text(77, 33, "Specialist Domain Tools", ha='center', va='center', 
            fontsize=9.5, fontweight='bold', color='#B06000')
    ax.text(77, 27, "Bloomberg Terminal, SQL, Models", ha='center', va='center', 
            fontsize=8, color=G_DARK)

    # MCP Arrow inside System B
    ax.annotate("", xy=(77, 40), xytext=(77, 48),
                arrowprops=dict(arrowstyle="<->", color='#B06000', lw=2))
    ax.text(86, 44, "MCP Protocol\n(Agent-to-Tool)", ha='left', va='center', 
            fontsize=7.5, fontweight='bold', color='#B06000')

    # A2A Bridge between Agent A and Agent B
    ax.annotate("", xy=(62, 58), xytext=(38, 58),
                arrowprops=dict(arrowstyle="<->", color=G_BLUE, lw=3, mutation_scale=15))
    
    # A2A Label Pill
    pill = FancyBboxPatch((41, 51), 18, 14, boxstyle="round,pad=0.8,rounding_size=2",
                          facecolor=G_BLUE, edgecolor='none')
    ax.add_patch(pill)
    ax.text(50, 60, "A2A PROTOCOL", ha='center', va='center', 
            fontsize=8.5, fontweight='bold', color=WHITE)
    ax.text(50, 54, "JSON-RPC / HTTP\nTask & Artifacts", ha='center', va='center', 
            fontsize=7, color=WHITE)

    # Opacity Privacy Wall note at bottom
    note_box = FancyBboxPatch((15, 4), 70, 9, boxstyle="round,pad=0.5,rounding_size=1.5",
                              facecolor=WHITE, edgecolor=G_BLUE_BORDER, linewidth=1)
    ax.add_patch(note_box)
    ax.text(50, 8.5, "[Security Principle] Opaque Boundaries: System A never sees System B's internal prompts, weights, or database queries.",
            ha='center', va='center', fontsize=8, color=G_DARK)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_a2a_lifecycle_diagram(output_path):
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=300)
    ax.set_facecolor(WHITE)
    fig.patch.set_facecolor(WHITE)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title
    ax.text(50, 93, "The 4-Step A2A Communication Lifecycle", 
            ha='center', va='center', fontsize=14, fontweight='bold', color=G_DARK)
    ax.text(50, 87, "From Agent Card discovery to asynchronous execution and artifact delivery", 
            ha='center', va='center', fontsize=9.5, color=G_MUTED)

    steps = [
        {"num": "1", "title": "Discovery", "sub": "GET /.well-known/\nagent-card.json", 
         "desc": "Client agent inspects skills,\nendpoints, auth & schema.", "color": G_BLUE, "bg": G_LIGHT_BLUE},
        {"num": "2", "title": "Task Dispatch", "sub": "POST message/send\nor message/stream", 
         "desc": "Client submits structured task\nwith roles and input parts.", "color": G_YELLOW, "bg": G_LIGHT_YELLOW},
        {"num": "3", "title": "Execution", "sub": "Status: working\nSSE Streaming Events", 
         "desc": "Remote agent processes work;\nstreams tokens or status updates.", "color": G_RED, "bg": G_LIGHT_RED},
        {"num": "4", "title": "Handoff", "sub": "Status: completed\nReturn Artifacts", 
         "desc": "Remote agent returns final\nstructured reports or outputs.", "color": G_GREEN, "bg": G_LIGHT_GREEN},
    ]

    x_positions = [6, 29.5, 53, 76.5]
    card_width = 18
    card_height = 54

    for i, step in enumerate(steps):
        x = x_positions[i]
        # Step Card
        card = FancyBboxPatch((x, 22), card_width, card_height, boxstyle="round,pad=0.8,rounding_size=2",
                              facecolor=step["bg"], edgecolor=step["color"], linewidth=1.5)
        ax.add_patch(card)

        # Number badge
        badge = FancyBboxPatch((x + 7, 70), 4, 4, boxstyle="circle",
                               facecolor=step["color"], edgecolor='none')
        ax.add_patch(badge)
        ax.text(x + 9, 72, step["num"], ha='center', va='center', 
                fontsize=9, fontweight='bold', color=WHITE)

        # Step title
        ax.text(x + 9, 63, step["title"], ha='center', va='center', 
                fontsize=11, fontweight='bold', color=G_DARK)
        
        # Subtitle / technical call
        ax.text(x + 9, 53, step["sub"], ha='center', va='center', 
                fontsize=8, fontweight='bold', color=step["color"])

        # Description
        ax.text(x + 9, 36, step["desc"], ha='center', va='center', 
                fontsize=7.8, color=G_DARK)

        # Connecting arrow (except last)
        if i < 3:
            ax.annotate("", xy=(x + card_width + 3.5, 49), xytext=(x + card_width + 0.5, 49),
                        arrowprops=dict(arrowstyle="->", color=G_MUTED, lw=2, mutation_scale=12))

    # Bottom Protocol note
    bot_box = FancyBboxPatch((10, 6), 80, 10, boxstyle="round,pad=0.5,rounding_size=1.5",
                             facecolor=G_BG, edgecolor=G_BORDER, linewidth=1)
    ax.add_patch(bot_box)
    ax.text(50, 11, "Standardized JSON-RPC 2.0 Payloads • Supports Synchronous, Streaming (SSE), and Asynchronous Webhooks",
            ha='center', va='center', fontsize=8.5, fontweight='bold', color=G_MUTED)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_local_multiagent_diagram(output_path):
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    ax.set_facecolor(WHITE)
    fig.patch.set_facecolor(WHITE)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title
    ax.text(50, 93, "Local Multi-Agent Communication Setup via A2A", 
            ha='center', va='center', fontsize=14, fontweight='bold', color=G_DARK)
    ax.text(50, 87, "Orchestrator client delegating to a local specialist service on localhost", 
            ha='center', va='center', fontsize=9.5, color=G_MUTED)

    # Left: Orchestrator Agent (Client)
    box_orch = FancyBboxPatch((6, 18), 38, 62, boxstyle="round,pad=1.2,rounding_size=2.5",
                              facecolor=G_LIGHT_BLUE, edgecolor=G_BLUE, linewidth=1.8)
    ax.add_patch(box_orch)
    ax.text(25, 74, "Agent 1: Orchestrator (Client)", ha='center', va='center', 
            fontsize=11, fontweight='bold', color=G_BLUE)
    ax.text(25, 69, "Port 8000 / Main Process", ha='center', va='center', 
            fontsize=8.5, color=G_MUTED)

    # Sub-boxes inside Orchestrator
    sub1 = FancyBboxPatch((9, 48), 32, 16, boxstyle="round,pad=0.6,rounding_size=1.5",
                          facecolor=WHITE, edgecolor=G_BORDER, linewidth=1)
    ax.add_patch(sub1)
    ax.text(25, 59, "RemoteA2aAgent Client", ha='center', va='center', 
            fontsize=9.5, fontweight='bold', color=G_DARK)
    ax.text(25, 53, "Discovers remote capabilities via\nGET http://127.0.0.1:8001/.well-known/agent-card.json", 
            ha='center', va='center', fontsize=7.2, color=G_MUTED)

    sub2 = FancyBboxPatch((9, 24), 32, 18, boxstyle="round,pad=0.6,rounding_size=1.5",
                          facecolor=WHITE, edgecolor=G_BORDER, linewidth=1)
    ax.add_patch(sub2)
    ax.text(25, 36, "Task Coordinator Logic", ha='center', va='center', 
            fontsize=9.5, fontweight='bold', color=G_DARK)
    ax.text(25, 29, "• Formulates specialized task\n• Awaits async result or artifact\n• Compiles final output for user", 
            ha='center', va='center', fontsize=7.2, color=G_DARK)

    # Right: Specialist Agent (Server)
    box_spec = FancyBboxPatch((56, 18), 38, 62, boxstyle="round,pad=1.2,rounding_size=2.5",
                              facecolor=G_LIGHT_GREEN, edgecolor=G_GREEN, linewidth=1.8)
    ax.add_patch(box_spec)
    ax.text(75, 74, "Agent 2: Specialist (A2A Server)", ha='center', va='center', 
            fontsize=11, fontweight='bold', color=G_GREEN)
    ax.text(75, 69, "Port 8001 (FastAPI / Starlette)", ha='center', va='center', 
            fontsize=8.5, color=G_MUTED)

    # Sub-boxes inside Specialist
    sub3 = FancyBboxPatch((59, 48), 32, 16, boxstyle="round,pad=0.6,rounding_size=1.5",
                          facecolor=WHITE, edgecolor=G_BORDER, linewidth=1)
    ax.add_patch(sub3)
    ax.text(75, 59, "A2A Server Endpoint (to_a2a)", ha='center', va='center', 
            fontsize=9.5, fontweight='bold', color=G_DARK)
    ax.text(75, 53, "• Serves Agent Card at /.well-known/...\n• Implements message/send & tasks/get", 
            ha='center', va='center', fontsize=7.2, color=G_MUTED)

    sub4 = FancyBboxPatch((59, 24), 32, 18, boxstyle="round,pad=0.6,rounding_size=1.5",
                          facecolor=WHITE, edgecolor=G_BORDER, linewidth=1)
    ax.add_patch(sub4)
    ax.text(75, 36, "Internal Specialist Engine", ha='center', va='center', 
            fontsize=9.5, fontweight='bold', color=G_DARK)
    ax.text(75, 29, "• Google ADK Agent / Custom LLM\n• Domain reasoning & calculation\n• Produces structured Artifact", 
            ha='center', va='center', fontsize=7.2, color=G_DARK)

    # Middle Bridge
    ax.annotate("", xy=(56, 56), xytext=(44, 56),
                arrowprops=dict(arrowstyle="<->", color=G_BLUE, lw=2.5, mutation_scale=14))
    ax.text(50, 62, "HTTP / JSON-RPC", ha='center', va='center', 
            fontsize=8, fontweight='bold', color=G_BLUE)
    ax.text(50, 50, "127.0.0.1:8001", ha='center', va='center', 
            fontsize=7.5, color=G_MUTED)

    # Footer banner
    foot = FancyBboxPatch((12, 5), 76, 8, boxstyle="round,pad=0.5,rounding_size=1.5",
                          facecolor=G_BG, edgecolor=G_BORDER, linewidth=1)
    ax.add_patch(foot)
    ax.text(50, 9, "Key Advantage: Switching from local to remote is just changing the URL from localhost to cloud endpoint!", 
            ha='center', va='center', fontsize=8, color=G_DARK)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_cloud_deployment_diagram(output_path):
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    ax.set_facecolor(WHITE)
    fig.patch.set_facecolor(WHITE)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title
    ax.text(50, 94, "A2A Enterprise Cloud Deployment Architecture", 
            ha='center', va='center', fontsize=14, fontweight='bold', color=G_DARK)
    ax.text(50, 88, "Cross-cloud, zero-trust interoperability with enterprise security and governance", 
            ha='center', va='center', fontsize=9.5, color=G_MUTED)

    # Google Cloud Box
    gcp_box = FancyBboxPatch((5, 14), 54, 68, boxstyle="round,pad=1.2,rounding_size=2.5",
                             facecolor=G_LIGHT_BLUE, edgecolor=G_BLUE, linewidth=1.8)
    ax.add_patch(gcp_box)
    ax.text(32, 77, "Google Cloud Platform (Enterprise Org)", ha='center', va='center', 
            fontsize=11, fontweight='bold', color=G_BLUE)

    # Cloud Run Specialist
    cr_box = FancyBboxPatch((9, 44), 46, 26, boxstyle="round,pad=0.8,rounding_size=2",
                            facecolor=WHITE, edgecolor=G_BLUE, linewidth=1.2)
    ax.add_patch(cr_box)
    ax.text(32, 64, "Cloud Run / Vertex AI Agent Engine", ha='center', va='center', 
            fontsize=10, fontweight='bold', color=G_DARK)
    ax.text(32, 57, "Specialist Agent Container (Autoscaling 0 to N)", ha='center', va='center', 
            fontsize=8, color=G_MUTED)
    ax.text(32, 49, "• Exposes A2A Service with OAuth2 Bearer Tokens\n• Cloud Pub/Sub & Webhooks for long tasks", 
            ha='center', va='center', fontsize=7.5, color=G_DARK)

    # Security & API Gateway Layer
    gw_box = FancyBboxPatch((9, 18), 46, 21, boxstyle="round,pad=0.8,rounding_size=2",
                            facecolor=WHITE, edgecolor=G_BORDER, linewidth=1)
    ax.add_patch(gw_box)
    ax.text(32, 33, "Cloud Armor & API Gateway / Apigee", ha='center', va='center', 
            fontsize=9.5, fontweight='bold', color=G_DARK)
    ax.text(32, 25, "• Rate Limiting, WAF, OAuth2 / mTLS Validation\n• Audit Logging & Cost Tracking per Agent Task", 
            ha='center', va='center', fontsize=7.5, color=G_MUTED)

    # External Partner Agent / Multi-Cloud Box
    ext_box = FancyBboxPatch((67, 14), 28, 68, boxstyle="round,pad=1.2,rounding_size=2.5",
                             facecolor=G_BG, edgecolor=G_BORDER, linewidth=1.5)
    ax.add_patch(ext_box)
    ax.text(81, 77, "External / Partner Cloud", ha='center', va='center', 
            fontsize=10.5, fontweight='bold', color=G_DARK)
    ax.text(81, 72, "(AWS / Azure / On-Prem)", ha='center', va='center', 
            fontsize=8, color=G_MUTED)

    ext_agent = FancyBboxPatch((70, 36), 22, 28, boxstyle="round,pad=0.8,rounding_size=2",
                               facecolor=WHITE, edgecolor=G_YELLOW, linewidth=1.5)
    ax.add_patch(ext_agent)
    ax.text(81, 58, "Partner Client Agent", ha='center', va='center', 
            fontsize=9.5, fontweight='bold', color='#B06000')
    ax.text(81, 48, "Built in CrewAI / AutoGen", ha='center', va='center', 
            fontsize=8, color=G_MUTED)
    ax.text(81, 41, "Speaks Standard A2A", ha='center', va='center', 
            fontsize=8, fontweight='bold', color=G_GREEN)

    # Cross-Cloud A2A Arrow
    ax.annotate("", xy=(55, 30), xytext=(70, 48),
                arrowprops=dict(arrowstyle="<->", color=G_BLUE, lw=2.5, mutation_scale=14))
    
    # Shield / Security Icon Pill
    sec_pill = FancyBboxPatch((55, 42), 16, 9, boxstyle="round,pad=0.5,rounding_size=1.5",
                              facecolor=G_LIGHT_GREEN, edgecolor=G_GREEN, linewidth=1)
    ax.add_patch(sec_pill)
    ax.text(63, 46.5, "mTLS / OAuth2\nA2A Protocol", ha='center', va='center', 
            fontsize=7, fontweight='bold', color=G_GREEN)

    # Bottom Callout
    bot = FancyBboxPatch((10, 4), 80, 7, boxstyle="round,pad=0.5,rounding_size=1",
                         facecolor=WHITE, edgecolor=G_BORDER, linewidth=1)
    ax.add_patch(bot)
    ax.text(50, 7.5, "A2A eliminates vendor lock-in: Any authorized agent in any cloud can collaborate securely.", 
            ha='center', va='center', fontsize=7.8, color=G_DARK)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    create_mcp_vs_a2a_diagram("/Users/sachinmishra/Desktop/A2A_google/diagram1_mcp_vs_a2a.png")
    create_a2a_lifecycle_diagram("/Users/sachinmishra/Desktop/A2A_google/diagram2_a2a_lifecycle.png")
    create_local_multiagent_diagram("/Users/sachinmishra/Desktop/A2A_google/diagram3_local_multiagent.png")
    create_cloud_deployment_diagram("/Users/sachinmishra/Desktop/A2A_google/diagram4_cloud_deployment.png")
    print("All diagrams generated successfully!")
