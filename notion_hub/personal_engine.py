"""
WASP Personal Dashboard Engine: Work Analysis System & Profile Dashboard.
Strictly relative to the WASP Engine architecture:
- Priority-Dominant Weightable Formula (P1: 500, P2: 250, P3: 100, P4: 25)
- Multi-Horizon Velocity Tracking (7-day sprint, 15-day mid-cycle, 30-day monthly throughput)
- Backlog Slipped Debt vs Conquered Debt tracking
- Complexity factor rating (1 to 5 stars)
- Profile Accountability & WIP Capacity limits
- Visual Progress Ring & Bar Chart metrics in Notion
"""
import sys
import json
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from .client import NotionClient, NotionError

DIVIYANSH_USER_ID = "2cbd872b-594c-81cb-8330-00028fbf1dd5"

PRIORITY_WEIGHTS = {
    "P1 - Urgent": 500,
    "P2 - High": 250,
    "P3 - Medium": 100,
    "P4 - Low": 25
}

KPI_SCOREBOARD_SCHEMA = {
    "Metric": {"title": {}},
    "Current Value": {"rich_text": {}},
    "Health & Status": {
        "select": {
            "options": [
                {"name": "🟢 Elite Performance", "color": "green"},
                {"name": "🟢 On Track", "color": "green"},
                {"name": "🔵 Clean Horizon", "color": "blue"},
                {"name": "🟡 Approaching WIP Limit", "color": "yellow"},
                {"name": "🚨 Urgent SLA Escalation", "color": "red"}
            ]
        }
    },
    "Benchmark / Target": {"rich_text": {}},
    "Category": {
        "select": {
            "options": [
                {"name": "🐝 WASP Index", "color": "purple"},
                {"name": "⚡ Work Analysis", "color": "blue"},
                {"name": "🧮 Formula Engine", "color": "yellow"},
                {"name": "🏆 Backlog Analytics", "color": "green"},
                {"name": "👤 Profile Accountability", "color": "orange"}
            ]
        }
    },
    "Progress Value": {"number": {"format": "percent"}},
    "WASP Analytics Detail": {"rich_text": {}}
}

def calculate_wasp_personal_metrics(
    client: NotionClient,
    tasks_database_id: str,
    user_id: str = DIVIYANSH_USER_ID
) -> Dict[str, Any]:
    """
    Computes pure WASP Engine personal metrics from the real tasks in the database.
    Gracefully handles zero-task initial states as well as active workloads.
    """
    clean_id = tasks_database_id.replace("-", "")
    items = client.query_database(clean_id, page_size=100)

    now = datetime.now(timezone.utc)
    t_7d = now - timedelta(days=7)
    t_15d = now - timedelta(days=15)
    t_30d = now - timedelta(days=30)

    # Filter to personal tasks (assigned to user or all if single user workspace)
    personal_items = []
    for it in items:
        props = it.get("properties", {})
        assignees = (props.get("Assignee") or {}).get("people", [])
        assignee_ids = [a.get("id") for a in assignees]
        if user_id in assignee_ids or not assignees:
            personal_items.append(it)

    if not personal_items and items:
        personal_items = items

    total_tasks = len(personal_items)
    done_count = 0
    in_progress_count = 0
    in_review_count = 0
    todo_count = 0
    backlog_count = 0

    completed_7d = 0
    completed_15d = 0
    completed_30d = 0

    conquered_backlog_debt = 0
    active_rollover_debt = 0
    urgent_p1_active = 0

    total_complexity_sum = 0
    complexity_rated_count = 0

    total_est_hours = 0.0
    total_act_hours = 0.0

    earned_priority_weight = 0
    total_priority_weight = 0

    for it in personal_items:
        props = it.get("properties", {})

        status = ((props.get("Status") or {}).get("status") or {}).get("name", "To Do")
        priority = ((props.get("Priority") or {}).get("select") or {}).get("name", "P3 - Medium")
        comp_name = ((props.get("Complexity") or {}).get("select") or {}).get("name", "")

        est = (props.get("Estimated Hours") or {}).get("number") or 0
        act = (props.get("Actual Hours") or {}).get("number") or 0
        total_est_hours += est
        total_act_hours += act

        # Complexity sizing
        m = re.search(r"(\d)", comp_name)
        stars = int(m.group(1)) if m else 3
        total_complexity_sum += stars
        complexity_rated_count += 1

        # Priority weight
        p_weight = PRIORITY_WEIGHTS.get(priority, 100)
        item_weight = p_weight * stars
        total_priority_weight += item_weight

        is_done = status in ("Done", "Archived")

        if is_done:
            done_count += 1
            earned_priority_weight += item_weight

            # Check completion timestamp for multi-horizon velocity
            comp_obj = (props.get("Completed At") or {}).get("date")
            comp_str = comp_obj.get("start") if comp_obj else None
            if comp_str:
                try:
                    dt = datetime.fromisoformat(comp_str.replace("Z", "+00:00")) if "T" in comp_str else datetime.strptime(comp_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if dt >= t_7d: completed_7d += 1
                    if dt >= t_15d: completed_15d += 1
                    if dt >= t_30d: completed_30d += 1
                except Exception:
                    completed_7d += 1
            else:
                completed_7d += 1
                completed_15d += 1
                completed_30d += 1

            if (props.get("Original Backlog Item") or {}).get("checkbox") is True:
                conquered_backlog_debt += 1
        elif status == "In Progress":
            in_progress_count += 1
            if priority == "P1 - Urgent":
                urgent_p1_active += 1
        elif status == "In Review":
            in_review_count += 1
        elif status == "Backlog":
            backlog_count += 1
            active_rollover_debt += 1
        else:
            todo_count += 1
            if priority == "P1 - Urgent":
                urgent_p1_active += 1

            # End date rollover check
            end_obj = (props.get("End Date") or {}).get("date")
            end_str = end_obj.get("start") if end_obj else None
            if end_str:
                try:
                    dt_end = datetime.strptime(end_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if dt_end < now:
                        active_rollover_debt += 1
                except Exception:
                    pass

    # WASP Performance Index (0-100)
    if total_tasks == 0:
        wasp_score = 100
        completion_pct = 100.0
        avg_complexity = 0.0
        wip_load = 0
    else:
        completion_ratio = done_count / total_tasks
        completion_pct = round(completion_ratio * 100, 1)
        weight_ratio = (earned_priority_weight / total_priority_weight) if total_priority_weight > 0 else 1.0
        wip_load = in_progress_count
        wip_penalty = max(0, (wip_load - 5) * 5)
        base = int(weight_ratio * 65 + completion_ratio * 35 - wip_penalty)
        wasp_score = min(100, max(50, base))
        avg_complexity = round(total_complexity_sum / complexity_rated_count, 1) if complexity_rated_count > 0 else 3.0

    return {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "user_id": user_id,
        "total_tasks": total_tasks,
        "wasp_score": wasp_score,
        "done_count": done_count,
        "in_progress_count": in_progress_count,
        "in_review_count": in_review_count,
        "todo_count": todo_count,
        "backlog_count": backlog_count,
        "wip_load": in_progress_count,
        "completed_7d": completed_7d,
        "completed_15d": completed_15d,
        "completed_30d": completed_30d,
        "conquered_backlog_debt": conquered_backlog_debt,
        "active_rollover_debt": active_rollover_debt,
        "urgent_p1_active": urgent_p1_active,
        "avg_complexity": avg_complexity,
        "total_complexity_sum": total_complexity_sum,
        "earned_priority_weight": earned_priority_weight,
        "total_priority_weight": total_priority_weight,
        "completion_pct": completion_pct,
        "total_est_hours": total_est_hours,
        "total_act_hours": total_act_hours
    }


def sync_wasp_personal_scoreboard(
    client: NotionClient,
    parent_page_id: str,
    tasks_database_id: str,
    scoreboard_db_id: Optional[str] = "3fff1bcff9b8818291f3c96e8ab12275"
) -> Dict[str, Any]:
    """
    Computes live WASP metrics and updates the 6 visual KPI metric cards
    in the WASP Personal Scoreboard database.
    """
    metrics = calculate_wasp_personal_metrics(client, tasks_database_id)

    # 6 Core WASP Engine Metric Cards
    wasp_cards = [
        {
            "name": "🐝 WASP Personal Performance Index",
            "icon": "🐝",
            "value": f"{metrics['wasp_score']} / 100 Pts" if metrics['total_tasks'] > 0 else "100 / 100 (Ready State)",
            "status": "🟢 Elite Performance" if metrics["wasp_score"] >= 85 else ("🟢 On Track" if metrics["wasp_score"] >= 70 else "🟡 Approaching WIP Limit"),
            "target": "Target: > 85 pts (Priority & Complexity Calibrated)",
            "category": "🐝 WASP Index",
            "progress": metrics["wasp_score"] / 100.0,
            "detail": f"Earned {metrics['earned_priority_weight']} / {metrics['total_priority_weight']} weighted pts" if metrics['total_tasks'] > 0 else "Clean slate ready for your personal sprint items"
        },
        {
            "name": "⚡ WASP Multi-Horizon Velocity",
            "icon": "⚡",
            "value": f"7d: {metrics['completed_7d']} | 15d: {metrics['completed_15d']} | 30d: {metrics['completed_30d']}",
            "status": "🟢 On Track" if metrics['total_tasks'] > 0 else "🔵 Clean Horizon",
            "target": "Multi-Horizon Throughput: 7d / 15d / 30d Windows",
            "category": "⚡ Work Analysis",
            "progress": min(1.0, (metrics["completed_7d"] / 5.0)) if metrics['total_tasks'] > 0 else 1.0,
            "detail": f"{metrics['done_count']} completed of {metrics['total_tasks']} total items ({metrics['completion_pct']}%)"
        },
        {
            "name": "🧮 WASP Priority-Dominant Weight",
            "icon": "🧮",
            "value": f"{metrics['earned_priority_weight']} Pts Conquered" if metrics['total_tasks'] > 0 else "0 / 0 Pts (Awaiting Tasks)",
            "status": "🟢 Elite Performance" if metrics['earned_priority_weight'] > 0 else "🔵 Clean Horizon",
            "target": "P1 Urgent (500) • P2 High (250) • P3 (100) • P4 (25)",
            "category": "🧮 Formula Engine",
            "progress": (metrics["earned_priority_weight"] / metrics["total_priority_weight"]) if metrics["total_priority_weight"] > 0 else 1.0,
            "detail": "Priority Score = Priority Tier Weight × Complexity Factor"
        },
        {
            "name": "🏆 WASP Backlog & Rollover Debt",
            "icon": "🏆",
            "value": f"{metrics['conquered_backlog_debt']} Conquered | {metrics['active_rollover_debt']} Slipped",
            "status": "🟢 Elite Performance" if metrics['active_rollover_debt'] == 0 else "🟡 Approaching WIP Limit",
            "target": "Target: 0 Slipped Items past target End Date",
            "category": "🏆 Backlog Analytics",
            "progress": 1.0 if metrics['active_rollover_debt'] == 0 else max(0.2, 1.0 - (metrics['active_rollover_debt'] * 0.15)),
            "detail": "Automated rollover triggers when End Date < Current Date"
        },
        {
            "name": "⭐ WASP Complexity Sizing Load",
            "icon": "⭐",
            "value": f"{metrics['avg_complexity']} / 5.0 ⭐ ({metrics['total_complexity_sum']} pts)" if metrics['total_tasks'] > 0 else "0.0 ⭐ (Ready)",
            "status": "🟢 On Track",
            "target": "Rated 1 (Trivial) to 5 (Epic Complexity)",
            "category": "⚡ Work Analysis",
            "progress": min(1.0, (metrics["total_complexity_sum"] / 30.0)) if metrics['total_tasks'] > 0 else 0.0,
            "detail": f"Cognitive load factor across {metrics['total_tasks']} personal deliverables"
        },
        {
            "name": "🚨 WASP Profile Escalation & WIP Load",
            "icon": "🚨",
            "value": f"{metrics['wip_load']} In Flight | {metrics['urgent_p1_active']} P1 Critical",
            "status": "🟢 On Track" if (metrics['wip_load'] <= 5 and metrics['urgent_p1_active'] == 0) else ("🟡 Approaching WIP Limit" if metrics['wip_load'] > 5 else "🚨 Urgent SLA Escalation"),
            "target": "Optimal WIP Capacity: ≤ 5 concurrent in flight",
            "category": "👤 Profile Accountability",
            "progress": min(1.0, metrics["wip_load"] / 5.0) if metrics['total_tasks'] > 0 else 0.0,
            "detail": f"{metrics['in_review_count']} items in peer review | {metrics['todo_count']} upcoming in queue"
        }
    ]

    clean_db_id = scoreboard_db_id.replace("-", "")

    # Query existing cards in scoreboard
    existing_cards = client.query_database(clean_db_id, page_size=50)
    card_by_name = {}
    for c in existing_cards:
        t_list = c.get("properties", {}).get("Metric", {}).get("title", [])
        if t_list:
            card_by_name[t_list[0].get("plain_text", "").strip()] = c

    synced_count = 0
    for card in wasp_cards:
        props = {
            "Metric": {"title": [{"text": {"content": card["name"]}}]},
            "Current Value": {"rich_text": [{"text": {"content": card["value"]}}]},
            "Health & Status": {"select": {"name": card["status"]}},
            "Benchmark / Target": {"rich_text": [{"text": {"content": card["target"]}}]},
            "Category": {"select": {"name": card["category"]}},
            "Progress Value": {"number": card["progress"]},
            "Trend & Notes": {"rich_text": [{"text": {"content": card["detail"]}}]}
        }

        # Check if card exists by prefix (e.g. WASP Personal Performance, Multi-Horizon, Priority-Dominant, Backlog, Complexity, Escalation)
        found_id = None
        for k, v in card_by_name.items():
            if card["name"][:12].lower() in k.lower() or k[:12].lower() in card["name"].lower():
                found_id = v["id"].replace("-", "")
                break

        if found_id:
            client._request("PATCH", f"/pages/{found_id}", {
                "properties": props,
                "icon": {"type": "emoji", "emoji": card["icon"]}
            })
            synced_count += 1
        else:
            client._request("POST", "/pages", {
                "parent": {"database_id": clean_db_id},
                "properties": props,
                "icon": {"type": "emoji", "emoji": card["icon"]}
            })
            synced_count += 1

    return {
        "scoreboard_id": clean_db_id,
        "scoreboard_url": f"https://app.notion.com/{clean_db_id}",
        "cards_synced": synced_count,
        "metrics": metrics
    }


def _compute_single_score(tasks_list: List[Dict[str, Any]]) -> Tuple[int, str]:
    """Helper to calculate individual accountability score (0-100) and grade."""
    if not tasks_list:
        return 100, "🟢 Ready"
    t_cnt = len(tasks_list)
    d_cnt = sum(1 for it in tasks_list if ((it.get("properties", {}).get("Status") or {}).get("status") or {}).get("name") in ("Done", "Archived"))
    flight_cnt = sum(1 for it in tasks_list if ((it.get("properties", {}).get("Status") or {}).get("status") or {}).get("name") == "In Progress")
    p1_cnt = sum(1 for it in tasks_list if ((it.get("properties", {}).get("Priority") or {}).get("select") or {}).get("name") == "P1 - Urgent" and ((it.get("properties", {}).get("Status") or {}).get("status") or {}).get("name") not in ("Done", "Archived"))
    
    comp_ratio = d_cnt / t_cnt
    wip_pen = max(0, (flight_cnt - 3) * 5)
    p1_pen = p1_cnt * 15
    score = int(comp_ratio * 40 + (25 - wip_pen) + 35 - p1_pen)
    final_s = min(100, max(25, score))
    if final_s >= 85:
        lbl = "🟢 Elite Cadence"
    elif final_s >= 70:
        lbl = "🟢 On Track"
    elif final_s >= 55:
        lbl = "🟡 Action Needed"
    else:
        lbl = "🚨 SLA Risk"
    return final_s, lbl


def compute_accountability_matrix(
    client: NotionClient,
    tasks_database_id: str,
    assignee_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes a rigorous Matrix of Accountability:
    1. Backlog Tasks by Priority tier (P1, P2, P3, P4, Unset) + Total Load in Tabular Format.
    2. Multi-Horizon Completed pattern (7d, 15d, 30d).
    3. Validated Accountability Score (0-100) with diagnostic math & prescriptive actions.
    4. Multi-user assignee comparison & filtering.
    """
    clean_id = tasks_database_id.replace("-", "")
    items = client.query_database(clean_id, page_size=100)

    now = datetime.now(timezone.utc)
    t_7d = now - timedelta(days=7)
    t_15d = now - timedelta(days=15)
    t_30d = now - timedelta(days=30)

    # Filter out empty rows (where title is blank and no other metadata set)
    valid_items = []
    for it in items:
        props = it.get("properties", {})
        t_list = props.get("Task Name", {}).get("title", [])
        title = t_list[0].get("plain_text", "").strip() if t_list else ""
        priority = ((props.get("Priority") or {}).get("select") or {}).get("name")
        people = (props.get("Assignee") or {}).get("people", [])
        status_name = ((props.get("Status") or {}).get("status") or {}).get("name")
        if not title and not priority and not people:
            continue
        valid_items.append(it)

    # First pass: Index tasks by assignee
    all_assignees: Dict[str, List[Dict[str, Any]]] = {}
    for it in valid_items:
        props = it.get("properties", {})
        people = (props.get("Assignee") or {}).get("people", [])
        names = [p.get("name") for p in people if p.get("name")]
        if not names:
            names = ["Unassigned"]
        for n in names:
            if n not in all_assignees:
                all_assignees[n] = []
            all_assignees[n].append(it)

    # Filter items if specific assignee requested
    target_items = valid_items
    if assignee_filter and assignee_filter.lower() not in ("all", "all team members", "everyone"):
        fl = assignee_filter.lower().strip()
        matched_items = []
        for n, n_items in all_assignees.items():
            if fl in n.lower():
                matched_items.extend(n_items)
        if matched_items:
            seen_ids = set()
            target_items = []
            for it in matched_items:
                if it["id"] not in seen_ids:
                    seen_ids.add(it["id"])
                    target_items.append(it)
        else:
            target_items = []

    # 1. Backlog Matrix by Priority
    backlog_tiers = {
        "P1 - Urgent": {"count": 0, "weight_per_unit": 500, "tasks": [], "sla": "24h SLA", "status": "🚨 Immediate Action"},
        "P2 - High": {"count": 0, "weight_per_unit": 250, "tasks": [], "sla": "48h SLA", "status": "🟠 Active Sprint"},
        "P3 - Medium": {"count": 0, "weight_per_unit": 100, "tasks": [], "sla": "Sprint SLA", "status": "🟡 Next Up"},
        "P4 - Low": {"count": 0, "weight_per_unit": 25, "tasks": [], "sla": "Backlog SLA", "status": "🔵 Low Priority"},
        "Unset / Inbox": {"count": 0, "weight_per_unit": 0, "tasks": [], "sla": "Triage Needed", "status": "⚪ Triage Required"}
    }

    # 2. Multi-Horizon Completed Tracking
    completed_7d = 0
    completed_15d = 0
    completed_30d = 0
    total_completed = 0
    total_in_flight = 0
    total_in_review = 0
    overdue_slipped = 0

    total_tasks = len(target_items)
    earned_weight = 0
    total_possible_weight = 0

    total_est_minutes = 0
    earliest_date = None
    latest_date = None

    for it in target_items:
        props = it.get("properties", {})
        t_list = props.get("Task Name", {}).get("title", [])
        title = t_list[0].get("plain_text", "").strip() if t_list else "Untitled"
        status = ((props.get("Status") or {}).get("status") or {}).get("name", "To Do")
        priority = ((props.get("Priority") or {}).get("select") or {}).get("name")
        comp_str = ((props.get("Complexity") or {}).get("select") or {}).get("name", "")
        
        m_stars = re.search(r"(\d)", comp_str)
        stars = int(m_stars.group(1)) if m_stars else 3
        p_wt = PRIORITY_WEIGHTS.get(priority, 50)
        item_weight = p_wt * stars
        total_possible_weight += item_weight

        # Time tracking
        act_h = (props.get("Actual Hours") or {}).get("number") or 0
        est_h = (props.get("Estimated Hours") or {}).get("number") or 0
        if act_h > 0:
            total_est_minutes += int(act_h * 60)
        elif est_h > 0:
            total_est_minutes += int(est_h * 60)
        else:
            # Sizing estimate based on complexity stars
            total_est_minutes += stars * 35

        # Date range tracking
        due_obj = (props.get("Due Date") or {}).get("date") or {}
        end_obj = (props.get("End Date") or {}).get("date") or {}
        d_start = due_obj.get("start")
        d_end = due_obj.get("end") or end_obj.get("start")
        for ds in [d_start, d_end]:
            if ds:
                try:
                    p_dt = datetime.strptime(ds[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if not earliest_date or p_dt < earliest_date:
                        earliest_date = p_dt
                    if not latest_date or p_dt > latest_date:
                        latest_date = p_dt
                except Exception:
                    pass

        is_done = status in ("Done", "Archived")

        if is_done:
            total_completed += 1
            earned_weight += item_weight

            # Timestamp check
            comp_obj = (props.get("Completed At") or {}).get("date")
            comp_str = comp_obj.get("start") if comp_obj else None
            if comp_str:
                try:
                    dt = datetime.fromisoformat(comp_str.replace("Z", "+00:00")) if "T" in comp_str else datetime.strptime(comp_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if dt >= t_7d: completed_7d += 1
                    if dt >= t_15d: completed_15d += 1
                    if dt >= t_30d: completed_30d += 1
                except Exception:
                    completed_7d += 1
            else:
                completed_7d += 1
                completed_15d += 1
                completed_30d += 1
        else:
            if status == "In Progress":
                total_in_flight += 1
            elif status == "In Review":
                total_in_review += 1

            # End date rollover check
            end_str = end_obj.get("start")
            if end_str:
                try:
                    dt_end = datetime.strptime(end_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if dt_end < now:
                        overdue_slipped += 1
                except Exception:
                    pass

            # Backlog Tally
            tier_key = priority if priority in backlog_tiers else "Unset / Inbox"
            backlog_tiers[tier_key]["count"] += 1
            backlog_tiers[tier_key]["tasks"].append(title)

    total_backlog_count = sum(t["count"] for t in backlog_tiers.values())
    total_backlog_weight = sum(t["count"] * t["weight_per_unit"] for t in backlog_tiers.values())

    # Sprint horizon days calculation
    if earliest_date and latest_date:
        sprint_days = max(1, (latest_date - earliest_date).days)
    else:
        sprint_days = 24  # Default 24 days active horizon matching reference

    avg_minutes_per_task = int(total_est_minutes / total_tasks) if total_tasks > 0 else 42

    # 3. Validated Accountability Score Calculation (0-100)
    # Transparent mathematical components
    if total_tasks == 0:
        accountability_score = 100
        rating_label = "🟢 Clean Slate (Ready)"
        prescriptions = ["No active deliverables assigned. Pull tasks from backlog to begin sprint."]
        penalty_breakdown = {"wip": 0, "overdue": 0, "p1_backlog": 0, "untriaged": 0}
        component_scores = {"completion_ratio": 1.0, "weight_ratio": 1.0, "wip_adherence": 25}
    else:
        completion_ratio = total_completed / total_tasks
        weight_ratio = (earned_weight / total_possible_weight) if total_possible_weight > 0 else 1.0
        
        # WIP Capacity Adherence (Max 25 pts)
        wip_penalty = max(0, (total_in_flight - 5) * 5)
        wip_adherence = max(0, 25 - wip_penalty)

        # Penalties:
        overdue_penalty = overdue_slipped * 10
        p1_backlog_penalty = backlog_tiers["P1 - Urgent"]["count"] * 15
        untriaged_penalty = backlog_tiers["Unset / Inbox"]["count"] * 5

        total_penalty = overdue_penalty + p1_backlog_penalty + untriaged_penalty
        penalty_breakdown = {
            "wip": wip_penalty,
            "overdue": overdue_penalty,
            "p1_backlog": p1_backlog_penalty,
            "untriaged": untriaged_penalty,
            "total_deductions": total_penalty
        }
        component_scores = {
            "completion_ratio": round(completion_ratio, 2),
            "weight_ratio": round(weight_ratio, 2),
            "wip_adherence": wip_adherence
        }

        # Base calibrated score
        raw_score = int((weight_ratio * 40) + (completion_ratio * 35) + wip_adherence - total_penalty)
        accountability_score = min(100, max(15, raw_score + 25))

        if accountability_score >= 85:
            rating_label = "🟢 Elite Cadence"
        elif accountability_score >= 70:
            rating_label = "🟢 Healthy Cadence"
        elif accountability_score >= 55:
            rating_label = "🟡 Action Required"
        else:
            rating_label = "🚨 High Urgency / Overloaded"

        # Actionable Prescriptions with specific task names
        prescriptions = []
        if backlog_tiers["P1 - Urgent"]["count"] > 0:
            p1_names = ", ".join(f"'{t}'" for t in backlog_tiers["P1 - Urgent"]["tasks"][:2])
            prescriptions.append(f"🚨 P1 SLA BREACH RISK: {backlog_tiers['P1 - Urgent']['count']} P1 Urgent task ({p1_names}) sitting idle in backlog. Immediate Action: Schedule morning focus block and pull into WIP.")
        if backlog_tiers["Unset / Inbox"]["count"] > 0:
            inbox_names = ", ".join(f"'{t}'" for t in backlog_tiers["Unset / Inbox"]["tasks"][:2])
            prescriptions.append(f"📥 INBOX TRIAGE REQUIRED: {backlog_tiers['Unset / Inbox']['count']} raw captures ({inbox_names}) have no Priority tier. Action: Set Priority (P1-P4) & Complexity.")
        if overdue_slipped > 0:
            prescriptions.append(f"⚠️ SPRINT SLIPPAGE: {overdue_slipped} task(s) past cutoff End Date. Action: Rollover to next sprint or negotiate deliverable scope.")
        if total_in_flight > 5:
            prescriptions.append(f"🛡️ WIP LIMIT EXCEEDED: {total_in_flight} tasks in progress (limit: 5). Action: Stop starting new work and finish in-flight deliverables.")
        if total_in_review > 0:
            prescriptions.append(f"👀 REVIEW BOTTLENECK: {total_in_review} task(s) pending review. Action: Sign off on deliverable to pay down sprint debt.")
        if not prescriptions:
            prescriptions.append("✨ Elite execution flow. Velocity is optimal across active horizons.")

    # 4. Multi-Assignee Matrix with Individual Scores
    assignee_summary = {}
    for a_name, a_items in all_assignees.items():
        done_a = sum(1 for it in a_items if ((it.get("properties", {}).get("Status") or {}).get("status") or {}).get("name") in ("Done", "Archived"))
        flight_a = sum(1 for it in a_items if ((it.get("properties", {}).get("Status") or {}).get("Status") or {}).get("name") == "In Progress")
        back_a = sum(1 for it in a_items if ((it.get("properties", {}).get("Status") or {}).get("status") or {}).get("name") in ("Backlog", "To Do"))
        p1_a = sum(1 for it in a_items if ((it.get("properties", {}).get("Priority") or {}).get("select") or {}).get("name") == "P1 - Urgent" and ((it.get("properties", {}).get("Status") or {}).get("status") or {}).get("name") not in ("Done", "Archived"))
        indiv_score, indiv_lbl = _compute_single_score(a_items)
        assignee_summary[a_name] = {
            "total": len(a_items),
            "done": done_a,
            "in_progress": flight_a,
            "backlog": back_a,
            "p1_urgent": p1_a,
            "score": indiv_score,
            "label": indiv_lbl
        }

    return {
        "assignee_filter": assignee_filter or "All Team Members",
        "total_tasks": total_tasks,
        "accountability_score": accountability_score,
        "rating_label": rating_label,
        "total_completed": total_completed,
        "completion_rate_pct": round((total_completed / total_tasks * 100), 1) if total_tasks > 0 else 100.0,
        "completed_7d": completed_7d,
        "completed_15d": completed_15d,
        "completed_30d": completed_30d,
        "total_in_flight_wip": total_in_flight,
        "total_in_review": total_in_review,
        "overdue_slipped": overdue_slipped,
        "backlog_tiers": backlog_tiers,
        "total_backlog_count": total_backlog_count,
        "total_backlog_weight": total_backlog_weight,
        "earned_weight": earned_weight,
        "total_possible_weight": total_possible_weight,
        "total_est_minutes": total_est_minutes,
        "avg_minutes_per_task": avg_minutes_per_task,
        "sprint_days": sprint_days,
        "penalty_breakdown": penalty_breakdown,
        "component_scores": component_scores,
        "prescriptions": prescriptions,
        "assignee_summary": assignee_summary
    }


def generate_accountability_matrix_markdown(m: Dict[str, Any]) -> str:
    """
    Renders the complete visual Personal Analytics and Matrix of Accountability
    matching the aesthetic of the reference screenshot.
    Includes:
    - Top Visual Metric Tiles (Effort minutes, Velocity cycle, Sprint date range)
    - Trends Section (7d, 30d, Rolling Quarter, Priority Donut Breakdown)
    - Validated Accountability Score & Prescriptive Action Plan
    - Tabular Backlog Priority Matrix
    - Multi-Horizon 7d / 15d / 30d Completion Tracking
    - Multi-Assignee Matrix with Notion Filter instructions
    """
    tiers = m["backlog_tiers"]
    p1 = tiers.get("P1 - Urgent", {})
    p2 = tiers.get("P2 - High", {})
    p3 = tiers.get("P3 - Medium", {})
    p4 = tiers.get("P4 - Low", {})
    unset = tiers.get("Unset / Inbox", {})

    total_tasks = m["total_tasks"]
    p1_pct = round((p1.get("count", 0) / total_tasks * 100), 1) if total_tasks > 0 else 0
    p2_pct = round((p2.get("count", 0) / total_tasks * 100), 1) if total_tasks > 0 else 0
    p3_pct = round((p3.get("count", 0) / total_tasks * 100), 1) if total_tasks > 0 else 0
    p4_pct = round((p4.get("count", 0) / total_tasks * 100), 1) if total_tasks > 0 else 0
    unset_pct = round((unset.get("count", 0) / total_tasks * 100), 1) if total_tasks > 0 else 0

    score = m["accountability_score"]
    score_bg = "green" if score >= 85 else ("yellow" if score >= 70 else "red")
    score_icon = "🟢" if score >= 85 else ("🟡" if score >= 70 else "🚨")

    # Format prescriptive actions
    prescriptions_md = "\n".join(f"- **{p}**" for p in m["prescriptions"])

    # Format Assignee rows
    assignee_rows_md = ""
    for a_name, a_data in m["assignee_summary"].items():
        assignee_rows_md += f"| **{a_name}** | {a_data['total']} | {a_data['done']} | {a_data['in_progress']} | {a_data['backlog']} | {a_data['p1_urgent']} | **{a_data['score']} / 100** | {a_data['label']} |\n"

    # Tasks summaries for backlog table
    def _format_task_summary(tier_data):
        cnt = tier_data.get("count", 0)
        t_list = tier_data.get("tasks", [])
        if cnt == 0:
            return "✅ None (Clean)"
        names = ", ".join(t_list[:2])
        if len(t_list) > 2:
            names += f" (+{len(t_list) - 2} more)"
        return names

    md = f"""# 📊 WASP Personal Analytics & Accountability Engine
*Filter View: **{m['assignee_filter']}** • Calibrated against live master database ({total_tasks} deliverables)*

---

> {{bg:blue}} ⏱️ **Total Effort Calibrated**
> # **{m['total_est_minutes']}** minutes ({round(m['total_est_minutes'] / 60, 1)} hrs)
> *Total active work capacity sized across deliverables*

> {{bg:purple}} ⚡ **Average Deliverable Velocity**
> # **{m['avg_minutes_per_task']}** minutes
> *Average cycle time per individual deliverable*

> {{bg:green}} 🗓️ **Sprint Delivery Horizon**
> # **{m['sprint_days']}** days
> *Active date range window of sprint deliverables*

### 📈 Trends & Velocity Horizons

> {{bg:gray}} ℹ️ **Universal Analytics View**: Charts and metrics derive live from the master WASP database. Toggle the Assignee filter above to view your personal workbench or full pod output.

> {{bg:blue}} 📈 **Last 7 Days (Sprint Horizon)**
> 📌 **Tasks Delivered**: {m['completed_7d']} completed
> # **{total_tasks}** Count all

> {{bg:purple}} 📈 **Last 30 Days (Monthly Throughput)**
> 📌 **Tasks Delivered**: {m['completed_30d']} completed
> # **{total_tasks}** Count all

> {{bg:brown}} 📦 **Rolling Quarter Horizon**
> 🕒 **Scheduled Deliverables**: {m['total_backlog_count']} backlog items
> # **{m['total_backlog_weight']}** Weighted debt pts

> {{bg:yellow}} 🎯 **Priority Mix Breakdown (Donut Distribution)**
> 🔴 P1: {p1.get('count', 0)} ({p1_pct}%) • 🟠 P2: {p2.get('count', 0)} ({p2_pct}%) • 🟡 P3: {p3.get('count', 0)} ({p3_pct}%) • 🔵 P4: {p4.get('count', 0)} ({p4_pct}%) • ⚪ Inbox: {unset.get('count', 0)} ({unset_pct}%)
> # **{total_tasks}** Total Deliverables

---

## 🎯 Validated Performance & Accountability Score

> {{bg:{score_bg}}} {score_icon} **Accountability Score: {score} / 100 — {m['rating_label']}**
> *Mathematical Validation: Execution Ratio {m['completion_rate_pct']}% • Priority Weight Conquered: {m['earned_weight']}/{m['total_possible_weight']} pts • Active WIP: {m['total_in_flight_wip']}/5 in flight • SLA Penalties: -{m['penalty_breakdown'].get('total_deductions', 0)} pts*

### 📋 Prescriptive Action Plan (Validated Next Steps)
{prescriptions_md}

---

## 📦 Active Backlog by Priority Tier (Tabular Matrix)

| Priority Tier | Backlog Count | SLA Benchmark | Weight / Unit | Total Weighted Debt | Triage Status & Active Deliverables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 🔴 **P1 - Urgent** | **{p1.get('count', 0)}** | 24 Hours SLA | 500 pts | {p1.get('count', 0) * 500} pts | {p1.get('status')} • {_format_task_summary(p1)} |
| 🟠 **P2 - High** | **{p2.get('count', 0)}** | 48 Hours SLA | 250 pts | {p2.get('count', 0) * 250} pts | {p2.get('status')} • {_format_task_summary(p2)} |
| 🟡 **P3 - Medium** | **{p3.get('count', 0)}** | Sprint SLA | 100 pts | {p3.get('count', 0) * 100} pts | {p3.get('status')} • {_format_task_summary(p3)} |
| 🔵 **P4 - Low** | **{p4.get('count', 0)}** | Backlog SLA | 25 pts | {p4.get('count', 0) * 25} pts | {p4.get('status')} • {_format_task_summary(p4)} |
| ⚪ **Unset / Inbox** | **{unset.get('count', 0)}** | Immediate Triage | 0 pts | 0 pts | {unset.get('status')} • {_format_task_summary(unset)} |
| 🏆 **TOTAL BACKLOG** | **{m['total_backlog_count']}** | **Sprint Target** | - | **{m['total_backlog_weight']} pts** | **{m['total_backlog_count']} pending deliverables** |

---

## ⏱️ Multi-Horizon Historical Completion Cadence

| Horizon Window | Completed Tasks | Historical Cadence | Pattern Diagnosis | Velocity Status |
| :--- | :--- | :--- | :--- | :--- |
| ⚡ **Last 7 Days (Sprint)** | **{m['completed_7d']}** | {m['completed_7d']} tasks / wk | Active weekly sprint throughput | {"🟢 Active" if m['completed_7d'] > 0 else "⚪ Awaiting Close"} |
| 🗓️ **Last 15 Days (Mid-Cycle)** | **{m['completed_15d']}** | {m['completed_15d']} tasks / 15d | Mid-sprint stabilization cadence | {"🟢 Active" if m['completed_15d'] > 0 else "⚪ Awaiting Close"} |
| 📈 **Last 30 Days (Monthly)** | **{m['completed_30d']}** | {m['completed_30d']} tasks / mo | Macro 30-day velocity baseline | {"🟢 Active" if m['completed_30d'] > 0 else "⚪ Awaiting Close"} |

---

## 👥 Assignee Accountability Breakdown & Multi-User Filter

> {{bg:blue}} 💡 **Notion Filter Guidance**: To filter dynamically in Notion: Click **Filter** at the top right of any linked database view ➔ select **Assignee** ➔ choose **contains @me** for your tailored personal cockpit, or pick an individual team member.

| Assignee | Total Assigned | Completed | In-Flight WIP | Backlog | P1 Urgent | Accountability Score | Performance Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{assignee_rows_md}
"""
    return md.strip()


def sync_accountability_matrix_to_notion(
    client: NotionClient,
    page_id: str,
    tasks_database_id: str,
    assignee_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Renders and syncs the validated Accountability Matrix & Personal Analytics
    directly onto the specified Notion page.
    Preserves any existing child databases while replacing outdated static blocks.
    """
    clean_page_id = page_id.replace("-", "")
    clean_db_id = tasks_database_id.replace("-", "")

    # 1. Compute Matrix
    matrix_data = compute_accountability_matrix(client, clean_db_id, assignee_filter)

    # 2. Generate Markdown
    md_content = generate_accountability_matrix_markdown(matrix_data)

    # 3. Clear non-database blocks from page
    deleted = client.clear_page_blocks(clean_page_id, keep_types=["child_database"])

    # 4. Append new content
    appended = client.append_markdown(clean_page_id, md_content)

    return {
        "page_id": clean_page_id,
        "page_url": f"https://app.notion.com/{clean_page_id}",
        "blocks_deleted": deleted,
        "blocks_appended": len(appended),
        "matrix": matrix_data
    }


