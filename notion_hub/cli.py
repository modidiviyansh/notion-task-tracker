"""
Command Line Interface for Notion Hub.
Allows Antigravity and the developer to interact with Notion seamlessly.
"""
import sys
import argparse
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from .client import NotionClient, NotionError
from .wasp_engine import (
    DEFAULT_WORKSPACE_PAGE_ID,
    setup_wasp_dashboard,
    calculate_wasp_analytics,
    raise_wasp_task,
    _build_wasp_dashboard_markdown
)
from .personal_engine import (
    calculate_wasp_personal_metrics,
    sync_wasp_personal_scoreboard,
    compute_accountability_matrix,
    generate_accountability_matrix_markdown,
    sync_accountability_matrix_to_notion
)

def get_client() -> NotionClient:
    try:
        return NotionClient()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_whoami(args):
    client = get_client()
    info = client.get_me()
    bot = info.get("bot", {})
    owner = bot.get("owner", {}).get("user", {})
    print(f"✅ Authenticated as: {info.get('name', 'Bot')}")
    print(f"🏠 Workspace: {bot.get('workspace_name', 'Unknown')} (ID: {bot.get('workspace_id', '')})")
    print(f"👤 Owner: {owner.get('name', 'Unknown')} <{owner.get('person', {}).get('email', '')}>")

def cmd_search(args):
    client = get_client()
    results = client.search(query=args.query or "", filter_type=args.type)
    print(f"Found {len(results)} items matching '{args.query or ''}':\n")
    for r in results:
        obj_type = r.get("object")
        item_id = r.get("id")
        title = ""
        if obj_type == "database":
            title = "".join(t.get("plain_text", "") for t in r.get("title", []))
            print(f"📁 [Database] {title or 'Untitled'} (ID: {item_id})")
        else:
            props = r.get("properties", {})
            for k, v in props.items():
                if v.get("type") == "title":
                    title = "".join(t.get("plain_text", "") for t in v.get("title", []))
                    break
            parent = r.get("parent", {}).get("type", "unknown")
            print(f"📄 [Page] {title or 'Untitled'} (Parent: {parent}, ID: {item_id})")

def cmd_list_dbs(args):
    client = get_client()
    dbs = client.list_databases()
    print(f"Accessible Databases ({len(dbs)}):\n")
    for db in dbs:
        title = "".join(t.get("plain_text", "") for t in db.get("title", []))
        props = list(db.get("properties", {}).keys())
        print(f"• {title or 'Untitled'}")
        print(f"  ID: {db.get('id')}")
        print(f"  Properties: {', '.join(props)}")
        print()

def cmd_list_pages(args):
    client = get_client()
    pages = client.list_pages()
    print(f"Accessible Pages ({len(pages)}):\n")
    for p in pages:
        props = p.get("properties", {})
        title = ""
        for k, v in props.items():
            if v.get("type") == "title":
                title = "".join(t.get("plain_text", "") for t in v.get("title", []))
                break
        parent_type = p.get("parent", {}).get("type", "")
        print(f"• {title or 'Untitled'} (ID: {p.get('id')}, Parent: {parent_type})")

def cmd_read(args):
    client = get_client()
    page = client.get_page(args.page_id)
    props = page.get("properties", {})
    title = ""
    for k, v in props.items():
        if v.get("type") == "title":
            title = "".join(t.get("plain_text", "") for t in v.get("title", []))
            break
    print(f"# {title or 'Untitled'}\n")
    md = client.get_page_markdown(args.page_id)
    print(md)

def cmd_query_db(args):
    client = get_client()
    items = client.query_database(args.database_id)
    print(f"Found {len(items)} items in database:\n")
    for it in items:
        props = it.get("properties", {})
        title = ""
        done = False
        status = ""
        due = ""
        for k, v in props.items():
            ptype = v.get("type")
            if ptype == "title":
                title = "".join(t.get("plain_text", "") for t in v.get("title", []))
            elif ptype == "checkbox":
                done = v.get("checkbox", False)
            elif ptype == "select" and v.get("select"):
                status = v["select"].get("name", "")
            elif ptype == "date" and v.get("date"):
                due = v["date"].get("start", "")
        mark = "[x]" if done else "[ ]"
        details = []
        if status:
            details.append(f"Status: {status}")
        if due:
            details.append(f"Due: {due}")
        detail_str = f" ({', '.join(details)})" if details else ""
        print(f"{mark} {title or 'Untitled'} - ID: {it.get('id')}{detail_str}")

def cmd_create_task(args):
    client = get_client()
    res = client.create_task(
        database_id=args.db,
        title=args.title,
        done=args.done,
        due_date=args.due,
        notes=args.notes
    )
    print(f"✅ Created task: '{args.title}' (ID: {res.get('id')})")
    print(f"🔗 URL: {res.get('url', '')}")

def cmd_update_task(args):
    client = get_client()
    done_val = None
    if args.done:
        done_val = True
    elif args.not_done:
        done_val = False

    res = client.update_task_status(
        page_id=args.task_id,
        done=done_val,
        status_name=args.status
    )
    print(f"✅ Updated task (ID: {res.get('id')})")

def cmd_create_doc(args):
    client = get_client()
    content = ""
    if args.file:
        content = Path(args.file).read_text(encoding="utf-8")
    elif args.content:
        content = args.content

    res = client.create_page(
        parent_id=args.parent,
        title=args.title,
        content_markdown=content,
        icon_emoji=args.icon or "📄"
    )
    print(f"✅ Created document: '{args.title}' (ID: {res.get('id')})")
    print(f"🔗 URL: {res.get('url', '')}")

def cmd_append(args):
    client = get_client()
    content = ""
    if args.file:
        content = Path(args.file).read_text(encoding="utf-8")
    elif args.content:
        content = args.content
    else:
        print("Error: either --file or --content is required", file=sys.stderr)
        sys.exit(1)

    res = client.append_markdown(args.page, content)
    print(f"✅ Appended {len(res)} block(s) to page {args.page}")

def cmd_init_hub(args):
    client = get_client()
    parent_id = args.parent
    project_name = args.name or "Project Hub"

    print(f"🚀 Initializing Notion Project Hub: '{project_name}' under parent {parent_id}...")

    # 1. Create main dashboard page
    dashboard_md = f"""# {project_name} - Collaboration Hub

Welcome to the central project hub for **{project_name}**!
Co-developed with Antigravity AI pair programmer.

## Quick Links
- **Task & Sprint Board**: Track active tasks, backlog, and milestones.
- **Architecture & Technical Specs**: Design docs, API schemas, and RFCs.
- **Milestones & Release Notes**: Changelogs and delivery updates.

---
> 🤖 **Antigravity Status**: Connected & ready to build!
"""
    hub_page = client.create_page(
        parent_id=parent_id,
        title=f"🚀 {project_name}",
        content_markdown=dashboard_md,
        icon_emoji="🚀"
    )
    hub_page_id = hub_page["id"]
    print(f"  ✓ Hub Page created: ID {hub_page_id} ({hub_page.get('url')})")

    # 2. Create Task & Sprint Board Database
    task_schema = {
        "Task": {"title": {}},
        "Status": {
            "select": {
                "options": [
                    {"name": "Backlog", "color": "gray"},
                    {"name": "Todo", "color": "yellow"},
                    {"name": "In Progress", "color": "blue"},
                    {"name": "Done", "color": "green"}
                ]
            }
        },
        "Priority": {
            "select": {
                "options": [
                    {"name": "P0 - Critical", "color": "red"},
                    {"name": "P1 - High", "color": "orange"},
                    {"name": "P2 - Medium", "color": "blue"},
                    {"name": "P3 - Low", "color": "gray"}
                ]
            }
        },
        "Due Date": {"date": {}},
        "Done": {"checkbox": {}}
    }
    task_db = client.create_database(
        parent_page_id=hub_page_id,
        title="Tasks & Sprints",
        properties_schema=task_schema,
        icon_emoji="🎯"
    )
    task_db_id = task_db["id"]
    print(f"  ✓ Task Database created: ID {task_db_id}")

    # Add starter tasks
    client.create_task(
        database_id=task_db_id,
        title="Project Initialization & Setup",
        done=True,
        notes="Repository and environment configured."
    )
    client.create_task(
        database_id=task_db_id,
        title="Architecture & Requirements Alignment",
        done=False,
        notes="Define core requirements and architecture specs."
    )

    # 3. Create Architecture & Tech Specs page
    arch_md = f"""# Architecture & Technical Specifications

Document technical decisions, API schemas, database designs, and system architecture.

## System Overview
- **Tech Stack**: Define core framework, libraries, and runtime.
- **Key Modules**: List high-level architecture components.

## Architecture Decision Records (ADRs)
- **ADR-001**: Initial Project Architecture & Tech Stack
"""
    arch_page = client.create_page(
        parent_id=hub_page_id,
        title="📐 Architecture & Specs",
        content_markdown=arch_md,
        icon_emoji="📐"
    )
    print(f"  ✓ Specs Page created: ID {arch_page['id']}")

    print("\n🎉 Project Hub successfully initialized in Notion!")
    print(f"🔗 Access your Hub here: {hub_page.get('url')}")

def _get_saved_db_id() -> Optional[str]:
    for cfg in [Path.cwd() / ".notion_wasp_config.json", Path.cwd() / ".notion_task_config.json"]:
        if cfg.exists():
            try:
                with open(cfg, "r") as f:
                    data = json.load(f)
                    val = data.get("database_id")
                    if val:
                        return val
            except Exception:
                pass
    return None

def _get_saved_hub_id() -> Optional[str]:
    for cfg in [Path.cwd() / ".notion_wasp_config.json", Path.cwd() / ".notion_task_config.json"]:
        if cfg.exists():
            try:
                with open(cfg, "r") as f:
                    data = json.load(f)
                    val = data.get("hub_page_id")
                    if val:
                        return val
            except Exception:
                pass
    return None

def cmd_wasp_setup(args):
    client = get_client()
    parent = args.parent or DEFAULT_WORKSPACE_PAGE_ID
    res = setup_wasp_dashboard(client, parent_page_id=parent)
    
    cfg_file = Path.cwd() / ".notion_wasp_config.json"
    cfg_data = {
        "hub_page_id": res["hub_page_id"],
        "database_id": res["database_id"],
        "hub_url": res["hub_url"]
    }
    with open(cfg_file, "w") as f:
        json.dump(cfg_data, f, indent=2)
    with open(Path.cwd() / ".notion_task_config.json", "w") as f:
        json.dump(cfg_data, f, indent=2)
    print(f"\n🐝 WASP Dashboard is LIVE!\n🔗 Open Notion Hub: {res['hub_url']}")
    print(f"📁 Local config saved to {cfg_file}")

cmd_setup_task_manager = cmd_wasp_setup

def cmd_wasp_raise(args):
    client = get_client()
    db_id = args.db or _get_saved_db_id()
    if not db_id:
        print("Error: No database ID provided. Specify --db or run wasp-setup first.", file=sys.stderr)
        sys.exit(1)
    
    task = raise_wasp_task(
        client=client,
        database_id=db_id,
        title=args.title,
        priority=args.priority or "P2 - High",
        due_date=args.due,
        end_date=args.end_date or args.due,
        complexity=getattr(args, 'complexity', None),
        category=args.category,
        details=args.details,
        estimated_hours=args.est_hours,
        eisenhower=args.eisenhower,
        parent_task_id=args.parent_task,
        is_backlog=args.backlog,
        team=args.team,
        action_required_by=args.action_by,
        profile_person_id=getattr(args, 'profile_person', None)
    )
    print(f"✅ WASP Work Item raised: {args.title} (ID: {task['id']})")
    print(f"🔗 Notion URL: {task.get('url')}")

cmd_raise_task = cmd_wasp_raise

def cmd_wasp_metrics(args):
    client = get_client()
    db_id = args.db or _get_saved_db_id()
    if not db_id:
        print("Error: No database ID provided. Specify --db or run wasp-setup first.", file=sys.stderr)
        sys.exit(1)
    
    a = calculate_wasp_analytics(client, db_id)
    print("\n" + "=" * 65)
    print("  🐝 WASP : WORK ANALYSIS SYSTEM & PROFILE DASHBOARD")
    print("=" * 65)
    print(f"  📅 As of: {a['timestamp']}")
    print(f"  📋 Total Tracked Work Items:  {a['total_tasks']}")
    print(f"  ⚡ In-Flight Active Work:     {a['active_tasks']}")
    print(f"  ✅ Completed Work:            {a['completed_tasks']} ({a['completion_rate_pct']}%)")
    print("-" * 65)
    print("  🚀 MULTI-HORIZON VELOCITY:")
    print(f"    •  7-Day Sprint Velocity:      {a['completed_7d']} Tasks")
    print(f"    • 15-Day Mid-Cycle Velocity:   {a['completed_15d']} Tasks")
    print(f"    • 30-Day Monthly Throughput:   {a['completed_monthly']} Tasks")
    print("-" * 65)
    print("  🏆 BACKLOG HEALTH & DEBT CLEARANCE:")
    print(f"    • 🏆 Conquered Backlog Debt:   {a['backlog_cleared_count']} Items Conquered")
    print(f"    • ⚠️ Rolled-Over Backlog Debt: {a['backlog_active_count']} Tasks (Missed End Date)")
    print(f"    • 🚨 Critical Escalation List: {a['hotlist_urgent_count']} Tasks (Score >= 250)")
    print("-" * 65)
    print("  ⭐ COMPLEXITY & SIZING FACTOR:")
    print(f"    • Average Complexity Rating:   {a.get('avg_complexity', 3.0)} / 5.0 ⭐")
    if a.get('complexity_distribution'):
        non_zero = {k: v for k, v in a['complexity_distribution'].items() if v > 0}
        if non_zero:
            print("    • Active Complexity Tiers:     " + ", ".join(f"{k}: {v}" for k, v in non_zero.items()))
    print("-" * 65)
    print("  👥 WORK ANALYSIS & PROFILE ALLOCATION:")
    assigned = a['active_tasks'] - a['unassigned_count']
    print(f"    • Assigned in Flight:          {assigned} Tasks")
    print(f"    • Unassigned Pool:             {a['unassigned_count']} Tasks")
    print(f"    • Awaiting Review:             {a['in_review_count']} Tasks")
    print(f"    • Blocked Action Items:        {a['blocked_count']} Tasks")
    print(f"    • Effort Variance (Est / Act): {a['total_estimated_hours']}h est / {a['total_actual_hours']}h act")
    if a.get('team_distribution'):
        print("    • Team Pod Allocation:         " + ", ".join(f"{k}: {v}" for k, v in a['team_distribution'].items()))
    print("=" * 65 + "\n")

cmd_metrics = cmd_wasp_metrics

def cmd_wasp_sync(args):
    client = get_client()
    db_id = args.db or _get_saved_db_id()
    hub_id = args.hub or _get_saved_hub_id()
    if not db_id or not hub_id:
        print("Error: Missing database or hub ID. Run wasp-setup first or pass --hub and --db.", file=sys.stderr)
        sys.exit(1)
    
    a = calculate_wasp_analytics(client, db_id)
    md = _build_wasp_dashboard_markdown(db_id, a)
    print(f"🧹 Clearing stale blocks on Notion Hub Page: {hub_id}...")
    client.clear_page_blocks(hub_id, keep_types=["child_database"])
    client.append_markdown(hub_id, md)
    print(f"✅ Refreshed WASP KPI Scoreboard pushed to Notion Hub Page: {hub_id}")

cmd_sync_metrics = cmd_wasp_sync

def cmd_personal_metrics(args):
    client = get_client()
    db_id = args.db or _get_saved_db_id()
    if not db_id:
        print("Error: Missing database ID. Run wasp-setup first or pass --db.", file=sys.stderr)
        sys.exit(1)
    
    m = calculate_wasp_personal_metrics(client, db_id)
    print("\n" + "=" * 65)
    print("🐝 WASP PERSONAL WORKBENCH & WORK ANALYSIS (MY NUMBERS)")
    print("=" * 65)
    print(f"🐝 WASP Performance Score    : {m['wasp_score']} / 100")
    print(f"⚡ Multi-Horizon Output (7d)  : {m['completed_7d']} Delivered")
    print(f"🗓️ Multi-Horizon Output (15d) : {m['completed_15d']} Delivered")
    print(f"📈 Multi-Horizon Output (30d) : {m['completed_30d']} Delivered")
    print(f"🧮 Priority-Dominant Weight   : {m['earned_priority_weight']} / {m['total_priority_weight']} Pts")
    print(f"🏆 Conquered Backlog Debt    : {m['conquered_backlog_debt']} Cleared")
    print(f"⚠️ Slipped Rollover Debt     : {m['active_rollover_debt']} Items")
    print(f"⭐ Sizing & Complexity Load   : {m['avg_complexity']} / 5.0 ⭐ ({m['total_complexity_sum']} pts)")
    print(f"🛡️ Active WIP Load (In Flight): {m['wip_load']} Tasks (Limit: ≤ 5)")
    print(f"🚨 Critical P1 Escalations    : {m['urgent_p1_active']} Active Items")
    print(f"👀 In Peer Review             : {m['in_review_count']} Tasks")
    print(f"📋 Upcoming In Queue          : {m['todo_count']} Tasks")
    print(f"⏳ Effort Sizing (Est / Act)  : {m['total_est_hours']}h est / {m['total_act_hours']}h act")
    print("=" * 65 + "\n")

def cmd_personal_sync(args):
    client = get_client()
    db_id = args.db or _get_saved_db_id()
    parent_id = args.parent or "3fff1bcf-f9b8-817f-8023-c5f897489080"
    if not db_id:
        print("Error: Missing database ID. Pass --db.", file=sys.stderr)
        sys.exit(1)
    
    print("🐝 Computing real-time WASP personal metrics...")
    metrics = calculate_wasp_personal_metrics(client, db_id)
    print(f"🎯 Current Score: {metrics['wasp_score']} / 100 | Total Tasks: {metrics['total_tasks']}")
    res = sync_wasp_personal_scoreboard(client, parent_id, db_id)
    print(f"✅ Successfully synced {res['cards_synced']} WASP KPI cards to Scoreboard Database: {res['scoreboard_url']}")

def cmd_gantt_sync(args):
    client = get_client()
    db_id = args.db or _get_saved_db_id()
    if not db_id:
        print("Error: Missing database ID. Pass --db.", file=sys.stderr)
        sys.exit(1)
    print(f"🗓️ Aligning personal task date ranges for Gantt Timeline in {db_id}...")
    pages = client.query_database(db_id, page_size=100)
    aligned = 0
    from datetime import datetime, timezone, timedelta
    for p in pages:
        props = p.get("properties", {})
        due_prop = props.get("Due Date", {}).get("date") or {}
        end_prop = props.get("End Date", {}).get("date") or {}
        start_val = due_prop.get("start")
        end_val = due_prop.get("end") or end_prop.get("start")

        if start_val and not end_val:
            try:
                d_end = datetime.strptime(start_val, "%Y-%m-%d")
                d_start = (d_end - timedelta(days=5)).strftime("%Y-%m-%d")
                pid = p["id"].replace("-", "")
                client._request("PATCH", f"/pages/{pid}", {
                    "properties": {
                        "Due Date": {"date": {"start": d_start, "end": start_val}},
                        "End Date": {"date": {"start": start_val}}
                    }
                })
                aligned += 1
            except Exception:
                pass
        elif not start_val and end_val:
            try:
                d_end = datetime.strptime(end_val, "%Y-%m-%d")
                d_start = (d_end - timedelta(days=5)).strftime("%Y-%m-%d")
                pid = p["id"].replace("-", "")
                client._request("PATCH", f"/pages/{pid}", {
                    "properties": {
                        "Due Date": {"date": {"start": d_start, "end": end_val}},
                        "End Date": {"date": {"start": end_val}}
                    }
                })
                aligned += 1
            except Exception:
                pass
    print(f"✅ Aligned {aligned} personal tasks with Gantt date ranges!")

def cmd_test_notifications(args):
    client = get_client()
    db_id = args.db or _get_saved_db_id()
    if not db_id:
        print("Error: Missing database ID. Pass --db.", file=sys.stderr)
        sys.exit(1)

    print(f"📡 Testing WASP Notification Engine against Database: {db_id}...\n")
    m = calculate_wasp_personal_metrics(client, db_id)

    print("=" * 65)
    print("🐝 GOOGLE CHAT CARD V2 PREVIEW (WASP DIGEST)")
    print("=" * 65)
    print("Header: 🐝 WASP Engine — Executive Accountability Digest")
    print(f"Subtitle: WASP Performance Score: {m['wasp_score']} / 100 Pts")
    print(f"Sections:")
    print(f"  • 7-Day Sprint Output: {m['completed_7d']} Tasks Delivered")
    print(f"  • 15-Day Mid-Cycle:    {m['completed_15d']} Tasks Delivered")
    print(f"  • Monthly Throughput:  {m['completed_30d']} Tasks Delivered")
    print(f"  • Priority Weight:     {m['earned_priority_weight']} / {m['total_priority_weight']} Pts Conquered")
    print(f"  • Conquered Debt:      {m['conquered_backlog_debt']} Cleared | Rollover: {m['active_rollover_debt']}")
    print(f"  • Work in Progress:    {m['wip_load']} Tasks In Flight (Optimal <= 5)")
    print(f"  • In Peer Review:      {m['in_review_count']} Tasks")
    print("Button: [OPEN WASP DASHBOARD]")
    print("=" * 65)
def cmd_accountability_matrix(args):
    client = get_client()
    db_id = args.db or _get_saved_db_id()
    if not db_id:
        print("Error: Missing database ID. Pass --db.", file=sys.stderr)
        sys.exit(1)

    page_id = args.page or "3fff1bcf-f9b8-817f-8023-c5f897489080"
    m = compute_accountability_matrix(client, db_id, assignee_filter=args.assignee)

    if getattr(args, "sync", False):
        print(f"🔄 Syncing visual Accountability Matrix to Notion page {page_id}...")
        res = sync_accountability_matrix_to_notion(client, page_id, db_id, assignee_filter=args.assignee)
        print(f"✅ Synced to Notion: {res['page_url']} ({res['blocks_appended']} blocks)")

    print("\n" + "=" * 78)
    print(f"📊 WASP ACCOUNTABILITY MATRIX & PERSONAL ANALYTICS (Filter: {m['assignee_filter']})")
    print("=" * 78)
    print(f"🎯 Validated Accountability Score : {m['accountability_score']} / 100 ({m['rating_label']})")
    print(f"⏱️ Total Effort Calibrated        : {m['total_est_minutes']} mins ({round(m['total_est_minutes'] / 60, 1)} hrs)")
    print(f"⚡ Average Deliverable Velocity   : {m['avg_minutes_per_task']} mins / task")
    print(f"🗓️ Sprint Delivery Horizon        : {m['sprint_days']} days")
    print(f"📈 7d / 15d / 30d Completed       : {m['completed_7d']} (7d) | {m['completed_15d']} (15d) | {m['completed_30d']} (30d)")
    print(f"📦 Total Active Backlog Load      : {m['total_backlog_count']} items ({m['total_backlog_weight']} weighted debt pts)")
    print("-" * 78)
    print("📋 TABULAR BACKLOG BY PRIORITY TIER:")
    print(f"  🔴 P1 - Urgent : {m['backlog_tiers']['P1 - Urgent']['count']:>2} tasks | 24h SLA     | {m['backlog_tiers']['P1 - Urgent']['count'] * 500:>4} pts | {', '.join(m['backlog_tiers']['P1 - Urgent']['tasks'][:2]) or 'None'}")
    print(f"  🟠 P2 - High   : {m['backlog_tiers']['P2 - High']['count']:>2} tasks | 48h SLA     | {m['backlog_tiers']['P2 - High']['count'] * 250:>4} pts | {', '.join(m['backlog_tiers']['P2 - High']['tasks'][:2]) or 'None'}")
    print(f"  🟡 P3 - Medium : {m['backlog_tiers']['P3 - Medium']['count']:>2} tasks | Sprint SLA  | {m['backlog_tiers']['P3 - Medium']['count'] * 100:>4} pts | {', '.join(m['backlog_tiers']['P3 - Medium']['tasks'][:2]) or 'None'}")
    print(f"  🔵 P4 - Low    : {m['backlog_tiers']['P4 - Low']['count']:>2} tasks | Backlog SLA | {m['backlog_tiers']['P4 - Low']['count'] * 25:>4} pts | {', '.join(m['backlog_tiers']['P4 - Low']['tasks'][:2]) or 'None'}")
    print(f"  ⚪ Raw Inbox   : {m['backlog_tiers']['Unset / Inbox']['count']:>2} tasks | Triage SLA  |    0 pts | {', '.join(m['backlog_tiers']['Unset / Inbox']['tasks'][:2]) or 'None'}")
    print(f"  🏆 TOTAL       : {m['total_backlog_count']:>2} tasks | Sprint Plan | {m['total_backlog_weight']:>4} pts")
    print("-" * 78)
    print("👥 ASSIGNEE ACCOUNTABILITY BREAKDOWN:")
    for a_name, a_data in m["assignee_summary"].items():
        print(f"  • {a_name:<16}: {a_data['score']:>3}/100 ({a_data['label']:<16}) | Total: {a_data['total']:>2} | Done: {a_data['done']:>2} | Flight: {a_data['in_progress']:>2} | Backlog: {a_data['backlog']:>2} | P1: {a_data['p1_urgent']:>2}")
    print("-" * 78)
    print("🚨 ACTIONABLE PRESCRIPTIONS (VALIDATED STEPS):")
    for p in m["prescriptions"]:
        print(f"  • {p}")
    print("=" * 78 + "\n")


def cmd_sync_analytics(args):
    from .sync_filtered_analytics import main as sync_main
    print("🚀 Running full sync of filtered tables, multi-horizon velocity, and charts...")
    sync_main()


def cmd_alert_p1(args):
    from .alerts import scan_and_dispatch_p1_alerts
    client = get_client()
    db_id = args.db or _get_saved_db_id()
    print("🔍 Scanning for active P1 - Urgent deliverables...")
    alerts = scan_and_dispatch_p1_alerts(client, db_id, webhook_url=args.webhook)
    if not alerts:
        print("✅ No sitting P1 - Urgent alerts detected. All critical SLAs healthy!")
    else:
        print(f"🚨 Dispatched {len(alerts)} P1 Urgent Alert(s):")
        for a in alerts:
            print(f"  • {a['task_title']} -> Status: {a['dispatch'].get('status')}")


def cmd_weekly_digest(args):
    from .alerts import build_weekly_digest_card, send_google_chat_webhook
    from .personal_engine import calculate_wasp_personal_metrics
    client = get_client()
    db_id = args.db or _get_saved_db_id()
    metrics = calculate_wasp_personal_metrics(client, db_id)
    hub_id = _get_saved_hub_id()
    hub_url = f"https://app.notion.com/{hub_id.replace('-', '')}" if hub_id else "https://app.notion.com"
    card = build_weekly_digest_card(metrics, hub_url)
    res = send_google_chat_webhook(card, webhook_url=args.webhook)
    print(f"📢 Weekly Executive Digest generated. Status: {res.get('status')}")
    if res.get("status") == "simulated":
        print("ℹ️ Set GOOGLE_CHAT_WEBHOOK_URL in .env to stream directly to a live Google Chat Space.")


def cmd_rollover_backlog(args):
    from .alerts import rollover_overdue_tasks_to_backlog
    client = get_client()
    db_id = args.db or _get_saved_db_id()
    print("🌙 Running Overdue Backlog Rollover Scan...")
    res = rollover_overdue_tasks_to_backlog(client, db_id, webhook_url=getattr(args, "webhook", None))
    count = res.get("overdue_count", 0)
    if count == 0:
        print("✅ No overdue tasks found. All deadlines healthy!")
    else:
        print(f"⚠️ Rolled over {count} overdue deliverable(s) into Backlog Debt:")
        for t in res.get("tasks", []):
            print(f"  • {t['title']} (Due: {t['due_date']} | Prev: {t['prev_status']}) ➔ Backlog")
        dispatch = res.get("dispatch", {})
        print(f"📢 Google Chat Dispatch: {dispatch.get('status')} ({dispatch.get('message', '')})")



def cmd_task_breakdown(args):
    from .task_breakdown import (
        parse_notes_into_subtasks,
        find_task_in_database,
        apply_user_decomposition_to_notion
    )
    client = get_client()
    db_id = args.db or _get_saved_db_id()
    identifier = args.task

    parent_task = find_task_in_database(client, db_id, identifier)
    if parent_task:
        parent_props = parent_task.get("properties", {})
        task_title = parent_props.get("Task Name", {}).get("title", [{}])[0].get("plain_text", identifier)
        print(f"📍 Selected deliverable in Notion: '{task_title}' (ID: {parent_task['id']})")
    else:
        task_title = identifier
        print(f"ℹ️ Deliverable '{identifier}' not found in database. Will create as new deliverable if --apply is set.")

    notes = getattr(args, "notes", None) or ""
    notes_file = getattr(args, "notes_file", None)
    if notes_file and Path(notes_file).exists():
        with open(notes_file, "r", encoding="utf-8") as f:
            notes = f.read()

    use_ai = getattr(args, "ai", False) or getattr(args, "gemini", False)
    if use_ai:
        from .task_breakdown import generate_breakdown_notes_with_gemini
        print(f"✨ Generating technical pillars & implementation notes with Google Gemini for: '{task_title}'...")
        gemini_key = getattr(args, "api_key", None)
        details_rich = parent_task.get("properties", {}).get("Task Details", {}).get("rich_text", []) if parent_task else []
        task_desc = notes or (details_rich[0].get("plain_text", "") if details_rich else "")
        notes = generate_breakdown_notes_with_gemini(task_title, task_desc, api_key=gemini_key)
        print("✓ Implementation plan & pillars drafted successfully!")

    if not notes.strip():
        details_rich = parent_task.get("properties", {}).get("Task Details", {}).get("rich_text", []) if parent_task else []
        notes = details_rich[0].get("plain_text", "") if details_rich else ""

    if not notes.strip():
        print("⚠️ No notes provided! Provide your implementation plan via --notes \"...\", --notes-file <PATH>, or pass --ai / --gemini to draft with Google Gemini.")
        return

    plan = parse_notes_into_subtasks(task_title, notes)

    print("\n" + "=" * 70)
    print(f"📝 DECOMPOSITION BLUEPRINT FOR: {task_title}")
    print("=" * 70)
    print(f"  • Calculated Sizing:   {plan['parent_complexity']} ({plan['total_hours']} total hours)")
    print(f"  • Subtasks Defined:    {len(plan['subtasks'])} items")
    print("\n📋 Decomposed Subtasks:")
    for idx, st in enumerate(plan["subtasks"], 1):
        print(f"  {idx}. [{st['pillar']}] {st['short_title']}")
        print(f"     ⏱️ {st['estimated_hours']} hrs | {st['complexity']} | Pod: {st['team']} | Priority: {st['priority']}")

    if getattr(args, "apply", False):
        print("\n🚀 Creating Subtasks in Notion & Linking to Parent Deliverable...")
        if not parent_task:
            clean_db_id = db_id.replace("-", "")
            parent_task = client._request("POST", "/pages", {
                "parent": {"database_id": clean_db_id},
                "properties": {
                    "Task Name": {"title": [{"text": {"content": task_title}}]},
                    "Status": {"status": {"name": "To Do"}},
                    "Priority": {"select": {"name": "P2 - High"}}
                },
                "icon": {"type": "emoji", "emoji": "🎯"}
            })
            print(f"  • Created parent deliverable in Notion: {task_title}")

        res = apply_user_decomposition_to_notion(client, db_id, parent_task, plan)
        print(f"\n✅ Subtasks Linked Successfully!")
        print(f"  • Parent Updated: {res['parent_title']} ➔ {res['parent_complexity']} ({res['total_hours']}h)")
        print(f"  • Created {res['subtasks_created']} subtasks with native Parent Task relation:")
        for sub in res["subtasks"]:
            print(f"    - {sub['title']} ➔ {sub['url']}")
    else:
        print("\n💡 Run with --apply to create and link these subtasks into Notion.")




def cmd_export_dashboard_data(args):
    from .export_dashboard import export_static_dashboard_data
    client = get_client()
    db_id = args.db or _get_saved_db_id()
    print("📦 Exporting live Notion metrics to docs/data.json for GitHub Pages...")
    out_path = export_static_dashboard_data(client, db_id)
    print(f"✅ Dashboard dataset successfully synced to: {out_path}")


def _add_task_raise_arguments(parser):
    parser.add_argument("--title", required=True, help="Task title")
    parser.add_argument("--db", help="Database ID (optional if configured)")
    parser.add_argument("--priority", default="P2 - High", choices=["P1 - Urgent", "P2 - High", "P3 - Medium", "P4 - Low", "P1", "P2", "P3", "P4"], help="Priority tier")
    parser.add_argument("--complexity", choices=["1", "2", "3", "4", "5", "trivial", "simple", "moderate", "complex", "epic"], help="Complexity rating (1 to 5)")
    parser.add_argument("--due", help="Due date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Target sprint end date / completion horizon (YYYY-MM-DD)")
    parser.add_argument("--team", choices=["Frontend", "Backend", "DevOps & Infra", "Design", "Product", "QA & Security"], help="Team / Functional Pod")
    parser.add_argument("--action-by", choices=["Assignee (In Flight)", "Reviewer (Code/Spec Review)", "Reporter (Clarification Needed)", "Blocked (Waiting on External)"], help="Action routing")
    parser.add_argument("--category", help="Category (Product, Engineering, Design, Growth, Ops, Research)")
    parser.add_argument("--details", help="High-level task details & context")
    parser.add_argument("--est-hours", type=float, help="Estimated effort in hours")
    parser.add_argument("--eisenhower", choices=[
        "Q1: Do First (Urgent & Important)",
        "Q2: Schedule (Important & Not Urgent)",
        "Q3: Delegate (Urgent & Not Important)",
        "Q4: Eliminate (Low Urgency & Low Impact)"
    ], help="Eisenhower Matrix quadrant")
    parser.add_argument("--parent-task", help="Parent Task Page ID if raising as a subtask")
    parser.add_argument("--profile-person", help="Page ID from People database to link profile accountability")
    parser.add_argument("--backlog", action="store_true", help="Raise directly into Backlog")

def main():
    parser = argparse.ArgumentParser(description="WASP Dashboard : Work Analysis System & Profile Dashboard")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # wasp-setup / setup-task-manager
    for cmd in ["wasp-setup", "setup-task-manager"]:
        p_setup = subparsers.add_parser(cmd, help="Initialize the Native Notion WASP Dashboard & Master Database")
        p_setup.add_argument("--parent", help="Parent Notion Page ID (defaults to To Do List workspace page)")
        p_setup.set_defaults(func=cmd_wasp_setup)

    # wasp-raise / raise-task
    for cmd in ["wasp-raise", "raise-task"]:
        p_raise = subparsers.add_parser(cmd, help="Raise a new work item with standardized 6-header blueprint & priority scoring")
        _add_task_raise_arguments(p_raise)
        p_raise.set_defaults(func=cmd_wasp_raise)

    # wasp-metrics / metrics
    for cmd in ["wasp-metrics", "metrics"]:
        p_met = subparsers.add_parser(cmd, help="Calculate live 7d, 15d, 30d velocity and conquered backlog metrics")
        p_met.add_argument("--db", help="Database ID (optional if configured)")
        p_met.set_defaults(func=cmd_wasp_metrics)

    # wasp-sync / sync-metrics
    for cmd in ["wasp-sync", "sync-metrics"]:
        p_sync = subparsers.add_parser(cmd, help="Refresh & push live KPI metrics directly onto Notion Hub Page")
        p_sync.add_argument("--hub", help="Hub Page ID (optional if configured)")
        p_sync.add_argument("--db", help="Database ID (optional if configured)")
        p_sync.set_defaults(func=cmd_wasp_sync)

    # personal-metrics / my-numbers
    for cmd in ["personal-metrics", "my-numbers"]:
        p_pm = subparsers.add_parser(cmd, help="Show personal score, KPI breakdown, and numbers")
        p_pm.add_argument("--db", help="Tasks Database ID (optional if configured)")
        p_pm.set_defaults(func=cmd_personal_metrics)

    # personal-sync / sync-scoreboard
    for cmd in ["personal-sync", "sync-scoreboard"]:
        p_ps = subparsers.add_parser(cmd, help="Sync personal KPI scoreboard cards into Notion")
        p_ps.add_argument("--db", help="Tasks Database ID (optional if configured)")
        p_ps.add_argument("--parent", help="Parent Page ID (defaults to Personal Dashboard or Hub page)")
        p_ps.set_defaults(func=cmd_personal_sync)

    # gantt-sync
    for cmd in ["gantt-sync", "sync-timeline"]:
        p_gs = subparsers.add_parser(cmd, help="Align tasks with cascading Start & End date ranges for Gantt Timeline")
        p_gs.add_argument("--db", help="Tasks Database ID (optional if configured)")
        p_gs.set_defaults(func=cmd_gantt_sync)

    # accountability-matrix
    for cmd in ["accountability-matrix", "accountability", "matrix", "matrix-sync"]:
        p_am = subparsers.add_parser(cmd, help="Show validated Matrix of Accountability and sync personal analytics")
        p_am.add_argument("--db", help="Tasks Database ID (optional if configured)")
        p_am.add_argument("--page", help="Page ID to sync onto (defaults to WASP Personal Dashboard)")
        p_am.add_argument("--assignee", help="Filter metrics by specific assignee name (e.g. karanveer, Diviyansh)")
        p_am.add_argument("--sync", "--push", action="store_true", help="Sync updated matrix directly to Notion page")
        p_am.set_defaults(func=cmd_accountability_matrix)

    # sync-analytics / sync-tables
    for cmd in ["sync-analytics", "sync-tables", "analytics-sync"]:
        p_sa = subparsers.add_parser(cmd, help="Sync filtered tables, multi-horizon velocity, and visual charts into Notion")
        p_sa.set_defaults(func=cmd_sync_analytics)

    # alert-p1
    p_ap1 = subparsers.add_parser("alert-p1", help="Scan for P1 Urgent SLA breaches and dispatch Google Chat alerts")
    p_ap1.add_argument("--db", help="Database ID")
    p_ap1.add_argument("--webhook", help="Google Chat Space Webhook URL")
    p_ap1.set_defaults(func=cmd_alert_p1)

    # weekly-digest
    p_wd = subparsers.add_parser("weekly-digest", help="Compile and dispatch weekly executive digest scorecard")
    p_wd.add_argument("--db", help="Database ID")
    p_wd.add_argument("--webhook", help="Google Chat Space Webhook URL")
    p_wd.set_defaults(func=cmd_weekly_digest)

    # breakdown / decompose
    for cmd in ["breakdown", "decompose", "task-breakdown"]:
        p_bd = subparsers.add_parser(cmd, help="Decompose deliverable into subtasks based on your implementation notes & major pillars")
        p_bd.add_argument("--task", required=True, help="Task title or ID to decompose")
        p_bd.add_argument("--notes", help="Implementation notes, major pillars, and subtask steps")
        p_bd.add_argument("--notes-file", help="Path to markdown/text file containing implementation notes")
        p_bd.add_argument("--ai", action="store_true", help="Draft implementation plan and pillars with Google Gemini AI")
        p_bd.add_argument("--gemini", action="store_true", help="Draft implementation plan and pillars with Google Gemini AI")
        p_bd.add_argument("--api-key", help="Google Gemini API key (defaults to GEMINI_API_KEY env var)")
        p_bd.add_argument("--db", help="Database ID")
        p_bd.add_argument("--apply", action="store_true", help="Create subtasks directly in Notion with Parent Task relation")
        p_bd.set_defaults(func=cmd_task_breakdown)

    # export-dashboard
    for cmd in ["export-dashboard", "export-data", "dashboard-export"]:
        p_ed = subparsers.add_parser(cmd, help="Export live Notion dataset to docs/data.json for GitHub Pages")
        p_ed.add_argument("--db", help="Database ID")
        p_ed.set_defaults(func=cmd_export_dashboard_data)

    # whoami
    subparsers.add_parser("whoami", help="Check current user & workspace")

    # search
    p_search = subparsers.add_parser("search", help="Search pages and databases")
    p_search.add_argument("query", nargs="?", default="", help="Search query")
    p_search.add_argument("--type", choices=["page", "database"], default=None, help="Filter by object type")
    p_search.set_defaults(func=cmd_search)

    # list-dbs
    p_list_dbs = subparsers.add_parser("list-dbs", help="List all accessible databases")
    p_list_dbs.set_defaults(func=cmd_list_dbs)

    # list-pages
    p_list_pages = subparsers.add_parser("list-pages", help="List all accessible pages")
    p_list_pages.set_defaults(func=cmd_list_pages)

    # read
    p_read = subparsers.add_parser("read", help="Read a page and output clean markdown")
    p_read.add_argument("page_id", help="Page ID to read")
    p_read.set_defaults(func=cmd_read)

    # query-db
    p_qdb = subparsers.add_parser("query-db", help="Query items in a database")
    p_qdb.add_argument("database_id", help="Database ID")
    p_qdb.set_defaults(func=cmd_query_db)

    # create-task
    p_ct = subparsers.add_parser("create-task", help="Create a task in a database")
    p_ct.add_argument("--db", required=True, help="Database ID")
    p_ct.add_argument("--title", required=True, help="Task title")
    p_ct.add_argument("--due", help="Due date (YYYY-MM-DD)")
    p_ct.add_argument("--done", action="store_true", help="Mark as completed")
    p_ct.add_argument("--notes", help="Detailed notes or description")
    p_ct.set_defaults(func=cmd_create_task)

    # update-task
    p_ut = subparsers.add_parser("update-task", help="Update task completion or status")
    p_ut.add_argument("task_id", help="Task Page ID")
    p_ut.add_argument("--done", action="store_true", help="Mark task as done")
    p_ut.add_argument("--not-done", action="store_true", help="Mark task as not done")
    p_ut.add_argument("--status", help="Status select name")
    p_ut.set_defaults(func=cmd_update_task)

    # create-doc
    p_cd = subparsers.add_parser("create-doc", help="Create a rich document/page")
    p_cd.add_argument("--parent", required=True, help="Parent Page ID")
    p_cd.add_argument("--title", required=True, help="Document title")
    p_cd.add_argument("--file", help="Path to markdown file")
    p_cd.add_argument("--content", help="Markdown string")
    p_cd.add_argument("--icon", help="Emoji icon")
    p_cd.set_defaults(func=cmd_create_doc)

    # append
    p_app = subparsers.add_parser("append", help="Append content to a page")
    p_app.add_argument("--page", required=True, help="Page ID")
    p_app.add_argument("--file", help="Path to markdown file")
    p_app.add_argument("--content", help="Markdown string")
    p_app.set_defaults(func=cmd_append)

    # init-hub
    p_init = subparsers.add_parser("init-hub", help="Initialize a full project collaboration hub in Notion")
    p_init.add_argument("--parent", required=True, help="Parent Page ID")
    p_init.add_argument("--name", default="Project Hub", help="Project name")
    p_init.set_defaults(func=cmd_init_hub)

    # rollover-backlog
    p_ro = subparsers.add_parser("rollover-backlog", help="Scan overdue tasks, move to Backlog and ping Google Chat")
    p_ro.add_argument("--db", help="Notion Database ID")
    p_ro.add_argument("--webhook", help="Google Chat Webhook URL")
    p_ro.set_defaults(func=cmd_rollover_backlog)


    args = parser.parse_args()
    if hasattr(args, "func"):
        try:
            args.func(args)
        except NotionError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
    elif args.subcommand == "whoami":
        cmd_whoami(args)

if __name__ == "__main__":
    main()
