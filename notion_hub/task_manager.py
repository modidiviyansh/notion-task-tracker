"""
Notion Task Manager Engine.
Implements the Native Notion Task Management Application:
- Complete Database Architecture with Formulas, Relations, and Rollups
- Standardized 5-Header Task Blueprint
- Priority & Aging Urgency Score Formula
- 7-Day, 15-Day, and Monthly Analytics & Velocity Metrics
- Previous Backlog Clearance Tracking
- Live KPI Dashboard Generation & Sync
"""
import sys
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from .client import NotionClient, NotionError

# Base Parent Page in Notion (To Do List workspace page)
DEFAULT_WORKSPACE_PAGE_ID = "2cbf1bcf-f9b8-8085-b20d-edffc13a913e"

PRIORITY_WEIGHTS = {
    "P1 - Urgent": 100,
    "P2 - High": 60,
    "P3 - Medium": 30,
    "P4 - Low": 10
}

TASK_SCHEMA = {
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
    "Assignee": {"people": {}},
    "Reviewer": {"people": {}},
    "Created By": {"created_by": {}},
    "Last Edited By": {"last_edited_by": {}},
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
    "Task Details": {"rich_text": {}},
    "Estimated Hours": {"number": {"format": "number"}},
    "Actual Hours": {"number": {"format": "number"}},
    "Original Backlog Item": {"checkbox": {}},
    "Created At": {"created_time": {}},
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


def generate_task_markdown_blueprint(
    title: str,
    details: str = "",
    priority: str = "P2 - High",
    due_date: str = "TBD",
    subtasks: Optional[List[str]] = None,
    estimated_hours: float = 0,
    actual_hours: float = 0
) -> str:
    """Build standardized 5-header blueprint markdown for task pages."""
    subtask_items = subtasks or [
        "Architect and review requirements",
        "Implement core solution",
        "Test and verify edge cases"
    ]
    subtask_md = "\n".join([f"- [ ] {st}" for st in subtask_items])

    return f"""# 📌 Task Overview & Details
> **Objective**: {details or f"Execute and deliver '{title}' with high standard."}

- **Definition of Done**:
  - [ ] Requirements fully met
  - [ ] Quality verified with zero regressions
  - [ ] Review completed and signed off

---

# ⚡ Urgency & Priority Metrics
- **Assigned Priority**: `{priority}`
- **Target Deadline**: `{due_date}`
- **Urgency Mechanism**: Priority Score dynamically escalates by `+3 pts/day` until completed, plus `+50 pts` if overdue.

---

# 👥 Team Collaboration & Action Routing
- **Primary Owner / Assignee**: *Assign above to take action*
- **Peer Reviewer**: *Assign reviewer when moving to In Review*
- **Action State**: Set `Action Required By` so the team knows who holds the ball.
- **Handoff Checklist**:
  - [ ] Implementation complete and self-tested
  - [ ] PR / Spec linked in Notes below
  - [ ] Assigned to Reviewer for sign-off

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
- *Log design decisions, meeting minutes, technical links, and retrospective takeaways here.*
"""


def setup_notion_task_manager(
    client: NotionClient,
    parent_page_id: str = DEFAULT_WORKSPACE_PAGE_ID
) -> Dict[str, Any]:
    """
    Creates the complete Native Notion Task Commander:
    1. Parent Hub Page
    2. Master Database with 17 properties, formulas & dual relations
    3. Realistic seed tasks demonstrating all features
    4. Executive Dashboard markdown on the Hub Page
    """
    print(f"🚀 Initializing Notion Task Commander under parent page: {parent_page_id}...")

    # 1. Create Hub Page
    hub_page = client.create_page(
        parent_id=parent_page_id,
        title="🎯 Task Commander — Notion Task Manager",
        content_markdown="# 🎯 Initializing Task Commander System...\n*Setting up database engine...*",
        icon_emoji="🎯"
    )
    hub_page_id = hub_page["id"]
    print(f"✅ Created Hub Page: {hub_page_id}")

    # 2. Create Master Database under the Hub Page
    db = client.create_database(
        parent_page_id=hub_page_id,
        title="📋 Central Task Engine",
        properties_schema=TASK_SCHEMA,
        icon_emoji="⚡"
    )
    db_id = db["id"]
    clean_db_id = db_id.replace("-", "")
    print(f"✅ Created Master Database: {clean_db_id}")

    # 3. Add Dual Self-Relation for Parent Task <-> Subtasks
    print("🔗 Configuring Sub-items Dual Self-Relation (Parent Task <-> Subtasks)...")
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
    print("✅ Subtask hierarchy dual relation linked!")

    # 4. Populate Realistic Seed Tasks
    print("🌱 Populating Seed Tasks & Metrics Demonstration...")
    seed_records = _create_seed_tasks(client, clean_db_id)
    print(f"✅ Created {len(seed_records)} demonstration tasks across all states!")

    # 5. Calculate Initial Analytics
    analytics = calculate_task_analytics(client, clean_db_id)

    # 6. Build Rich Executive Hub Page Dashboard Content
    dashboard_md = _build_hub_dashboard_markdown(db_id, analytics)

    # Append dashboard content to Hub Page
    print("🎨 Formatting Executive Dashboard on Notion Hub Page...")
    client.append_markdown(hub_page_id, dashboard_md)
    print("✅ Dashboard published!")

    return {
        "hub_page_id": hub_page_id,
        "database_id": db_id,
        "hub_url": hub_page.get("url", f"https://notion.so/{hub_page_id.replace('-', '')}"),
        "analytics": analytics
    }


def _create_seed_tasks(client: NotionClient, database_id: str) -> List[Dict[str, Any]]:
    """Seed tasks demonstrating all priorities, completion timeframes, and subtask relations."""
    now = datetime.now(timezone.utc)
    d_7_ago = (now - timedelta(days=5)).strftime("%Y-%m-%d")
    d_12_ago = (now - timedelta(days=12)).strftime("%Y-%m-%d")
    d_25_ago = (now - timedelta(days=25)).strftime("%Y-%m-%d")
    d_tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    d_next_week = (now + timedelta(days=7)).strftime("%Y-%m-%d")
    d_overdue = (now - timedelta(days=2)).strftime("%Y-%m-%d")

    records = []

    # 1. Parent Task (Epic) with Subtasks
    epic_md = generate_task_markdown_blueprint(
        title="Deploy Notion Task Commander v1.0",
        details="Full delivery of Native Notion Task Manager with formulas, forms, and dashboard.",
        priority="P1 - Urgent",
        due_date=d_tomorrow,
        subtasks=[
            "Configure 17-property database schema with formulas",
            "Build 5-header standardized task template blueprint",
            "Implement 7-day, 15-day, and monthly analytics engine",
            "Set up intake form view and quick CLI capture"
        ],
        estimated_hours=16,
        actual_hours=12
    )
    epic = client.create_page(
        parent_id=database_id,
        title="Deploy Notion Task Commander v1.0",
        content_markdown=epic_md,
        is_database_parent=True,
        icon_emoji="🚀",
        properties={
            "Task Name": {"title": [{"text": {"content": "Deploy Notion Task Commander v1.0"}}]},
            "Status": {"status": {"name": "In Progress"}},
            "Priority": {"select": {"name": "P1 - Urgent"}},
            "Due Date": {"date": {"start": d_tomorrow}},
            "Category": {"select": {"name": "🚀 Product & Feature"}},
            "Eisenhower Matrix": {"select": {"name": "Q1: Do First (Urgent & Important)"}},
            "Task Details": {"rich_text": [{"text": {"content": "Comprehensive launch of the Native Notion Task Commander suite."}}]},
            "Estimated Hours": {"number": 16},
            "Actual Hours": {"number": 12},
            "Original Backlog Item": {"checkbox": False}
        }
    )
    epic_id = epic["id"]
    records.append(epic)

    # 2. Subtask 1 (Linked to Epic, marked Done)
    sub1_md = generate_task_markdown_blueprint(
        title="Subtask: Database Schema & Formula Engine",
        details="Establish formulas for Days Elapsed and Priority Score calculation.",
        priority="P2 - High",
        due_date=d_7_ago,
        estimated_hours=4,
        actual_hours=4
    )
    sub1 = client.create_page(
        parent_id=database_id,
        title="Subtask: Database Schema & Formula Engine",
        content_markdown=sub1_md,
        is_database_parent=True,
        icon_emoji="🧩",
        properties={
            "Task Name": {"title": [{"text": {"content": "Subtask: Database Schema & Formula Engine"}}]},
            "Status": {"status": {"name": "Done"}},
            "Priority": {"select": {"name": "P2 - High"}},
            "Due Date": {"date": {"start": d_7_ago}},
            "Completed At": {"date": {"start": d_7_ago}},
            "Category": {"select": {"name": "🛠️ Engineering & Tech"}},
            "Eisenhower Matrix": {"select": {"name": "Q1: Do First (Urgent & Important)"}},
            "Task Details": {"rich_text": [{"text": {"content": "Implemented Formula 2.0 Priority Score calculation and dual relation."}}]},
            "Estimated Hours": {"number": 4},
            "Actual Hours": {"number": 4},
            "Original Backlog Item": {"checkbox": False},
            "Parent Task": {"relation": [{"id": epic_id}]}
        }
    )
    records.append(sub1)

    # 3. Subtask 2 (Linked to Epic, In Progress)
    sub2 = client.create_page(
        parent_id=database_id,
        title="Subtask: Intake Form & 5-Header Blueprint",
        content_markdown=generate_task_markdown_blueprint(
            title="Subtask: Intake Form & 5-Header Blueprint",
            details="Standardized page template with 5 structured headers.",
            priority="P2 - High",
            due_date=d_tomorrow,
            estimated_hours=5,
            actual_hours=3
        ),
        is_database_parent=True,
        icon_emoji="📝",
        properties={
            "Task Name": {"title": [{"text": {"content": "Subtask: Intake Form & 5-Header Blueprint"}}]},
            "Status": {"status": {"name": "In Progress"}},
            "Priority": {"select": {"name": "P2 - High"}},
            "Due Date": {"date": {"start": d_tomorrow}},
            "Category": {"select": {"name": "🎨 UI / UX Design"}},
            "Eisenhower Matrix": {"select": {"name": "Q1: Do First (Urgent & Important)"}},
            "Estimated Hours": {"number": 5},
            "Actual Hours": {"number": 3},
            "Original Backlog Item": {"checkbox": False},
            "Parent Task": {"relation": [{"id": epic_id}]}
        }
    )
    records.append(sub2)

    # 4. Critical Overdue Task (Demonstrates Score Escalation & Overdue Penalty)
    overdue = client.create_page(
        parent_id=database_id,
        title="Resolve Production Database Connection Pooling",
        content_markdown=generate_task_markdown_blueprint(
            title="Resolve Production Database Connection Pooling",
            details="High concurrency connection spikes causing latency.",
            priority="P1 - Urgent",
            due_date=d_overdue,
            estimated_hours=6,
            actual_hours=2
        ),
        is_database_parent=True,
        icon_emoji="🔥",
        properties={
            "Task Name": {"title": [{"text": {"content": "Resolve Production Database Connection Pooling"}}]},
            "Status": {"status": {"name": "In Progress"}},
            "Priority": {"select": {"name": "P1 - Urgent"}},
            "Due Date": {"date": {"start": d_overdue}},
            "Category": {"select": {"name": "🛠️ Engineering & Tech"}},
            "Eisenhower Matrix": {"select": {"name": "Q1: Do First (Urgent & Important)"}},
            "Task Details": {"rich_text": [{"text": {"content": "Connection pool timeout during traffic surges."}}]},
            "Estimated Hours": {"number": 6},
            "Actual Hours": {"number": 2},
            "Original Backlog Item": {"checkbox": False}
        }
    )
    records.append(overdue)

    # 5. Backlog Item Cleared (Demonstrates "Previous Backlog Completion")
    backlog_cleared = client.create_page(
        parent_id=database_id,
        title="Refactor Legacy Error Handling Middleware",
        content_markdown=generate_task_markdown_blueprint(
            title="Refactor Legacy Error Handling Middleware",
            details="Old backlog chore that was finally addressed and completed.",
            priority="P3 - Medium",
            due_date=d_7_ago,
            estimated_hours=8,
            actual_hours=6
        ),
        is_database_parent=True,
        icon_emoji="🧹",
        properties={
            "Task Name": {"title": [{"text": {"content": "Refactor Legacy Error Handling Middleware"}}]},
            "Status": {"status": {"name": "Done"}},
            "Priority": {"select": {"name": "P3 - Medium"}},
            "Due Date": {"date": {"start": d_7_ago}},
            "Completed At": {"date": {"start": d_7_ago}},
            "Category": {"select": {"name": "🛠️ Engineering & Tech"}},
            "Eisenhower Matrix": {"select": {"name": "Q2: Schedule (Important & Not Urgent)"}},
            "Task Details": {"rich_text": [{"text": {"content": "Legacy technical debt from Q1 cleared successfully."}}]},
            "Estimated Hours": {"number": 8},
            "Actual Hours": {"number": 6},
            "Original Backlog Item": {"checkbox": True}  # Conquered Backlog!
        }
    )
    records.append(backlog_cleared)

    # 6. Task Completed in 15-Day window
    task_15d = client.create_page(
        parent_id=database_id,
        title="Q3 Security Audit & Secret Key Rotation",
        content_markdown=generate_task_markdown_blueprint(
            title="Q3 Security Audit & Secret Key Rotation",
            details="Completed during mid-cycle operations window.",
            priority="P2 - High",
            due_date=d_12_ago,
            estimated_hours=5,
            actual_hours=5
        ),
        is_database_parent=True,
        icon_emoji="🛡️",
        properties={
            "Task Name": {"title": [{"text": {"content": "Q3 Security Audit & Secret Key Rotation"}}]},
            "Status": {"status": {"name": "Done"}},
            "Priority": {"select": {"name": "P2 - High"}},
            "Due Date": {"date": {"start": d_12_ago}},
            "Completed At": {"date": {"start": d_12_ago}},
            "Category": {"select": {"name": "⚙️ Operations & Chores"}},
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
        content_markdown=generate_task_markdown_blueprint(
            title="Design System Color & Typography Tokens v2",
            details="Monthly baseline improvement for UI styling.",
            priority="P3 - Medium",
            due_date=d_25_ago,
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
            "Completed At": {"date": {"start": d_25_ago}},
            "Category": {"select": {"name": "🎨 UI / UX Design"}},
            "Eisenhower Matrix": {"select": {"name": "Q2: Schedule (Important & Not Urgent)"}},
            "Estimated Hours": {"number": 10},
            "Actual Hours": {"number": 9},
            "Original Backlog Item": {"checkbox": True}  # Another backlog item cleared!
        }
    )
    records.append(task_monthly)

    # 8. Stale Backlog Item (Demonstrating Aging Backlog Queue)
    backlog_active = client.create_page(
        parent_id=database_id,
        title="Evaluate Vector Embeddings for Local Search",
        content_markdown=generate_task_markdown_blueprint(
            title="Evaluate Vector Embeddings for Local Search",
            details="Research spike resting in backlog for future cycle.",
            priority="P4 - Low",
            due_date=d_next_week,
            estimated_hours=12,
            actual_hours=0
        ),
        is_database_parent=True,
        icon_emoji="💡",
        properties={
            "Task Name": {"title": [{"text": {"content": "Evaluate Vector Embeddings for Local Search"}}]},
            "Status": {"status": {"name": "Backlog"}},
            "Priority": {"select": {"name": "P4 - Low"}},
            "Due Date": {"date": {"start": d_next_week}},
            "Category": {"select": {"name": "💡 Research & Strategy"}},
            "Eisenhower Matrix": {"select": {"name": "Q2: Schedule (Important & Not Urgent)"}},
            "Estimated Hours": {"number": 12},
            "Actual Hours": {"number": 0},
            "Original Backlog Item": {"checkbox": True}
        }
    )
    records.append(backlog_active)

    return records


def calculate_task_analytics(client: NotionClient, database_id: str) -> Dict[str, Any]:
    """
    Computes real-time task analytics:
    - 7-Day Velocity
    - 15-Day Velocity
    - Monthly Velocity
    - Completed Tasks Total
    - Previous Backlog Completion (in numbers)
    - Hotlist / Escalated Task Count
    - Effort Tracking (Estimated vs Actual)
    """
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

    for it in items:
        props = it.get("properties", {})

        # Status
        status_obj = props.get("Status", {}).get("status") or {}
        status = status_obj.get("name", "To Do")
        is_done = status in ("Done", "Archived")

        if is_done:
            completed_tasks += 1
        else:
            active_tasks += 1
            if status == "Backlog":
                backlog_active += 1

        # Priority
        pri_obj = (props.get("Priority") or {}).get("select") or {}
        pri_name = pri_obj.get("name")
        if pri_name in priority_dist:
            priority_dist[pri_name] += 1

        # Category
        cat_obj = (props.get("Category") or {}).get("select") or {}
        cat_name = cat_obj.get("name", "Uncategorized")
        category_dist[cat_name] = category_dist.get(cat_name, 0) + 1

        # Multi-user Team Pod & Action routing
        pod_obj = (props.get("Team / Pod") or {}).get("select") or {}
        pod_name = pod_obj.get("name")
        if pod_name:
            team_dist[pod_name] = team_dist.get(pod_name, 0) + 1

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

        # Estimated & Actual Hours
        est = props.get("Estimated Hours", {}).get("number") or 0
        act = props.get("Actual Hours", {}).get("number") or 0
        total_estimated_hours += est
        total_actual_hours += act

        # Backlog State inspection
        bstate_obj = props.get("Backlog State", {}).get("formula") or {}
        bstate = bstate_obj.get("string", "")

        is_orig_backlog = props.get("Original Backlog Item", {}).get("checkbox") is True
        if bstate == "🏆 Conquered Backlog Debt" or (is_done and is_orig_backlog):
            backlog_completed += 1
        elif bstate == "⚠️ Rolled-Over Backlog Debt":
            backlog_active += 1

        # Completed At parsing
        comp_date_obj = props.get("Completed At", {}).get("date")
        comp_str = comp_date_obj.get("start") if comp_date_obj else None

        if is_done and comp_str:
            try:
                # Handle dates like '2026-10-15' or ISO with timestamp
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

        # Priority-dominant score escalation inspection
        score_obj = props.get("Priority Score", {}).get("formula") or {}
        score = score_obj.get("number") or 0
        if not is_done and (score >= 250 or pri_name == "P1 - Urgent"):
            hotlist_urgent += 1

    completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0

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
        "team_distribution": team_dist
    }


def _build_hub_dashboard_markdown(database_id: str, a: Dict[str, Any]) -> str:
    """Formats the rich executive KPI dashboard for the Hub Page in Notion."""
    return f"""# 👑 Admin Executive Accountability Cockpit
> **Real-time Performance Cockpit** | Last calculated: `{a['timestamp']}`

---

## 📊 Executive KPI Scorecard Grid

| KPI Dimension | Value | Operational Context |
| :--- | :--- | :--- |
| ⚡ **7-Day Sprint Output** | **{a['completed_7d']} Tasks** | High-cadence sprint delivery |
| 🗓️ **15-Day Mid-Cycle Output** | **{a['completed_15d']} Tasks** | Bi-weekly milestone progress |
| 📈 **Monthly Throughput (30d)** | **{a['completed_monthly']} Tasks** | Strategic delivery pace |
| 🏆 **Previous Backlog Conquered** | **{a['backlog_cleared_count']} Debt Items** | Conquered technical & operational debt |
| ⚠️ **Rolled-Over Backlog Debt** | **{a['backlog_active_count']} Tasks** | Incomplete tasks from past End Dates |
| 🚨 **High Escalation Hotlist** | **{a['hotlist_urgent_count']} Active Alerts** | Tasks with Score >= 250 or P1 |
| 👥 **Team Workload Balance** | **{a['active_tasks'] - a['unassigned_count']} Assigned / {a['unassigned_count']} Open** | Resource allocation ratio |
| 👀 **In Peer Review** | **{a['in_review_count']} Tasks** | Waiting on reviewer sign-off |
| 🚧 **Blocked Action Items** | **{a['blocked_count']} Tasks** | Requiring unblocking / spec clarity |
| ⏱️ **Effort Planning Accuracy** | **{a['total_estimated_hours']}h est / {a['total_actual_hours']}h act** | Variance indicator |

---

## 📅 End Date & Automated Backlog Construction Engine
How the Backlog is dynamically constructed from task dates:

1. **🚀 Active Sprint Horizon**: Tasks with an active `End Date` in the current/upcoming cycle.
2. **📦 Unscheduled Backlog Pool**: Raw tasks without an `End Date` awaiting sprint planning.
3. **⚠️ Rolled-Over Backlog Debt**: Tasks whose `End Date` has passed and remain uncompleted.
4. **🏆 Conquered Backlog Debt**: When an old backlog or rolled-over debt item is completed, it automatically counts toward **Previous Backlog Conquered**!

---

## 🧮 Priority-Dominant Weightable Formula
Priority strictly commands the highest score, ensuring that critical tasks always take precedence:

$$\\text{{Priority Score}} = \\text{{Priority Base Weight}} + (\\text{{Days Elapsed}} \\times \\text{{Tier Rate}}) + \\text{{Overdue Penalty}}$$

- **Base Weights**: `P1 - Urgent` = **500 pts** (+10/day) | `P2 - High` = **250 pts** (+5/day) | `P3 - Medium` = **100 pts** (+2/day) | `P4 - Low` = **25 pts** (+0.5/day)
- **Overdue Penalty**: Adds `+100 pts` (P1), `+75 pts` (P2), `+50 pts` (P3), `+25 pts` (P4) if current date exceeds `End Date`.
- **Done State**: Drops immediately to `0 pts` upon reaching `Done` or `Archived`.
- **Escalation Badges**:
  - `🔥 CRITICAL OVERDUE`: Score $\\ge 500$ & Overdue
  - `🚨 HIGH URGENCY`: Score $\\ge 250$
  - `⚠️ ELEVATED`: Score $\\ge 100$
  - `🟢 STABLE`: Score $< 100$
  - `✅ RESOLVED`: Status is Done

---

## 👥 Multi-User Shared Action Engine & Collaboration Protocol
Designed for distributed teams to collaborate seamlessly:

1. 👤 **Personalized "My Tasks" Cockpit (`Assignee is @me`)**:
   - In Notion, set any view's filter to **`Assignee contains @me`**.
   - Notion dynamically filters the board to show only tasks assigned to whoever is currently logged in!
2. 🎯 **Grab-and-Go Open Queue (`Assignee is empty`)**:
   - Anyone who finishes their sprint deliverables early can view this pool and assign a task to themselves to take action immediately.
3. 👀 **Peer Review & Handoff Pipeline**:
   - When an engineer finishes implementation, they set `Status` $\\to$ **`In Review`** and choose a `Reviewer` (Person).
4. 🏢 **Team / Pod Workload Distribution**:
   - Categorize by `Frontend`, `Backend`, `DevOps & Infra`, `Design`, `Product`, or `QA & Security`.

---

## 🤖 Google Workspace & n8n Automation Ecosystem
This Notion Task Commander connects with pre-built **n8n workflows** located in `n8n_workflows/`:

- **💬 Google Chat Space Alerts**: Pings your team space with formatted interactive cards for P1 escalations and overdue tasks.
- **✉️ Google Workspace Email Briefings**: Sends weekly C-level digests to leadership every Friday.
- **📅 Automated Sunday Sprint Rollover**: Automatically identifies missed End Dates and rolls them into Backlog Debt for Monday sprint planning.

---

## 🧭 Curated Database Views Guide
Switch between these native views in the **📋 Central Task Engine** database:

1. 👑 **Admin Accountability Matrix (Grouped by Assignee $\\to$ Status)**:
   - Full team visibility into active work, bottlenecks, and throughput.
2. 🔥 **Escalation Hotlist (Sort: Priority Score Descending)**:
   - Evaluates real-time risk. Highest priority aged items appear at the very top.
3. 👤 **My Action Items (Filter: `Assignee is @me`)**:
   - Dynamic 1-click personal workbench for each logged-in team member.
4. 🎯 **Open Sprint Grab-and-Go (Filter: `Assignee is empty` & `Status != Done`)**:
   - Unassigned tasks ready to be claimed by available engineers.
5. 👀 **Peer Review Board (Filter: `Status is In Review`)**:
   - Dedicated handoff queue for code reviews and QA sign-offs.
6. 🗓️ **End Date Horizon Planner (Calendar & Timeline View)**:
   - Milestone calendar and sprint timeline view.
7. ⚡ **7-Day Sprint Horizon**:
   - Filter: `End Date is within next week` OR `Status is Done within 7 days`.
8. 🏢 **Team Pod Workload Board**:
   - Grouped by `Team / Pod`: Frontend ➡️ Backend ➡️ DevOps ➡️ Design ➡️ Product ➡️ QA.
9. 📥 **Backlog Cleared & Rolled-Over Queue**:
   - Filter: `Status is Backlog` | Sort: `Days Elapsed Descending` (Oldest first).
10. 🎯 **Eisenhower 4-Quadrant Board**:
    - Grouped by `Eisenhower Matrix`: Q1 (Do First), Q2 (Schedule), Q3 (Delegate), Q4 (Eliminate).
11. 🌳 **Parent & Subtask Hierarchy**:
    - Sub-items enabled via `Parent Task` <-> `Subtasks` dual relation.


---

## 🧮 Mathematical Priority Scoring Formula
Every task automatically computes its urgency score in real-time using Notion Formula 2.0:

```plain text
Priority Score = Base Weight + (Days Elapsed × 3) + Overdue Penalty
```
- **Base Weights**: `P1 - Urgent` = 100 | `P2 - High` = 60 | `P3 - Medium` = 30 | `P4 - Low` = 10
- **Aging Multiplier**: Each day the task remains active adds `+3 points` to its score.
- **Overdue Penalty**: Automatically adds `+50 points` if current date exceeds `Due Date`.
- **Done State**: Drops immediately to `0 points` upon reaching `Done` or `Archived`.

---

## 🛠️ CLI Companion Quick Reference
Run these commands anytime to manage and sync your Native Notion Task Manager:
```bash
# View live analytics & team collaboration metrics
python3 -m notion_hub.cli metrics --db {database_id}

# Refresh KPI scoreboard directly on Notion Hub Page
python3 -m notion_hub.cli sync-metrics --hub {database_id}

# Fast raise a new task with 5-header blueprint
python3 -m notion_hub.cli raise-task --db {database_id} --title "Fix Security Bug" --priority "P1 - Urgent" --end-date "2026-10-25"
```
"""


def raise_new_task(
    client: NotionClient,
    database_id: str,
    title: str,
    priority: str = "P2 - High",
    due_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    details: Optional[str] = None,
    estimated_hours: Optional[float] = None,
    eisenhower: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    is_backlog: bool = False,
    team: Optional[str] = None,
    action_required_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Raises a new task in the Notion database with:
    - Standardized 5-header blueprint content
    - Automatic Priority & Score calculation
    - End Date and Backlog Construction
    - Team Pod and Action routing
    - Optional Subtask linking
    """
    clean_id = database_id.replace("-", "")

    # Standardize category
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

    # Standardize priority
    valid_priorities = ["P1 - Urgent", "P2 - High", "P3 - Medium", "P4 - Low"]
    matched_priority = "P2 - High"
    p_upper = priority.strip().upper()
    for vp in valid_priorities:
        if p_upper == vp.upper() or p_upper in vp.upper() or vp.upper().startswith(p_upper):
            matched_priority = vp
            break

    # Build properties
    properties: Dict[str, Any] = {
        "Task Name": {"title": [{"text": {"content": title}}]},
        "Status": {"status": {"name": "Backlog" if is_backlog else "To Do"}},
        "Priority": {"select": {"name": matched_priority}},
        "Category": {"select": {"name": matched_category}},
        "Original Backlog Item": {"checkbox": is_backlog}
    }

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

    # Generate 5-header blueprint markdown
    blueprint_md = generate_task_markdown_blueprint(
        title=title,
        details=details or "",
        priority=matched_priority,
        due_date=due_date or "TBD",
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
