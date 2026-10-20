"""
WASP Engine: Work Analysis System & Profile Dashboard
Enterprise-grade task management, multi-horizon velocity analytics,
profile accountability, and automated backlog construction.
"""
import sys
import json
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from .client import NotionClient, NotionError

# Base Parent Page in Notion (None creates top-level Workspace page in sidebar)
DEFAULT_WORKSPACE_PAGE_ID: Optional[str] = None
PEOPLE_DATABASE_ID = "d3df1bcf-f9b8-82df-b0d8-014512d331ec"

PRIORITY_WEIGHTS = {
    "P1 - Urgent": 500,
    "P2 - High": 250,
    "P3 - Medium": 100,
    "P4 - Low": 25
}

WASP_SCHEMA = {
    "Task Name": {"title": {}},
    "Status": {
        "status": {
            "options": [
                {"name": "Backlog", "color": "gray"},
                {"name": "To Do", "color": "default"},
                {"name": "In Progress", "color": "blue"},
                {"name": "In Review", "color": "purple"},
                {"name": "Done", "color": "green"},
                {"name": "Archived", "color": "brown"}
            ]
        }
    },
    "Priority": {
        "select": {
            "options": [
                {"name": "P1 - Urgent", "color": "red"},
                {"name": "P2 - High", "color": "orange"},
                {"name": "P3 - Medium", "color": "yellow"},
                {"name": "P4 - Low", "color": "blue"}
            ]
        }
    },
    "Due Date": {"date": {}},
    "End Date": {"date": {}},
    "Completed At": {"date": {}},
    "Category": {
        "select": {
            "options": [
                {"name": "🚀 Product & Feature", "color": "purple"},
                {"name": "🛠️ Engineering & Tech", "color": "blue"},
                {"name": "🎨 UI / UX Design", "color": "pink"},
                {"name": "📈 Growth & Marketing", "color": "green"},
                {"name": "⚙️ Operations & Chores", "color": "gray"},
                {"name": "💡 Research & Strategy", "color": "yellow"}
            ]
        }
    },
    "Team / Pod": {
        "select": {
            "options": [
                {"name": "Frontend", "color": "blue"},
                {"name": "Backend", "color": "purple"},
                {"name": "DevOps & Infra", "color": "orange"},
                {"name": "Design", "color": "pink"},
                {"name": "Product", "color": "green"},
                {"name": "QA & Security", "color": "red"}
            ]
        }
    },
    "Action Required By": {
        "select": {
            "options": [
                {"name": "Assignee (In Flight)", "color": "blue"},
                {"name": "Reviewer (Code/Spec Review)", "color": "purple"},
                {"name": "Reporter (Clarification Needed)", "color": "yellow"},
                {"name": "Blocked (Waiting on External)", "color": "red"},
                {"name": "None (Completed/Backlog)", "color": "default"}
            ]
        }
    },
    "Assignee": {"people": {}},
    "Reviewer": {"people": {}},
    "Eisenhower Matrix": {
        "select": {
            "options": [
                {"name": "Q1: Do First (Urgent & Important)", "color": "red"},
                {"name": "Q2: Schedule (Important & Not Urgent)", "color": "blue"},
                {"name": "Q3: Delegate (Urgent & Not Important)", "color": "yellow"},
                {"name": "Q4: Eliminate (Low Urgency & Low Impact)", "color": "gray"}
            ]
        }
    },
    "Complexity": {
        "select": {
            "options": [
                {"name": "⭐ 1 - Trivial", "color": "gray"},
                {"name": "⭐⭐ 2 - Simple", "color": "blue"},
                {"name": "⭐⭐⭐ 3 - Moderate", "color": "yellow"},
                {"name": "⭐⭐⭐⭐ 4 - Complex", "color": "orange"},
                {"name": "⭐⭐⭐⭐⭐ 5 - Epic", "color": "red"}
            ]
        }
    },
    "Task Details": {"rich_text": {}},
    "Estimated Hours": {"number": {"format": "number"}},
    "Actual Hours": {"number": {"format": "number"}},
    "Original Backlog Item": {"checkbox": {}},
    "Created At": {"created_time": {}},
    "Created By": {"created_by": {}},
    "Last Edited Time": {"last_edited_time": {}},
    "Last Edited By": {"last_edited_by": {}},
    "Days Elapsed": {
        "formula": {
            "expression": 'dateBetween(now(), prop("Created At"), "days")'
        }
    },
    "Priority Score": {
        "formula": {
            "expression": (
                'if(prop("Status") == "Done" or prop("Status") == "Archived", 0, '
                'if(prop("Priority") == "P1 - Urgent", 500 + (dateBetween(now(), prop("Created At"), "days") * 10) + if(empty(prop("End Date")), 0, if(now() > prop("End Date"), 100, 0)), '
                'if(prop("Priority") == "P2 - High", 250 + (dateBetween(now(), prop("Created At"), "days") * 5) + if(empty(prop("End Date")), 0, if(now() > prop("End Date"), 75, 0)), '
                'if(prop("Priority") == "P3 - Medium", 100 + (dateBetween(now(), prop("Created At"), "days") * 2) + if(empty(prop("End Date")), 0, if(now() > prop("End Date"), 50, 0)), '
                '25 + round(dateBetween(now(), prop("Created At"), "days") * 0.5) + if(empty(prop("End Date")), 0, if(now() > prop("End Date"), 25, 0))))))'
            )
        }
    },
    "Escalation Level": {
        "formula": {
            "expression": (
                'if(prop("Status") == "Done", "✅ RESOLVED", '
                'if(prop("Priority Score") >= 500, "🔥 CRITICAL OVERDUE", '
                'if(prop("Priority Score") >= 250, "🚨 HIGH URGENCY", '
                'if(prop("Priority Score") >= 100, "⚠️ ELEVATED", "🟢 STABLE"))))'
            )
        }
    },
    "Backlog State": {
        "formula": {
            "expression": (
                'if(prop("Status") == "Done" and (prop("Original Backlog Item") or (not empty(prop("End Date")) and prop("Completed At") > prop("End Date"))), "🏆 Conquered Backlog Debt", '
                'if(prop("Status") == "Done", "✅ Completed On Time", '
                'if(empty(prop("End Date")), "📦 Unscheduled Backlog", '
                'if(now() > prop("End Date"), "⚠️ Rolled-Over Backlog Debt", "🚀 Active Sprint Horizon"))))'
            )
        }
    }
}


def generate_wasp_task_blueprint(
    title: str,
    details: str = "",
    priority: str = "P2 - High",
    end_date: str = "TBD",
    team_pod: str = "Engineering",
    complexity: str = "⭐⭐⭐ 3 - Moderate",
    subtasks: Optional[List[str]] = None,
    estimated_hours: float = 0,
    actual_hours: float = 0
) -> str:
    """Build standardized 6-header blueprint markdown for WASP task pages."""
    subtask_items = subtasks or [
        "Architect technical requirements and edge cases",
        "Implement core functionality and unit tests",
        "Execute peer review and verification sign-off"
    ]
    subtask_md = "\n".join([f"- [ ] {st}" for st in subtask_items])

    return f"""# 📌 Task Overview & Definition of Done
> **Objective**: {details or f"Deliver '{title}' with exceptional quality and zero regressions."}

- **Definition of Done (Acceptance Criteria)**:
  - [ ] Implementation complete and verified against requirements
  - [ ] Code/Design reviewed and approved by Reviewer
  - [ ] Automated tests passing with zero regressions
  - [ ] Technical documentation & release notes updated

---

# ⚡ Urgency, Priority & Complexity Factor
- **Assigned Priority**: `{priority}`
- **Complexity Rating**: `{complexity}`
- **Target End Date / Cutoff**: `{end_date}`
- **Progressive Organization**: Sized as `{complexity}` with estimated effort `{estimated_hours or 0} hrs`.
- **Priority Scoring Engine**: Base `{priority}` weight escalates daily until completed, plus overdue surge penalty if past `{end_date}`.

---

# 👤 Profile & Team Ownership
- **Functional Pod**: `{team_pod}`
- **Primary Assignee**: *Assign above to claim action*
- **Peer Reviewer**: *Assign above when moving to In Review*
- **Action State**: Update `Action Required By` so the team knows who holds the ball.

---

# 🧩 Subtasks Breakdown
{subtask_md}

---

# ⏱️ Effort Estimation & Time Log
- **Estimated Hours**: `{estimated_hours or 0} hrs`
- **Actual Hours Logged**: `{actual_hours or 0} hrs`
- **Blockers & Dependencies**: None reported.

---

# 📝 Notes & Architecture Decisions
- *Log technical decisions, PR links, meeting minutes, and retrospective takeaways here.*
"""


def setup_wasp_dashboard(
    client: NotionClient,
    parent_page_id: Optional[str] = DEFAULT_WORKSPACE_PAGE_ID
) -> Dict[str, Any]:
    """
    Creates the complete WASP Dashboard (Work Analysis System & Profile Dashboard):
    1. Parent Hub Page
    2. Master Database with 25 properties, formulas, and relations
    3. Links to People / Contributor Profile database
    4. Dual self-relation for subtasks
    5. Realistic demonstration tasks
    6. Executive Admin Scorecard & Profile Dashboard published on Hub Page
    """
    loc_desc = f"under parent page: {parent_page_id}" if parent_page_id else "as a top-level Workspace page in sidebar"
    print(f"🐝 Initializing WASP Dashboard {loc_desc}...")

    # 1. Create WASP Hub Page
    hub_page = client.create_page(
        parent_id=parent_page_id,
        title="🐝 WASP Dashboard : Work Analysis System & Profile Dashboard",
        content_markdown="# 🐝 Initializing WASP Dashboard...\n*Setting up Work Analysis System & Profile Engine...*",
        icon_emoji="🐝"
    )
    hub_page_id = hub_page["id"]
    print(f"✅ Created WASP Hub Page: {hub_page_id}")

    # 2. Create Master Task Database under the Hub Page
    db = client.create_database(
        parent_page_id=hub_page_id,
        title="📋 WASP Work Engine (Tasks & Sprints)",
        properties_schema=WASP_SCHEMA,
        icon_emoji="⚡"
    )
    db_id = db["id"]
    clean_db_id = db_id.replace("-", "")
    print(f"✅ Created WASP Work Engine Database: {clean_db_id}")

    # 3. Add Dual Self-Relation (Parent Task <-> Subtasks)
    print("🔗 Configuring Sub-items Dual Self-Relation (Parent Task <-> Subtasks)...")
    try:
        client._request("PATCH", f"/databases/{clean_db_id}", {
            "properties": {
                "Parent Task": {
                    "relation": {
                        "database_id": clean_db_id,
                        "dual_property": {
                            "synced_property_name": "Subtasks"
                        }
                    }
                }
            }
        })
        print("✅ Dual Self-Relation (Parent Task <-> Subtasks) configured!")
    except Exception as e:
        print(f"⚠️ Subtask relation warning: {e}")
    
    # Try adding Profile link to existing People database if accessible
    print("🔗 Linking Profile / Contributor relation to People database...")
    try:
        client._request("PATCH", f"/databases/{clean_db_id}", {
            "properties": {
                "Profile / Contributor": {
                    "relation": {
                        "database_id": PEOPLE_DATABASE_ID.replace("-", ""),
                        "single_property": {}
                    }
                }
            }
        })
        print("✅ Profile / Contributor relation linked successfully!")
    except Exception as e:
        print(f"⚠️ People database relation warning: {e}")

    # 4. Populate Realistic Seed Tasks
    print("🌱 Populating Seed Work Analysis Tasks...")
    seed_records = _create_wasp_seed_tasks(client, clean_db_id)
    print(f"✅ Created {len(seed_records)} demonstration tasks across all states!")

    # 5. Calculate Initial Analytics
    analytics = calculate_wasp_analytics(client, clean_db_id)

    # 6. Build Rich Executive Hub Page Dashboard Content
    dashboard_md = _build_wasp_dashboard_markdown(clean_db_id, analytics)

    # Append dashboard content to Hub Page (clear placeholder blocks first)
    print("🎨 Formatting Executive WASP Dashboard on Notion Hub Page...")
    client.clear_page_blocks(hub_page_id, keep_types=["child_database"])
    client.append_markdown(hub_page_id, dashboard_md)
    print("✅ WASP Dashboard is Published!")

    # Save local config
    cfg_file = Path.cwd() / ".notion_wasp_config.json"
    with open(cfg_file, "w") as f:
        json.dump({
            "hub_page_id": hub_page_id,
            "database_id": db_id,
            "hub_url": hub_page.get("url", f"https://notion.so/{hub_page_id.replace('-', '')}")
        }, f, indent=2)

    return {
        "hub_page_id": hub_page_id,
        "database_id": db_id,
        "hub_url": hub_page.get("url", f"https://notion.so/{hub_page_id.replace('-', '')}"),
        "analytics": analytics
    }


def _create_wasp_seed_tasks(client: NotionClient, database_id: str) -> List[Dict[str, Any]]:
    """Seed tasks demonstrating all priorities, completion timeframes, and subtask relations."""
    now = datetime.now(timezone.utc)
    d_7_ago = (now - timedelta(days=5)).strftime("%Y-%m-%d")
    d_12_ago = (now - timedelta(days=12)).strftime("%Y-%m-%d")
    d_25_ago = (now - timedelta(days=25)).strftime("%Y-%m-%d")
    d_tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    d_next_week = (now + timedelta(days=7)).strftime("%Y-%m-%d")
    d_overdue = (now - timedelta(days=2)).strftime("%Y-%m-%d")

    records = []

    # 1. Critical Overdue Task (P1 - Urgent: Demonstrates 500+ score and overdue surge)
    overdue = client.create_page(
        parent_id=database_id,
        title="Resolve Production Database Connection Surge",
        content_markdown=generate_wasp_task_blueprint(
            title="Resolve Production Database Connection Surge",
            details="High concurrency connection pooling spikes causing API gateway timeouts.",
            priority="P1 - Urgent",
            end_date=d_overdue,
            team_pod="Backend",
            estimated_hours=6,
            actual_hours=2
        ),
        is_database_parent=True,
        icon_emoji="🔥",
        properties={
            "Task Name": {"title": [{"text": {"content": "Resolve Production Database Connection Surge"}}]},
            "Status": {"status": {"name": "In Progress"}},
            "Priority": {"select": {"name": "P1 - Urgent"}},
            "Due Date": {"date": {"start": d_overdue}},
            "End Date": {"date": {"start": d_overdue}},
            "Category": {"select": {"name": "🛠️ Engineering & Tech"}},
            "Team / Pod": {"select": {"name": "Backend"}},
            "Action Required By": {"select": {"name": "Assignee (In Flight)"}},
            "Eisenhower Matrix": {"select": {"name": "Q1: Do First (Urgent & Important)"}},
            "Task Details": {"rich_text": [{"text": {"content": "Critical latency spike on primary cluster."}}]},
            "Estimated Hours": {"number": 6},
            "Actual Hours": {"number": 2},
            "Original Backlog Item": {"checkbox": False}
        }
    )
    records.append(overdue)

    # 2. Parent Epic with Subtasks (P2 - High)
    epic = client.create_page(
        parent_id=database_id,
        title="Deploy WASP Work Analysis & Profile Suite v1.0",
        content_markdown=generate_wasp_task_blueprint(
            title="Deploy WASP Work Analysis & Profile Suite v1.0",
            details="End-to-end launch of the Work Analysis System and Profile Dashboard.",
            priority="P2 - High",
            end_date=d_tomorrow,
            team_pod="Product",
            subtasks=[
                "Configure 25-property database schema with priority-dominant formulas",
                "Integrate Profile Dashboard with contributor accountability views",
                "Deploy n8n Google Chat Space Card v2 and Gmail notification workflows",
                "Verify multi-horizon velocity tracking (7d, 15d, monthly)"
            ],
            estimated_hours=16,
            actual_hours=12
        ),
        is_database_parent=True,
        icon_emoji="🚀",
        properties={
            "Task Name": {"title": [{"text": {"content": "Deploy WASP Work Analysis & Profile Suite v1.0"}}]},
            "Status": {"status": {"name": "In Progress"}},
            "Priority": {"select": {"name": "P2 - High"}},
            "Due Date": {"date": {"start": d_tomorrow}},
            "End Date": {"date": {"start": d_tomorrow}},
            "Category": {"select": {"name": "🚀 Product & Feature"}},
            "Team / Pod": {"select": {"name": "Product"}},
            "Action Required By": {"select": {"name": "Assignee (In Flight)"}},
            "Eisenhower Matrix": {"select": {"name": "Q1: Do First (Urgent & Important)"}},
            "Estimated Hours": {"number": 16},
            "Actual Hours": {"number": 12},
            "Original Backlog Item": {"checkbox": False}
        }
    )
    epic_id = epic["id"]
    records.append(epic)

    # 3. Subtask 1 (Linked to Epic, Done)
    sub1 = client.create_page(
        parent_id=database_id,
        title="Subtask: Database Schema & Priority-Dominant Formula Engine",
        content_markdown=generate_wasp_task_blueprint(
            title="Subtask: Database Schema & Priority-Dominant Formula Engine",
            details="Formulas for Days Elapsed, Priority Score (500/250/100/25), and Backlog State.",
            priority="P2 - High",
            end_date=d_7_ago,
            team_pod="DevOps & Infra",
            estimated_hours=4,
            actual_hours=4
        ),
        is_database_parent=True,
        icon_emoji="🧩",
        properties={
            "Task Name": {"title": [{"text": {"content": "Subtask: Database Schema & Priority-Dominant Formula Engine"}}]},
            "Status": {"status": {"name": "Done"}},
            "Priority": {"select": {"name": "P2 - High"}},
            "Due Date": {"date": {"start": d_7_ago}},
            "End Date": {"date": {"start": d_7_ago}},
            "Completed At": {"date": {"start": d_7_ago}},
            "Category": {"select": {"name": "🛠️ Engineering & Tech"}},
            "Team / Pod": {"select": {"name": "DevOps & Infra"}},
            "Eisenhower Matrix": {"select": {"name": "Q1: Do First (Urgent & Important)"}},
            "Estimated Hours": {"number": 4},
            "Actual Hours": {"number": 4},
            "Original Backlog Item": {"checkbox": False},
            "Parent Task": {"relation": [{"id": epic_id}]}
        }
    )
    records.append(sub1)

    # 4. Subtask 2 (Linked to Epic, In Review)
    sub2 = client.create_page(
        parent_id=database_id,
        title="Subtask: n8n Google Workspace Automations & Chat Cards",
        content_markdown=generate_wasp_task_blueprint(
            title="Subtask: n8n Google Workspace Automations & Chat Cards",
            details="Ready-to-import JSON workflows for Google Chat spaces and Gmail digests.",
            priority="P2 - High",
            end_date=d_tomorrow,
            team_pod="DevOps & Infra",
            estimated_hours=5,
            actual_hours=3
        ),
        is_database_parent=True,
        icon_emoji="🤖",
        properties={
            "Task Name": {"title": [{"text": {"content": "Subtask: n8n Google Workspace Automations & Chat Cards"}}]},
            "Status": {"status": {"name": "In Review"}},
            "Priority": {"select": {"name": "P2 - High"}},
            "Due Date": {"date": {"start": d_tomorrow}},
            "End Date": {"date": {"start": d_tomorrow}},
            "Category": {"select": {"name": "🛠️ Engineering & Tech"}},
            "Team / Pod": {"select": {"name": "DevOps & Infra"}},
            "Action Required By": {"select": {"name": "Reviewer (Code/Spec Review)"}},
            "Eisenhower Matrix": {"select": {"name": "Q1: Do First (Urgent & Important)"}},
            "Estimated Hours": {"number": 5},
            "Actual Hours": {"number": 3},
            "Original Backlog Item": {"checkbox": False},
            "Parent Task": {"relation": [{"id": epic_id}]}
        }
    )
    records.append(sub2)

    # 5. Backlog Item Cleared (Demonstrates "Previous Backlog Conquered")
    backlog_cleared = client.create_page(
        parent_id=database_id,
        title="Refactor Legacy Microservice Error Middleware",
        content_markdown=generate_wasp_task_blueprint(
            title="Refactor Legacy Microservice Error Middleware",
            details="Old technical debt that lingered in backlog and was conquered this cycle.",
            priority="P3 - Medium",
            end_date=d_7_ago,
            team_pod="Backend",
            estimated_hours=8,
            actual_hours=6
        ),
        is_database_parent=True,
        icon_emoji="🏆",
        properties={
            "Task Name": {"title": [{"text": {"content": "Refactor Legacy Microservice Error Middleware"}}]},
            "Status": {"status": {"name": "Done"}},
            "Priority": {"select": {"name": "P3 - Medium"}},
            "Due Date": {"date": {"start": d_7_ago}},
            "End Date": {"date": {"start": d_7_ago}},
            "Completed At": {"date": {"start": d_7_ago}},
            "Category": {"select": {"name": "🛠️ Engineering & Tech"}},
            "Team / Pod": {"select": {"name": "Backend"}},
            "Eisenhower Matrix": {"select": {"name": "Q2: Schedule (Important & Not Urgent)"}},
            "Estimated Hours": {"number": 8},
            "Actual Hours": {"number": 6},
            "Original Backlog Item": {"checkbox": True}  # Conquered Debt!
        }
    )
    records.append(backlog_cleared)

    # 6. Task Completed in 15-Day window
    task_15d = client.create_page(
        parent_id=database_id,
        title="Security Audit & Secret Token Rotation",
        content_markdown=generate_wasp_task_blueprint(
            title="Security Audit & Secret Token Rotation",
            details="Bi-weekly security hygiene and key rotation.",
            priority="P2 - High",
            end_date=d_12_ago,
            team_pod="QA & Security",
            estimated_hours=5,
            actual_hours=5
        ),
        is_database_parent=True,
        icon_emoji="🛡️",
        properties={
            "Task Name": {"title": [{"text": {"content": "Security Audit & Secret Token Rotation"}}]},
            "Status": {"status": {"name": "Done"}},
            "Priority": {"select": {"name": "P2 - High"}},
            "Due Date": {"date": {"start": d_12_ago}},
            "End Date": {"date": {"start": d_12_ago}},
            "Completed At": {"date": {"start": d_12_ago}},
            "Category": {"select": {"name": "⚙️ Operations & Chores"}},
            "Team / Pod": {"select": {"name": "QA & Security"}},
            "Eisenhower Matrix": {"select": {"name": "Q1: Do First (Urgent & Important)"}},
            "Estimated Hours": {"number": 5},
            "Actual Hours": {"number": 5},
            "Original Backlog Item": {"checkbox": False}
        }
    )
    records.append(task_15d)

    # 7. Task Completed in Monthly window (25 days ago)
    task_monthly = client.create_page(
        parent_id=database_id,
        title="Design System Color & Typography Tokens v2",
        content_markdown=generate_wasp_task_blueprint(
            title="Design System Color & Typography Tokens v2",
            details="Monthly visual design foundation upgrade.",
            priority="P3 - Medium",
            end_date=d_25_ago,
            team_pod="Design",
            estimated_hours=10,
            actual_hours=9
        ),
        is_database_parent=True,
        icon_emoji="🎨",
        properties={
            "Task Name": {"title": [{"text": {"content": "Design System Color & Typography Tokens v2"}}]},
            "Status": {"status": {"name": "Done"}},
            "Priority": {"select": {"name": "P3 - Medium"}},
            "Due Date": {"date": {"start": d_25_ago}},
            "End Date": {"date": {"start": d_25_ago}},
            "Completed At": {"date": {"start": d_25_ago}},
            "Category": {"select": {"name": "🎨 UI / UX Design"}},
            "Team / Pod": {"select": {"name": "Design"}},
            "Eisenhower Matrix": {"select": {"name": "Q2: Schedule (Important & Not Urgent)"}},
            "Estimated Hours": {"number": 10},
            "Actual Hours": {"number": 9},
            "Original Backlog Item": {"checkbox": True}  # Another conquered debt!
        }
    )
    records.append(task_monthly)

    # 8. Unscheduled Backlog Item
    backlog_active = client.create_page(
        parent_id=database_id,
        title="Evaluate Vector Embeddings for Local Search",
        content_markdown=generate_wasp_task_blueprint(
            title="Evaluate Vector Embeddings for Local Search",
            details="Research spike resting in raw backlog pool.",
            priority="P4 - Low",
            end_date="TBD",
            team_pod="Backend",
            estimated_hours=12,
            actual_hours=0
        ),
        is_database_parent=True,
        icon_emoji="💡",
        properties={
            "Task Name": {"title": [{"text": {"content": "Evaluate Vector Embeddings for Local Search"}}]},
            "Status": {"status": {"name": "Backlog"}},
            "Priority": {"select": {"name": "P4 - Low"}},
            "Category": {"select": {"name": "💡 Research & Strategy"}},
            "Team / Pod": {"select": {"name": "Backend"}},
            "Eisenhower Matrix": {"select": {"name": "Q2: Schedule (Important & Not Urgent)"}},
            "Estimated Hours": {"number": 12},
            "Actual Hours": {"number": 0},
            "Original Backlog Item": {"checkbox": True}
        }
    )
    records.append(backlog_active)

    return records


def calculate_wasp_analytics(client: NotionClient, database_id: str) -> Dict[str, Any]:
    """Computes real-time WASP Work Analysis and Profile metrics."""
    clean_id = database_id.replace("-", "")
    items = client.query_database(clean_id)

    now = datetime.now(timezone.utc)
    t_7d = now - timedelta(days=7)
    t_15d = now - timedelta(days=15)
    t_30d = now - timedelta(days=30)

    total_tasks = len(items)
    active_tasks = 0
    completed_tasks = 0
    completed_7d = 0
    completed_15d = 0
    completed_monthly = 0
    backlog_completed = 0
    backlog_active = 0
    hotlist_urgent = 0

    total_estimated_hours = 0.0
    total_actual_hours = 0.0

    priority_dist = {"P1 - Urgent": 0, "P2 - High": 0, "P3 - Medium": 0, "P4 - Low": 0}
    category_dist: Dict[str, int] = {}
    team_dist: Dict[str, int] = {}
    unassigned_count = 0
    in_review_count = 0
    blocked_count = 0

    complexity_dist = {
        "⭐ 1 - Trivial": 0,
        "⭐⭐ 2 - Simple": 0,
        "⭐⭐⭐ 3 - Moderate": 0,
        "⭐⭐⭐⭐ 4 - Complex": 0,
        "⭐⭐⭐⭐⭐ 5 - Epic": 0
    }
    total_complexity_sum = 0
    complexity_count = 0

    for it in items:
        props = it.get("properties", {})

        # Status
        status_obj = (props.get("Status") or {}).get("status") or {}
        status = status_obj.get("name", "To Do")
        is_done = status in ("Done", "Archived")

        if is_done:
            completed_tasks += 1
        else:
            active_tasks += 1

        # Priority
        pri_obj = (props.get("Priority") or {}).get("select") or {}
        pri_name = pri_obj.get("name")
        if pri_name in priority_dist:
            priority_dist[pri_name] += 1

        # Complexity
        comp_obj = (props.get("Complexity") or {}).get("select") or {}
        comp_name = comp_obj.get("name")
        if comp_name:
            complexity_dist[comp_name] = complexity_dist.get(comp_name, 0) + 1
            m = re.search(r"(\d)", comp_name)
            if m:
                total_complexity_sum += int(m.group(1))
                complexity_count += 1

        # Category
        cat_obj = (props.get("Category") or {}).get("select") or {}
        cat_name = cat_obj.get("name", "Uncategorized")
        category_dist[cat_name] = category_dist.get(cat_name, 0) + 1

        # Team / Pod
        pod_obj = (props.get("Team / Pod") or {}).get("select") or {}
        pod_name = pod_obj.get("name")
        if pod_name:
            team_dist[pod_name] = team_dist.get(pod_name, 0) + 1

        # Action Routing & Assignees
        action_req_obj = (props.get("Action Required By") or {}).get("select") or {}
        action_req = action_req_obj.get("name", "")
        assignees = (props.get("Assignee") or {}).get("people", [])

        if not is_done:
            if not assignees:
                unassigned_count += 1
            if status == "In Review" or "Reviewer" in action_req:
                in_review_count += 1
            if status == "Blocked" or "Blocked" in action_req:
                blocked_count += 1

        # Hours
        est = (props.get("Estimated Hours") or {}).get("number") or 0
        act = (props.get("Actual Hours") or {}).get("number") or 0
        total_estimated_hours += est
        total_actual_hours += act

        # Backlog State inspection
        bstate_obj = (props.get("Backlog State") or {}).get("formula") or {}
        bstate = bstate_obj.get("string", "")
        is_orig_backlog = (props.get("Original Backlog Item") or {}).get("checkbox") is True

        if bstate == "🏆 Conquered Backlog Debt" or (is_done and is_orig_backlog):
            backlog_completed += 1
        elif bstate == "⚠️ Rolled-Over Backlog Debt" or (not is_done and status == "Backlog"):
            backlog_active += 1

        # Completed At parsing
        comp_date_obj = (props.get("Completed At") or {}).get("date")
        comp_str = comp_date_obj.get("start") if comp_date_obj else None

        if is_done and comp_str:
            try:
                if "T" in comp_str:
                    comp_dt = datetime.fromisoformat(comp_str.replace("Z", "+00:00"))
                else:
                    comp_dt = datetime.strptime(comp_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

                if comp_dt >= t_7d:
                    completed_7d += 1
                if comp_dt >= t_15d:
                    completed_15d += 1
                if comp_dt >= t_30d:
                    completed_monthly += 1
            except Exception:
                pass
        elif is_done and not comp_str:
            completed_7d += 1
            completed_15d += 1
            completed_monthly += 1

        # Score inspection
        score_obj = (props.get("Priority Score") or {}).get("formula") or {}
        score = score_obj.get("number") or 0
        if not is_done and (score >= 250 or pri_name == "P1 - Urgent"):
            hotlist_urgent += 1

    completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
    avg_complexity = round(total_complexity_sum / complexity_count, 1) if complexity_count > 0 else 3.0

    return {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_tasks": total_tasks,
        "active_tasks": active_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate_pct": completion_rate,
        "completed_7d": completed_7d,
        "completed_15d": completed_15d,
        "completed_monthly": completed_monthly,
        "backlog_cleared_count": backlog_completed,
        "backlog_active_count": backlog_active,
        "hotlist_urgent_count": hotlist_urgent,
        "unassigned_count": unassigned_count,
        "in_review_count": in_review_count,
        "blocked_count": blocked_count,
        "total_estimated_hours": round(total_estimated_hours, 1),
        "total_actual_hours": round(total_actual_hours, 1),
        "priority_distribution": priority_dist,
        "category_distribution": category_dist,
        "team_distribution": team_dist,
        "complexity_distribution": complexity_dist,
        "avg_complexity": avg_complexity
    }


def _build_wasp_dashboard_markdown(database_id: str, a: Dict[str, Any]) -> str:
    """Formats the aesthetic Task Dashboard layout for Notion matching user horizons and focus suite."""
    return f"""# 📋 Task Dashboard
### Work Analysis System & Profile Dashboard

> 🐝 **WASP Command Center** | Work Analysis System & Profile Dashboard | Live Analytics: `{a['timestamp']}`

---

## 🎧 Deep Work & Productivity Suite

> 🍅 **Focus Station**: Boost execution velocity with time-boxed sprints and ambient focus audio.

- 🍅 **Pomodoro Focus Timer (25m Focus / 5m Rest)**: [Launch Pomofocus App](https://pomofocus.io) | [Pomodoro Timer Online](https://pomodorotimer.online)
- ⏱️ **Task Time Tracker**: [Open Toggl Track](https://track.toggl.com) | [Open Clockify](https://clockify.me)
- 🎧 **24/7 Deep Work Lo-Fi Focus Music Radio**:
https://www.youtube.com/watch?v=jfKfPfyJRdk

---

## 📥 Progressive Organization Workflow

> 📥 **Methodology**: Capture first, clarify when necessary, and only add complexity when it actually helps.

- 📥 **Stage 1 — Raw Capture (Inbox)**: Fast, friction-free idea dump. Zero mandatory fields.
- 🔍 **Stage 2 — Clarify & Triage**: Review inbox items, assign Priority tier, End Date cutoff, and Pod ownership.
- ⚡ **Stage 3 — Sizing & Execution**: Add Complexity rating (`⭐ 1 - Trivial` to `⭐⭐⭐⭐⭐ 5 - Epic`), estimated hours, and subtasks.

---

## 👤 Personalized Workbenches (Multi-User Accountability)

> 👤 **Personalized @me Views**: Click the database views above to see your customized workstation.

- 👤 **My Action Workbench** (Filtered by `Assignee contains @me`): Focused queue of tasks assigned directly to you.
- ✍️ **Tasks Created by Me** (Filtered by `Created By contains @me`): Track deliverables you authored or delegated.
- 🤝 **Peer Review Pipeline** (Filtered by `Status is In Review`): Code, design, and specification sign-off queue.
- 🎯 **Open Sprint Grab-and-Go** (Filtered by `Assignee is empty`): Unassigned sprint items ready for pickup.

---

## 🗓️ Visual Workflow Horizons (As shown in Task Dashboard)

| Horizon Section | Description & Filter Rule | Immediate Action |
| :--- | :--- | :--- |
| 🗓️ **TODO Today & Sprint Focus** | `Due Date / End Date is Today` or `Status is In Progress` | Primary daily execution focus |
| ⚠️ **Past Due / Rolled-Over Debt** | `Status != Done` and `End Date < Today` | Urgent slipped items needing attention |
| 📥 **Capture Inbox** | `Assignee is empty` and `Status is Backlog/To Do` | Raw captures awaiting clarification |
| 📅 **Due in Next 7 Days** | `End Date within next 7 days` | Upcoming milestone deliverables |

---

## 📊 Executive KPI Cockpit (Work Analysis Overview)

| Dimension | Metric Value | Operational Context |
| :--- | :--- | :--- |
| ⚡ **7-Day Sprint Output** | **{a['completed_7d']} Tasks Delivered** | Immediate sprint delivery velocity |
| 🗓️ **15-Day Mid-Cycle Output** | **{a['completed_15d']} Tasks Delivered** | Bi-weekly milestone trajectory |
| 📈 **Monthly Throughput (30d)** | **{a['completed_monthly']} Tasks Delivered** | 30-day cumulative strategic delivery |
| 🏆 **Previous Backlog Conquered** | **{a['backlog_cleared_count']} Debt Items Cleared** | Legacy technical debt paid down |
| ⚠️ **Rolled-Over Backlog Debt** | **{a['backlog_active_count']} Tasks Overdue** | Slipped tasks that missed target End Dates |
| 🚨 **High Escalation Hotlist** | **{a['hotlist_urgent_count']} Active Alerts** | Tasks with Urgency Score >= 250 or P1 |
| ⭐ **Average Task Complexity** | **{a.get('avg_complexity', 3.0)} / 5.0 ⭐** | Team deliverable difficulty index |
| 👥 **Team Workload Allocation** | **{a['active_tasks'] - a['unassigned_count']} Assigned / {a['unassigned_count']} Open** | Open sprint pool for grab-and-go |
| 👀 **In Peer Review** | **{a['in_review_count']} Tasks** | Code & design review bottleneck |
| ⏱️ **Effort Planning Accuracy** | **{a['total_estimated_hours']}h est / {a['total_actual_hours']}h act** | Team estimation accuracy ratio |

---

## 🧭 Visual Workflows: Kanban, Calendar & Complexity Views

> 🧭 **Master Views Guide**: 11 curated views configured for the master database above.

1. 🗂️ **Status Kanban Board**: Columns: `Backlog` ➔ `To Do` ➔ `In Progress` ➔ `In Review` ➔ `Done` ➔ `Archived`.
2. 🎯 **Priority Kanban Board**: Columns: `P1 - Urgent` ➔ `P2 - High` ➔ `P3 - Medium` ➔ `P4 - Low`.
3. 🗓️ **Calendar Delivery Planner**: Visual monthly calendar view plotted by End Date & Due Date.
4. ⭐ **Complexity Matrix (1 to 5)**: Sized from `⭐ 1 - Trivial` to `⭐⭐⭐⭐⭐ 5 - Epic`.
5. 👤 **My Action Items**: 1-click personal view filtered by `Assignee contains @me`.
6. ✍️ **Tasks Created by Me**: Filtered by `Created By contains @me`.
7. 🎯 **Open Grab-and-Go Queue**: Filtered by `Assignee is empty` & `Status != Done`.
8. 👀 **Peer Review Pipeline**: Filtered by `Status is In Review`.
9. ⚡ **7-Day Sprint Horizon**: Due in the next 7 days or completed within 7 days.
10. 🏢 **Team Pod Workload Board**: Grouped by `Team / Pod` (Frontend, Backend, DevOps, Design, Product, QA).
11. 🌳 **Parent & Subtask Hierarchy**: Native Notion sub-items tree view.

---

## 🧮 Priority-Dominant Weightable Formula

> 🧮 **Formula Engine**: Base Priority Weight + (Days Elapsed × Tier Rate) + Overdue Penalty

- **Base Weights**: `P1 - Urgent` = **500 pts** (+10/day) | `P2 - High` = **250 pts** (+5/day) | `P3 - Medium` = **100 pts** (+2/day) | `P4 - Low` = **25 pts** (+0.5/day)
- **Overdue Penalty**: Adds `+100 pts` (P1), `+75 pts` (P2), `+50 pts` (P3), `+25 pts` (P4) if current date exceeds `End Date`.
- **Done State**: Drops immediately to `0 pts` upon reaching `Done` or `Archived`.
- **Pill Badges**: `🔥 CRITICAL OVERDUE` (Score >= 500) | `🚨 HIGH URGENCY` (Score >= 250) | `⚠️ ELEVATED` (Score >= 100) | `🟢 STABLE` (Score < 100) | `✅ RESOLVED` (Done)

---

## 🤖 Google Workspace & n8n Automation Workflows

> 🤖 **Automations**: Ready-to-import workflows located in `n8n_workflows/`

- 💬 **Google Chat Space Alerts**: Interactive Card v2 alerts for P1 escalations and overdue tasks.
- ✉️ **Google Workspace Email Briefings**: Weekly executive digests delivered to leadership via Gmail.
- 📅 **Automated Sunday Sprint Rollover**: Auto-rolls missed End Dates into Backlog Debt for Monday sprint planning.

---

## 🛠️ CLI Quick Reference

```bash
# View live Work Analysis metrics
python3 -m notion_hub.cli wasp-metrics

# Fast progressive capture (Stage 1: raw capture without mandatory fields)
python3 -m notion_hub.cli wasp-raise --title "Quick thought / bug fix"

# Full staged raise with End Date, Complexity (1-5), and Team Pod (Stage 2 & 3)
python3 -m notion_hub.cli wasp-raise --title "Implement Cache Cluster" --priority "P1 - Urgent" --end-date "2026-10-25" --complexity 4 --team "Backend" --est-hours 8

# Refresh and clean KPI scoreboard on Notion
python3 -m notion_hub.cli wasp-sync
```
"""


def raise_wasp_task(
    client: NotionClient,
    database_id: str,
    title: str,
    priority: str = "P2 - High",
    due_date: Optional[str] = None,
    end_date: Optional[str] = None,
    complexity: Optional[Any] = None,
    category: Optional[str] = None,
    team: Optional[str] = None,
    action_required_by: Optional[str] = None,
    details: Optional[str] = None,
    estimated_hours: Optional[float] = None,
    eisenhower: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    profile_person_id: Optional[str] = None,
    is_backlog: bool = False
) -> Dict[str, Any]:
    """Raises a new task in the WASP Work Engine with standardized blueprint and progressive organization."""
    clean_id = database_id.replace("-", "")

    valid_categories = [
        "🚀 Product & Feature",
        "🛠️ Engineering & Tech",
        "🎨 UI / UX Design",
        "📈 Growth & Marketing",
        "⚙️ Operations & Chores",
        "💡 Research & Strategy"
    ]
    matched_category = None
    if category:
        for vc in valid_categories:
            if category.lower() in vc.lower():
                matched_category = vc
                break
    if not matched_category:
        matched_category = "🛠️ Engineering & Tech"

    valid_priorities = ["P1 - Urgent", "P2 - High", "P3 - Medium", "P4 - Low"]
    matched_priority = "P2 - High"
    p_upper = priority.strip().upper()
    for vp in valid_priorities:
        if p_upper == vp.upper() or p_upper in vp.upper() or vp.upper().startswith(p_upper):
            matched_priority = vp
            break

    properties: Dict[str, Any] = {
        "Task Name": {"title": [{"text": {"content": title}}]},
        "Status": {"status": {"name": "Backlog" if is_backlog else "To Do"}},
        "Priority": {"select": {"name": matched_priority}},
        "Category": {"select": {"name": matched_category}},
        "Original Backlog Item": {"checkbox": is_backlog}
    }

    # Progressive Complexity Assignment
    valid_complexities = {
        "1": "⭐ 1 - Trivial",
        "trivial": "⭐ 1 - Trivial",
        "2": "⭐⭐ 2 - Simple",
        "simple": "⭐⭐ 2 - Simple",
        "3": "⭐⭐⭐ 3 - Moderate",
        "moderate": "⭐⭐⭐ 3 - Moderate",
        "4": "⭐⭐⭐⭐ 4 - Complex",
        "complex": "⭐⭐⭐⭐ 4 - Complex",
        "5": "⭐⭐⭐⭐⭐ 5 - Epic",
        "epic": "⭐⭐⭐⭐⭐ 5 - Epic"
    }
    matched_complexity = None
    if complexity is not None:
        c_str = str(complexity).strip().lower()
        for k, v in valid_complexities.items():
            if k in c_str:
                matched_complexity = v
                break
        if not matched_complexity:
            matched_complexity = "⭐⭐⭐ 3 - Moderate"
        properties["Complexity"] = {"select": {"name": matched_complexity}}

    if team:
        valid_teams = ["Frontend", "Backend", "DevOps & Infra", "Design", "Product", "QA & Security"]
        for vt in valid_teams:
            if team.lower() in vt.lower():
                properties["Team / Pod"] = {"select": {"name": vt}}
                break

    if action_required_by:
        properties["Action Required By"] = {"select": {"name": action_required_by}}

    effective_end = end_date or due_date
    if due_date:
        properties["Due Date"] = {"date": {"start": due_date}}
    if effective_end:
        properties["End Date"] = {"date": {"start": effective_end}}
    if details:
        properties["Task Details"] = {"rich_text": [{"text": {"content": details}}]}
    if estimated_hours is not None:
        properties["Estimated Hours"] = {"number": estimated_hours}
    if eisenhower:
        properties["Eisenhower Matrix"] = {"select": {"name": eisenhower}}
    if parent_task_id:
        clean_parent = parent_task_id.replace("-", "")
        properties["Parent Task"] = {"relation": [{"id": clean_parent}]}
    if profile_person_id:
        clean_person = profile_person_id.replace("-", "")
        properties["Profile / Contributor"] = {"relation": [{"id": clean_person}]}

    blueprint_md = generate_wasp_task_blueprint(
        title=title,
        details=details or "",
        priority=matched_priority,
        end_date=effective_end or "TBD",
        team_pod=team or "Engineering",
        complexity=matched_complexity or "⭐⭐⭐ 3 - Moderate",
        estimated_hours=estimated_hours or 0
    )

    icon = "⚡" if not parent_task_id else "🧩"
    new_page = client.create_page(
        parent_id=clean_id,
        title=title,
        content_markdown=blueprint_md,
        is_database_parent=True,
        icon_emoji=icon,
        properties=properties
    )
    return new_page
