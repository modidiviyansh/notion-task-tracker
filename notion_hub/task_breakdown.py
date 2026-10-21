"""
AI-Powered Task Decomposition and Subtask Generation Engine.
Decomposes complex deliverables into sized, prioritized subtasks
and automatically links them to the Notion Tasks database.
"""
import re
from typing import Dict, Any, List, Optional
from .client import NotionClient

# Archetype templates for common software, engineering, and operational tasks
BREAKDOWN_ARCHETYPES = {
    "system": [
        ("Architecture & Data Schema Modeling", 3.0, "P2 - High", "Backend", "📐 Database schema, entity relationships, and core state machines."),
        ("Core Backend API & Logic Implementation", 4.5, "P2 - High", "Backend", "⚙️ Business rules, validation, and endpoint handlers."),
        ("User Interface & Interactive Workflows", 3.5, "P3 - Medium", "Frontend", "🎨 Intuitive responsive frontend views and user interactions."),
        ("Integration Testing, Permissions & Audit", 2.0, "P3 - Medium", "QA & Security", "🛡️ RBAC permissions, audit trail logging, and edge case tests.")
    ],
    "video": [
        ("Scripting, Storyboard & Visual Concept", 2.5, "P2 - High", "Design", "📝 Narrative structure, key message beats, and asset list."),
        ("Raw Footage Assembly & Pacing Cut", 3.5, "P2 - High", "Design", "🎬 Timeline rough cut, transitions, and audio sync."),
        ("Motion Graphics, Titles & Brand Polish", 2.5, "P3 - Medium", "Design", "✨ Title cards, captions, and visual effects."),
        ("Final Audio Mix & Multi-Platform Export", 1.5, "P3 - Medium", "Design", "🔊 Sound mastering and platform-specific encodes.")
    ],
    "dashboard": [
        ("Data Aggregation & Metric Formulas", 2.5, "P2 - High", "Backend", "🧮 Calculation logic, weighted metrics, and query filters."),
        ("Layout Structure & KPI Card Grid", 2.5, "P2 - High", "Frontend", "📊 Visual tiles, status badges, and typography hierarchy."),
        ("Dynamic Filtering & Interactive Views", 3.0, "P3 - Medium", "Frontend", "🔍 Multi-dimensional filtering by user, date, and priority."),
        ("User Testing & Responsive Polish", 1.5, "P4 - Low", "QA & Security", "📱 Verification across desktop, tablet, and mobile views.")
    ],
    "default": [
        ("Requirements Analysis & Scope Definition", 1.5, "P2 - High", "Product", "📋 Acceptance criteria, boundary conditions, and deliverables."),
        ("Implementation & Core Deliverable Build", 4.0, "P2 - High", "Backend", "🔨 Primary execution and functional implementation."),
        ("Review, Verification & Edge Case Handling", 2.0, "P3 - Medium", "QA & Security", "🔍 Quality review, edge cases, and performance checks."),
        ("Documentation & Team Handoff", 1.0, "P4 - Low", "Operations", "📖 Usage documentation, release notes, and deployment handoff.")
    ]
}


def decompose_task(title: str, description: str = "") -> List[Dict[str, Any]]:
    """Analyzes task title and context to generate a structured subtask breakdown."""
    lower_text = f"{title.lower()} {description.lower()}"

    if any(k in lower_text for k in ["video", "clip", "editing", "cut", "footage", "motion", "youtube"]):
        template = BREAKDOWN_ARCHETYPES["video"]
    elif any(k in lower_text for k in ["dashboard", "analytics", "tracker", "metrics", "chart", "report", "board"]):
        template = BREAKDOWN_ARCHETYPES["dashboard"]
    elif any(k in lower_text for k in ["system", "erp", "reception", "api", "database", "platform", "backend", "portal", "engine"]):
        template = BREAKDOWN_ARCHETYPES["system"]
    else:
        template = BREAKDOWN_ARCHETYPES["default"]

    subtasks = []
    for sub_title, hours, prio, team, notes in template:
        full_sub_title = f"{title} — {sub_title}"
        subtasks.append({
            "title": full_sub_title,
            "estimated_hours": hours,
            "priority": prio,
            "team": team,
            "complexity": "3 - Moderate" if hours >= 3.0 else "2 - Simple",
            "notes": notes,
            "parent_task": title
        })

    return subtasks


def apply_subtasks_to_notion(
    client: NotionClient,
    database_id: str,
    parent_task_title: str,
    subtasks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Creates generated subtasks in the Notion database and tags them with parent deliverable."""
    clean_db_id = database_id.replace("-", "")
    created = []

    for st in subtasks:
        props = {
            "Task Name": {"title": [{"text": {"content": st["title"]}}]},
            "Priority": {"select": {"name": st["priority"]}},
            "Status": {"status": {"name": "To Do"}},
            "Estimated Hours": {"number": st["estimated_hours"]},
            "Complexity": {"select": {"name": st["complexity"]}},
            "Action Required By": {"select": {"name": "Assignee (In Flight)"}},
            "Task Details": {"rich_text": [{"text": {"content": f"Parent: {parent_task_title} • {st['notes']}"}}]}
        }
        res = client._request("POST", "/pages", {
            "parent": {"database_id": clean_db_id},
            "properties": props,
            "icon": {"type": "emoji", "emoji": "🔹"}
        })
        created.append(res)

    return created
