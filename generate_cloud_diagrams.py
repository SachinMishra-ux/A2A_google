#!/usr/bin/env python3
"""
Generates high-DPI architecture diagrams for Google A2A Cloud Deployment:
1. Google Cloud Platform (GCP) Cloud Run Architecture
2. Amazon Web Services (AWS) ECS Fargate Architecture
3. Microsoft Azure Container Apps Architecture
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

plt.rcParams['font.sans-serif'] = 'Helvetica, Arial, DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

# Google Palette
G_BLUE = '#1A73E8'
G_LIGHT_BLUE = '#E8F0FE'
G_GREEN = '#1E8E3E'
G_LIGHT_GREEN = '#E6F4EA'
G_YELLOW = '#F9AB00'
G_LIGHT_YELLOW = '#FEF7E0'
G_RED = '#EA4335'
G_LIGHT_RED = '#FCE8E6'
G_DARK = '#202124'
G_MUTED = '#5F6368'
G_BG = '#F8F9FA'
G_BORDER = '#DADCE0'
WHITE = '#FFFFFF'

OUT_DIR = "documentation/diagrams"
os.makedirs(OUT_DIR, exist_ok=True)

# ── 1. GCP CLOUD RUN ARCHITECTURE ─────────────────────────────────────────────
def generate_gcp_diagram():
    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=300)
    ax.set_facecolor(WHITE)
    fig.patch.set_facecolor(WHITE)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title
    ax.text(50, 95, "Google Cloud Platform (GCP): Production A2A Architecture",
            ha='center', va='center', fontsize=15, fontweight='bold', color=G_DARK)
    ax.text(50, 90.5, "Serverless Auto-Scaling Microservices on Cloud Run with Apigee & Secret Manager",
            ha='center', va='center', fontsize=9.5, color=G_MUTED)

    # Public Ingress Box
    ingress_box = FancyBboxPatch((3, 20), 18, 62, boxstyle="round,pad=1,rounding_size=2",
                                facecolor=G_BG, edgecolor=G_BORDER, linewidth=1.5)
    ax.add_patch(ingress_box)
    ax.text(12, 77, "Edge & Ingress", ha='center', va='center', fontsize=11, fontweight='bold', color=G_DARK)
    
    # Cloud Armor / CDN
    p1 = FancyBboxPatch((5, 52), 14, 18, boxstyle="round,pad=0.8,rounding_size=1.5",
                        facecolor=G_LIGHT_BLUE, edgecolor=G_BLUE, linewidth=1.2)
    ax.add_patch(p1)
    ax.text(12, 63, "Cloud Armor\n+ Cloud CDN", ha='center', va='center', fontsize=9, fontweight='bold', color=G_BLUE)
    ax.text(12, 56, "DDoS & WAF", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    # Apigee API Gateway
    p2 = FancyBboxPatch((5, 26), 14, 20, boxstyle="round,pad=0.8,rounding_size=1.5",
                        facecolor=G_LIGHT_BLUE, edgecolor=G_BLUE, linewidth=1.2)
    ax.add_patch(p2)
    ax.text(12, 38, "Apigee Gateway", ha='center', va='center', fontsize=9, fontweight='bold', color=G_BLUE)
    ax.text(12, 31, "• OAuth2 / JWT\n• Agent Cards\n• Rate Limits", ha='center', va='center', fontsize=7.5, color=G_DARK)

    # Cloud Run Cluster Box (VPC)
    vpc_box = FancyBboxPatch((25, 12), 48, 70, boxstyle="round,pad=1.5,rounding_size=3",
                             facecolor='#F1F3F4', edgecolor=G_BLUE, linewidth=1.8, linestyle='--')
    ax.add_patch(vpc_box)
    ax.text(49, 78, "Serverless Private VPC • Google Cloud Run", ha='center', va='center',
            fontsize=11.5, fontweight='bold', color=G_BLUE)

    # 4 Services inside Cloud Run
    # 1. Gateway
    s_gw = FancyBboxPatch((28, 52), 42, 18, boxstyle="round,pad=0.8,rounding_size=2",
                          facecolor=WHITE, edgecolor=G_BLUE, linewidth=1.8)
    ax.add_patch(s_gw)
    ax.text(49, 64, "GATEWAY: a2a-gateway-service (Port 8000)", ha='center', va='center', fontsize=10, fontweight='bold', color=G_BLUE)
    ax.text(49, 57, "FastAPI Protocol Gateway • Intent Matcher • Web Inspector UI", ha='center', va='center', fontsize=8, color=G_DARK)

    # 2. SQL Agent
    s_sql = FancyBboxPatch((28, 33), 13, 14, boxstyle="round,pad=0.6,rounding_size=1.5",
                           facecolor=WHITE, edgecolor=G_BLUE, linewidth=1.2)
    ax.add_patch(s_sql)
    ax.text(34.5, 42, "SQL Agent", ha='center', va='center', fontsize=9, fontweight='bold', color=G_BLUE)
    ax.text(34.5, 36, "LangGraph + HITL\nPII Redaction", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    # 3. RAG Agent
    s_rag = FancyBboxPatch((42.5, 33), 13, 14, boxstyle="round,pad=0.6,rounding_size=1.5",
                           facecolor=WHITE, edgecolor=G_GREEN, linewidth=1.2)
    ax.add_patch(s_rag)
    ax.text(49, 42, "RAG Agent", ha='center', va='center', fontsize=9, fontweight='bold', color=G_GREEN)
    ax.text(49, 36, "LangChain + FAISS\nCitations", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    # 4. Podcast Agent
    s_pod = FancyBboxPatch((57, 33), 13, 14, boxstyle="round,pad=0.6,rounding_size=1.5",
                           facecolor=WHITE, edgecolor=G_YELLOW, linewidth=1.2)
    ax.add_patch(s_pod)
    ax.text(63.5, 42, "Podcast Agent", ha='center', va='center', fontsize=9, fontweight='bold', color='#B06000')
    ax.text(63.5, 36, "Google ADK\nScript Synthesis", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    # Cloud Tasks
    tasks_box = FancyBboxPatch((28, 16), 42, 12, boxstyle="round,pad=0.6,rounding_size=1.5",
                               facecolor=G_LIGHT_GREEN, edgecolor=G_GREEN, linewidth=1)
    ax.add_patch(tasks_box)
    ax.text(49, 23.5, "Cloud Tasks & Pub/Sub (Async Task Queue)", ha='center', va='center', fontsize=8.5, fontweight='bold', color=G_GREEN)
    ax.text(49, 18.5, "Guaranteed task delivery, retry backoff, dead-letter storage", ha='center', va='center', fontsize=7.5, color=G_DARK)

    # Backplane & Storage Box
    backplane = FancyBboxPatch((76, 12), 21, 70, boxstyle="round,pad=1,rounding_size=2",
                               facecolor=G_BG, edgecolor=G_BORDER, linewidth=1.5)
    ax.add_patch(backplane)
    ax.text(86.5, 78, "Managed GCP Backplane", ha='center', va='center', fontsize=10.5, fontweight='bold', color=G_DARK)

    b1 = FancyBboxPatch((78, 60), 17, 13, boxstyle="round,pad=0.6,rounding_size=1.5", facecolor=WHITE, edgecolor=G_BORDER)
    ax.add_patch(b1)
    ax.text(86.5, 68, "Secret Manager", ha='center', va='center', fontsize=8.5, fontweight='bold', color=G_DARK)
    ax.text(86.5, 63, "Gemini & DB Keys", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    b2 = FancyBboxPatch((78, 44), 17, 13, boxstyle="round,pad=0.6,rounding_size=1.5", facecolor=WHITE, edgecolor=G_BORDER)
    ax.add_patch(b2)
    ax.text(86.5, 52, "Vertex AI / Studio", ha='center', va='center', fontsize=8.5, fontweight='bold', color=G_DARK)
    ax.text(86.5, 47, "Gemini 2.5/3.1", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    b3 = FancyBboxPatch((78, 28), 17, 13, boxstyle="round,pad=0.6,rounding_size=1.5", facecolor=WHITE, edgecolor=G_BORDER)
    ax.add_patch(b3)
    ax.text(86.5, 36, "Cloud Monitoring", ha='center', va='center', fontsize=8.5, fontweight='bold', color=G_DARK)
    ax.text(86.5, 31, "OTel Logs & Traces", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    b4 = FancyBboxPatch((78, 15), 17, 10, boxstyle="round,pad=0.6,rounding_size=1.5", facecolor=WHITE, edgecolor=G_BORDER)
    ax.add_patch(b4)
    ax.text(86.5, 20.5, "Cloud SQL / Storage", ha='center', va='center', fontsize=8, fontweight='bold', color=G_DARK)

    # Arrows
    arrow_kw = dict(arrowstyle="-|>", color=G_BLUE, lw=1.5, mutation_scale=12)
    ax.annotate("", xy=(25, 61), xytext=(19, 61), arrowprops=arrow_kw)
    ax.annotate("", xy=(28, 61), xytext=(22, 38), arrowprops=arrow_kw)
    ax.annotate("", xy=(34.5, 47), xytext=(34.5, 52), arrowprops=dict(arrowstyle="<|-|>", color=G_BLUE, lw=1.2))
    ax.annotate("", xy=(49, 47), xytext=(49, 52), arrowprops=dict(arrowstyle="<|-|>", color=G_GREEN, lw=1.2))
    ax.annotate("", xy=(63.5, 47), xytext=(63.5, 52), arrowprops=dict(arrowstyle="<|-|>", color=G_YELLOW, lw=1.2))
    ax.annotate("", xy=(76, 52), xytext=(70, 52), arrowprops=arrow_kw)

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/diagram5_gcp_cloudrun_deployment.png", dpi=300)
    plt.close()
    print("✅ Created: diagram5_gcp_cloudrun_deployment.png")

# ── 2. AWS ECS FARGATE ARCHITECTURE ───────────────────────────────────────────
def generate_aws_diagram():
    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=300)
    ax.set_facecolor(WHITE)
    fig.patch.set_facecolor(WHITE)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title
    ax.text(50, 95, "Amazon Web Services (AWS): Production A2A Architecture",
            ha='center', va='center', fontsize=15, fontweight='bold', color=G_DARK)
    ax.text(50, 90.5, "Containerized Multi-Agent Cluster on AWS ECS Fargate with App Mesh & ALB",
            ha='center', va='center', fontsize=9.5, color=G_MUTED)

    # Ingress
    ingress_box = FancyBboxPatch((3, 20), 18, 62, boxstyle="round,pad=1,rounding_size=2",
                                facecolor=G_BG, edgecolor=G_BORDER, linewidth=1.5)
    ax.add_patch(ingress_box)
    ax.text(12, 77, "AWS Ingress", ha='center', va='center', fontsize=11, fontweight='bold', color=G_DARK)

    p1 = FancyBboxPatch((5, 52), 14, 18, boxstyle="round,pad=0.8,rounding_size=1.5",
                        facecolor='#FFF3E0', edgecolor='#FF9900', linewidth=1.2)
    ax.add_patch(p1)
    ax.text(12, 63, "Route 53\n+ AWS WAF", ha='center', va='center', fontsize=9, fontweight='bold', color='#D46B08')
    ax.text(12, 56, "DNS & Edge Shield", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    p2 = FancyBboxPatch((5, 26), 14, 20, boxstyle="round,pad=0.8,rounding_size=1.5",
                        facecolor='#FFF3E0', edgecolor='#FF9900', linewidth=1.2)
    ax.add_patch(p2)
    ax.text(12, 38, "Application\nLoad Balancer", ha='center', va='center', fontsize=9, fontweight='bold', color='#D46B08')
    ax.text(12, 30, "TLS 1.3 Termination\nPath Routing", ha='center', va='center', fontsize=7.5, color=G_DARK)

    # ECS Cluster Box (VPC)
    vpc_box = FancyBboxPatch((25, 12), 48, 70, boxstyle="round,pad=1.5,rounding_size=3",
                             facecolor='#F8F9FA', edgecolor='#FF9900', linewidth=1.8, linestyle='--')
    ax.add_patch(vpc_box)
    ax.text(49, 78, "Private VPC Subnets • ECS Fargate Multi-Agent Cluster", ha='center', va='center',
            fontsize=11.5, fontweight='bold', color='#D46B08')

    s_gw = FancyBboxPatch((28, 52), 42, 18, boxstyle="round,pad=0.8,rounding_size=2",
                          facecolor=WHITE, edgecolor='#FF9900', linewidth=1.8)
    ax.add_patch(s_gw)
    ax.text(49, 64, "GATEWAY: a2a-gateway-task (ECS Fargate)", ha='center', va='center', fontsize=10, fontweight='bold', color='#D46B08')
    ax.text(49, 57, "FastAPI Protocol Gateway • App Mesh Envoy Sidecar", ha='center', va='center', fontsize=8, color=G_DARK)

    s_sql = FancyBboxPatch((28, 33), 13, 14, boxstyle="round,pad=0.6,rounding_size=1.5",
                           facecolor=WHITE, edgecolor=G_BLUE, linewidth=1.2)
    ax.add_patch(s_sql)
    ax.text(34.5, 42, "SQL Fargate", ha='center', va='center', fontsize=9, fontweight='bold', color=G_BLUE)
    ax.text(34.5, 36, "LangGraph Task\nHITL + PII", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    s_rag = FancyBboxPatch((42.5, 33), 13, 14, boxstyle="round,pad=0.6,rounding_size=1.5",
                           facecolor=WHITE, edgecolor=G_GREEN, linewidth=1.2)
    ax.add_patch(s_rag)
    ax.text(49, 42, "RAG Fargate", ha='center', va='center', fontsize=9, fontweight='bold', color=G_GREEN)
    ax.text(49, 36, "LangChain Task\nVector Engine", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    s_pod = FancyBboxPatch((57, 33), 13, 14, boxstyle="round,pad=0.6,rounding_size=1.5",
                           facecolor=WHITE, edgecolor=G_YELLOW, linewidth=1.2)
    ax.add_patch(s_pod)
    ax.text(63.5, 42, "Podcast Task", ha='center', va='center', fontsize=9, fontweight='bold', color='#B06000')
    ax.text(63.5, 36, "Google ADK\nDialogue Studio", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    mesh_box = FancyBboxPatch((28, 16), 42, 12, boxstyle="round,pad=0.6,rounding_size=1.5",
                              facecolor='#FFF8E1', edgecolor='#FFB300', linewidth=1)
    ax.add_patch(mesh_box)
    ax.text(49, 23.5, "AWS App Mesh (mTLS & Cloud Map Service Discovery)", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#B06000')
    ax.text(49, 18.5, "Encrypted peer-to-peer agent transit with automatic retries", ha='center', va='center', fontsize=7.5, color=G_DARK)

    # AWS Backplane
    backplane = FancyBboxPatch((76, 12), 21, 70, boxstyle="round,pad=1,rounding_size=2",
                               facecolor=G_BG, edgecolor=G_BORDER, linewidth=1.5)
    ax.add_patch(backplane)
    ax.text(86.5, 78, "AWS Managed Services", ha='center', va='center', fontsize=10.5, fontweight='bold', color=G_DARK)

    b1 = FancyBboxPatch((78, 60), 17, 13, boxstyle="round,pad=0.6,rounding_size=1.5", facecolor=WHITE, edgecolor=G_BORDER)
    ax.add_patch(b1)
    ax.text(86.5, 68, "Secrets Manager", ha='center', va='center', fontsize=8.5, fontweight='bold', color=G_DARK)
    ax.text(86.5, 63, "API Keys & DB Vault", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    b2 = FancyBboxPatch((78, 44), 17, 13, boxstyle="round,pad=0.6,rounding_size=1.5", facecolor=WHITE, edgecolor=G_BORDER)
    ax.add_patch(b2)
    ax.text(86.5, 52, "Amazon Aurora", ha='center', va='center', fontsize=8.5, fontweight='bold', color=G_DARK)
    ax.text(86.5, 47, "Serverless PostgreSQL", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    b3 = FancyBboxPatch((78, 28), 17, 13, boxstyle="round,pad=0.6,rounding_size=1.5", facecolor=WHITE, edgecolor=G_BORDER)
    ax.add_patch(b3)
    ax.text(86.5, 36, "OpenSearch / S3", ha='center', va='center', fontsize=8.5, fontweight='bold', color=G_DARK)
    ax.text(86.5, 31, "Vector Store & Audio", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    b4 = FancyBboxPatch((78, 15), 17, 10, boxstyle="round,pad=0.6,rounding_size=1.5", facecolor=WHITE, edgecolor=G_BORDER)
    ax.add_patch(b4)
    ax.text(86.5, 20.5, "CloudWatch Metrics", ha='center', va='center', fontsize=8, fontweight='bold', color=G_DARK)

    arrow_kw = dict(arrowstyle="-|>", color='#D46B08', lw=1.5, mutation_scale=12)
    ax.annotate("", xy=(25, 61), xytext=(19, 61), arrowprops=arrow_kw)
    ax.annotate("", xy=(28, 61), xytext=(22, 38), arrowprops=arrow_kw)
    ax.annotate("", xy=(34.5, 47), xytext=(34.5, 52), arrowprops=dict(arrowstyle="<|-|>", color=G_BLUE, lw=1.2))
    ax.annotate("", xy=(49, 47), xytext=(49, 52), arrowprops=dict(arrowstyle="<|-|>", color=G_GREEN, lw=1.2))
    ax.annotate("", xy=(63.5, 47), xytext=(63.5, 52), arrowprops=dict(arrowstyle="<|-|>", color=G_YELLOW, lw=1.2))
    ax.annotate("", xy=(76, 52), xytext=(70, 52), arrowprops=arrow_kw)

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/diagram6_aws_ecs_deployment.png", dpi=300)
    plt.close()
    print("✅ Created: diagram6_aws_ecs_deployment.png")

# ── 3. AZURE CONTAINER APPS ARCHITECTURE ──────────────────────────────────────
def generate_azure_diagram():
    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=300)
    ax.set_facecolor(WHITE)
    fig.patch.set_facecolor(WHITE)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title
    ax.text(50, 95, "Microsoft Azure: Production A2A Architecture",
            ha='center', va='center', fontsize=15, fontweight='bold', color=G_DARK)
    ax.text(50, 90.5, "Microservice Multi-Agent Mesh on Azure Container Apps (ACA) with Dapr & APIM",
            ha='center', va='center', fontsize=9.5, color=G_MUTED)

    # Ingress
    ingress_box = FancyBboxPatch((3, 20), 18, 62, boxstyle="round,pad=1,rounding_size=2",
                                facecolor=G_BG, edgecolor=G_BORDER, linewidth=1.5)
    ax.add_patch(ingress_box)
    ax.text(12, 77, "Azure Edge", ha='center', va='center', fontsize=11, fontweight='bold', color=G_DARK)

    p1 = FancyBboxPatch((5, 52), 14, 18, boxstyle="round,pad=0.8,rounding_size=1.5",
                        facecolor='#E1F5FE', edgecolor='#0078D4', linewidth=1.2)
    ax.add_patch(p1)
    ax.text(12, 63, "Azure Front Door\n+ WAF", ha='center', va='center', fontsize=9, fontweight='bold', color='#0078D4')
    ax.text(12, 56, "Global Ingress", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    p2 = FancyBboxPatch((5, 26), 14, 20, boxstyle="round,pad=0.8,rounding_size=1.5",
                        facecolor='#E1F5FE', edgecolor='#0078D4', linewidth=1.2)
    ax.add_patch(p2)
    ax.text(12, 38, "Azure API\nManagement (APIM)", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#0078D4')
    ax.text(12, 30, "Agent Card Portal\nOAuth2 / mTLS", ha='center', va='center', fontsize=7.5, color=G_DARK)

    # ACA Environment Box
    aca_box = FancyBboxPatch((25, 12), 48, 70, boxstyle="round,pad=1.5,rounding_size=3",
                             facecolor='#F8F9FA', edgecolor='#0078D4', linewidth=1.8, linestyle='--')
    ax.add_patch(aca_box)
    ax.text(49, 78, "Azure Container Apps (ACA) Managed Environment", ha='center', va='center',
            fontsize=11.5, fontweight='bold', color='#0078D4')

    s_gw = FancyBboxPatch((28, 52), 42, 18, boxstyle="round,pad=0.8,rounding_size=2",
                          facecolor=WHITE, edgecolor='#0078D4', linewidth=1.8)
    ax.add_patch(s_gw)
    ax.text(49, 64, "GATEWAY: a2a-gateway-app (Azure Container App)", ha='center', va='center', fontsize=10, fontweight='bold', color='#0078D4')
    ax.text(49, 57, "FastAPI Protocol Gateway • Dapr Sidecar • Web Inspector UI", ha='center', va='center', fontsize=8, color=G_DARK)

    s_sql = FancyBboxPatch((28, 33), 13, 14, boxstyle="round,pad=0.6,rounding_size=1.5",
                           facecolor=WHITE, edgecolor=G_BLUE, linewidth=1.2)
    ax.add_patch(s_sql)
    ax.text(34.5, 42, "SQL ACA", ha='center', va='center', fontsize=9, fontweight='bold', color=G_BLUE)
    ax.text(34.5, 36, "LangGraph Task\nHITL + PII", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    s_rag = FancyBboxPatch((42.5, 33), 13, 14, boxstyle="round,pad=0.6,rounding_size=1.5",
                           facecolor=WHITE, edgecolor=G_GREEN, linewidth=1.2)
    ax.add_patch(s_rag)
    ax.text(49, 42, "RAG ACA", ha='center', va='center', fontsize=9, fontweight='bold', color=G_GREEN)
    ax.text(49, 36, "LangChain Task\nVector Engine", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    s_pod = FancyBboxPatch((57, 33), 13, 14, boxstyle="round,pad=0.6,rounding_size=1.5",
                           facecolor=WHITE, edgecolor=G_YELLOW, linewidth=1.2)
    ax.add_patch(s_pod)
    ax.text(63.5, 42, "Podcast ACA", ha='center', va='center', fontsize=9, fontweight='bold', color='#B06000')
    ax.text(63.5, 36, "Google ADK\nDialogue Studio", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    dapr_box = FancyBboxPatch((28, 16), 42, 12, boxstyle="round,pad=0.6,rounding_size=1.5",
                              facecolor='#E8EAF6', edgecolor='#3F51B5', linewidth=1)
    ax.add_patch(dapr_box)
    ax.text(49, 23.5, "Dapr (Distributed Application Runtime) Mesh", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#303F9F')
    ax.text(49, 18.5, "Service-to-service invocation with automatic mTLS and distributed tracing", ha='center', va='center', fontsize=7.5, color=G_DARK)

    # Azure Backplane
    backplane = FancyBboxPatch((76, 12), 21, 70, boxstyle="round,pad=1,rounding_size=2",
                               facecolor=G_BG, edgecolor=G_BORDER, linewidth=1.5)
    ax.add_patch(backplane)
    ax.text(86.5, 78, "Azure Platform Services", ha='center', va='center', fontsize=10.5, fontweight='bold', color=G_DARK)

    b1 = FancyBboxPatch((78, 60), 17, 13, boxstyle="round,pad=0.6,rounding_size=1.5", facecolor=WHITE, edgecolor=G_BORDER)
    ax.add_patch(b1)
    ax.text(86.5, 68, "Azure Key Vault", ha='center', va='center', fontsize=8.5, fontweight='bold', color=G_DARK)
    ax.text(86.5, 63, "Managed Identity", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    b2 = FancyBboxPatch((78, 44), 17, 13, boxstyle="round,pad=0.6,rounding_size=1.5", facecolor=WHITE, edgecolor=G_BORDER)
    ax.add_patch(b2)
    ax.text(86.5, 52, "Azure AI Search", ha='center', va='center', fontsize=8.5, fontweight='bold', color=G_DARK)
    ax.text(86.5, 47, "Vector DB & Index", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    b3 = FancyBboxPatch((78, 28), 17, 13, boxstyle="round,pad=0.6,rounding_size=1.5", facecolor=WHITE, edgecolor=G_BORDER)
    ax.add_patch(b3)
    ax.text(86.5, 36, "Azure Blob / Cosmos", ha='center', va='center', fontsize=8.5, fontweight='bold', color=G_DARK)
    ax.text(86.5, 31, "Task Artifacts", ha='center', va='center', fontsize=7.5, color=G_MUTED)

    b4 = FancyBboxPatch((78, 15), 17, 10, boxstyle="round,pad=0.6,rounding_size=1.5", facecolor=WHITE, edgecolor=G_BORDER)
    ax.add_patch(b4)
    ax.text(86.5, 20.5, "Application Insights", ha='center', va='center', fontsize=8, fontweight='bold', color=G_DARK)

    arrow_kw = dict(arrowstyle="-|>", color='#0078D4', lw=1.5, mutation_scale=12)
    ax.annotate("", xy=(25, 61), xytext=(19, 61), arrowprops=arrow_kw)
    ax.annotate("", xy=(28, 61), xytext=(22, 38), arrowprops=arrow_kw)
    ax.annotate("", xy=(34.5, 47), xytext=(34.5, 52), arrowprops=dict(arrowstyle="<|-|>", color=G_BLUE, lw=1.2))
    ax.annotate("", xy=(49, 47), xytext=(49, 52), arrowprops=dict(arrowstyle="<|-|>", color=G_GREEN, lw=1.2))
    ax.annotate("", xy=(63.5, 47), xytext=(63.5, 52), arrowprops=dict(arrowstyle="<|-|>", color=G_YELLOW, lw=1.2))
    ax.annotate("", xy=(76, 52), xytext=(70, 52), arrowprops=arrow_kw)

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/diagram7_azure_aca_deployment.png", dpi=300)
    plt.close()
    print("✅ Created: diagram7_azure_aca_deployment.png")

if __name__ == "__main__":
    generate_gcp_diagram()
    generate_aws_diagram()
    generate_azure_diagram()
