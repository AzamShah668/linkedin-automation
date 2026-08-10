#!/usr/bin/env python3
"""Seed the Content Hub with the 20 project showcases for Tue/Thu slots.

Run once:  py -3 tools/seed_content_hub.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from content_hub_db import connect, add_idea, stats

# The 20 projects from the approved content calendar
PROJECTS = [
    {
        "title": "LinkedIn Job Hunt Autopilot — Full Agent Architecture",
        "insight": "MCP-first autonomous pipeline: discovery, outreach, CV tailoring, Slack mobile approval. 5-layer architecture with Playwright stealth and FLUX.1 image studio.",
        "hashtags": "#SoftwareEngineering #AI #Automation #MCP #Python #LinkedIn",
    },
    {
        "title": "AZNA-CLOUD — Private Cloud Platform for University GPU Access",
        "insight": "30 students, 1 shared server, zero isolation. Built a full VM management platform with 1-click deploy, GPU scheduling, admin command center, and AI ChatOps.",
        "hashtags": "#CloudComputing #DevOps #PlatformEngineering #SelfHosted #GPU",
    },
    {
        "title": "AXM Production RAG — Hybrid Retrieval with Cross-Encoder Re-ranking",
        "insight": "Vector + BM25 hybrid search, cross-encoder re-ranking, LLM-as-a-Judge CI/CD gates. Production-grade retrieval pipeline for enterprise knowledge bases.",
        "hashtags": "#RAG #AI #MachineLearning #NLP #Python #VectorSearch",
    },
    {
        "title": "Desktop Computer-Use Vision Agent — GUI Automation with UIA",
        "insight": "Free models score 0/8 on GUI tasks without grounding. UIA accessibility tree + vision model = reliable screen-control agent. Answer bank prevents hallucinated clicks.",
        "hashtags": "#AI #ComputerVision #Automation #DesktopAgent #Accessibility",
    },
    {
        "title": "MCP Server Hub — Building Stdio RPC Tool Orchestration",
        "insight": "Model Context Protocol for zero-latency tool calling. JSON-RPC over stdio connecting Playwright, image generation, Notion, and LinkedIn APIs.",
        "hashtags": "#MCP #AI #APIDesign #SystemDesign #Python #Tooling",
    },
    {
        "title": "FLUX.1 & Imagen 3 — AI Visual Content Studio",
        "insight": "Free unlimited 8K image generation via Pollinations API. Three-engine fallback chain. Generates LinkedIn carousels, hero images, and infographics programmatically.",
        "hashtags": "#AI #GenerativeAI #ImageGeneration #ContentCreation #FLUX",
    },
    {
        "title": "Slack Mobile Approval Gate — Human-in-the-Loop for Bot Safety",
        "insight": "One-tap mobile approval via Slack webhooks before any automated outreach dispatches. The human review queue that keeps accounts safe.",
        "hashtags": "#Slack #Automation #HumanInTheLoop #BotSafety #DevOps",
    },
    {
        "title": "Stealth Playwright Automation — Anti-Detection Browser Control",
        "insight": "Persistent browser profiles, randomized delays, fingerprint masking. How to automate without getting detected or banned.",
        "hashtags": "#Playwright #Automation #WebScraping #Testing #JavaScript",
    },
    {
        "title": "Notion as a Production Database — Two-Way Sync Architecture",
        "insight": "Notion is the system of record, SQLite is the local mirror. Status changes win locally until pushed. Self-correcting sync with timestamp comparison.",
        "hashtags": "#Notion #Databases #Architecture #DataSync #Productivity",
    },
    {
        "title": "Tailored CV Engine — AI-Powered Resume Customization",
        "insight": "Claude as a subprocess for the one artifact a human reads. Free model fills forms, premium model writes the CV. Cost: zero rupees per day.",
        "hashtags": "#Resume #AI #CareerDevelopment #JobSearch #Automation",
    },
    {
        "title": "Kubernetes GPU Scheduling — ML Training on K3s Clusters",
        "insight": "Lightweight K3s on bare metal for ML workloads. GPU time-slicing, priority queues, and fair-share scheduling for multi-tenant training.",
        "hashtags": "#Kubernetes #K3s #MLOps #GPU #DevOps #CloudNative",
    },
    {
        "title": "Redis Distributed Locking — Preventing Race Conditions at Scale",
        "insight": "Redlock algorithm for multi-instance coordination. How we prevented double-sends in the outreach pipeline with TTL-based mutex locks.",
        "hashtags": "#Redis #DistributedSystems #Concurrency #Backend #Architecture",
    },
    {
        "title": "Ansible Bare-Metal Provisioning — Zero-Touch Server Setup",
        "insight": "From racked hardware to running VMs in 20 minutes. Idempotent playbooks, vault secrets, and rolling updates for university infrastructure.",
        "hashtags": "#Ansible #DevOps #InfrastructureAsCode #Automation #Linux",
    },
    {
        "title": "Proxmox Virtualization — Building a Private Cloud from Scratch",
        "insight": "KVM/LXC hypervisor on commodity hardware. HA clustering, ZFS storage, Ceph for distributed block storage, and API-driven VM lifecycle.",
        "hashtags": "#Proxmox #Virtualization #HomeServer #SelfHosted #Linux",
    },
    {
        "title": "Gmail API Integration — Automated Recruiter Outreach Pipeline",
        "insight": "OAuth2 + Gmail API for delivering tailored CVs. MX record detection decides Drive sharing mode. Throttled, randomized, business-hours-only sends.",
        "hashtags": "#Gmail #API #Automation #EmailMarketing #Python",
    },
    {
        "title": "LinkedIn Easy Apply Bot — The Answer Bank Architecture",
        "insight": "19 dictionary lookups and 1 real question per form. Answer bank prevents hallucinated responses. Blank beats wrong, skip beats invent.",
        "hashtags": "#LinkedIn #Automation #JobSearch #AI #Python",
    },
    {
        "title": "ATS Audit Tool — Resume Scoring Against Job Descriptions",
        "insight": "Keyword extraction, skill matching, and gap analysis. Score your resume against any job description before applying.",
        "hashtags": "#ATS #Resume #JobSearch #NLP #CareerDevelopment",
    },
    {
        "title": "Real-Time Dashboard — SQLite + Express Web UI for Pipeline Monitoring",
        "insight": "Live web dashboard serving from SQLite. Four pipeline stages visualized, one-click status changes, Notion push reconciliation.",
        "hashtags": "#Dashboard #WebDev #SQLite #DataVisualization #Monitoring",
    },
    {
        "title": "CI/CD with LLM-as-a-Judge — Automated Quality Gates for AI Outputs",
        "insight": "LLM evaluates LLM outputs before deployment. Regression detection, factuality checks, and tone consistency scoring in the PR pipeline.",
        "hashtags": "#CICD #AI #MLOps #QualityAssurance #DevOps",
    },
    {
        "title": "Graphify Knowledge Graph — Codebase-Aware AI Context Engine",
        "insight": "AST-parsed code graph with 75 nodes, 125 edges, 14 communities. Query with natural language for 19.5x token reduction vs bulk file reading.",
        "hashtags": "#KnowledgeGraph #AI #DeveloperTools #CodeAnalysis #Python",
    },
]


def main() -> None:
    conn = connect()

    # Check if already seeded
    existing = stats(conn)
    if existing["total"] > 0:
        print(f"Content Hub already has {existing['total']} posts. Skipping seed.")
        print("Use --force to re-seed (will add duplicates).")
        if "--force" not in sys.argv:
            return

    # Calculate dates: Tue/Thu starting from next Tuesday
    today = dt.date.today()
    # Find next Tuesday
    days_until_tue = (1 - today.weekday()) % 7
    if days_until_tue == 0:
        days_until_tue = 7
    next_tue = today + dt.timedelta(days=days_until_tue)

    added = 0
    for i, project in enumerate(PROJECTS):
        # Alternate Tue/Thu
        week_offset = i // 2
        day_offset = 0 if i % 2 == 0 else 2  # Tue=0, Thu=+2
        scheduled = next_tue + dt.timedelta(weeks=week_offset, days=day_offset)
        day_name = "tue" if i % 2 == 0 else "thu"

        row_id = add_idea(
            conn,
            title=project["title"],
            post_type="project",
            insight=project["insight"],
            scheduled_day=day_name,
            scheduled_date=scheduled.isoformat(),
            source="seed-script",
            hashtags=project["hashtags"],
        )
        added += 1
        print(f"  #{row_id:>3} [{day_name.upper()}] {scheduled} | {project['title'][:60]}")

    s = stats(conn)
    print(f"\nSeeded {added} project showcases.")
    print(f"Content Hub now has {s['total']} post(s)")
    print(f"  By type: {json.dumps(s['by_type'])}")
    print(f"  By status: {json.dumps(s['by_status'])}")
    print(f"\nSchedule spans {PROJECTS[0]['title'][:30]}... to {PROJECTS[-1]['title'][:30]}...")
    print(f"  From {next_tue} to {next_tue + dt.timedelta(weeks=9, days=2)}")


if __name__ == "__main__":
    import json
    main()
