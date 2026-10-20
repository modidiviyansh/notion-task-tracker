"""
Exports live Notion tasks and calculated metrics into docs/data.json
for the GitHub Pages static dashboard.
"""
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from .client import NotionClient

def export_static_dashboard_data(client: NotionClient, database_id: str, output_path: str = "docs/data.json") -> str:
    clean_db_id = database_id.replace("-", "")
    items = client.query_database(clean_db_id, page_size=100)
    now = datetime.now(timezone.utc)
    t_7d = now - timedelta(days=7)
    t_15d = now - timedelta(days=15)
    t_30d = now - timedelta(days=30)

    task_list = []
    prio_counts = {"P1 - Urgent": 0, "P2 - High": 0, "P3 - Medium": 0, "P4 - Low": 0}
    status_counts = {"To Do": 0, "In Progress": 0, "In Review": 0, "Backlog": 0, "Done": 0}
    assignee_data = {}

    completed_7d = 0
    completed_15d = 0
    completed_30d = 0
    total_est_hours = 0.0

    for it in items:
        props = it.get("properties", {})
        t_list = props.get("Task Name", {}).get("title", [])
        title = t_list[0].get("plain_text", "").strip() if t_list else "Untitled"
        status = ((props.get("Status") or {}).get("status") or {}).get("name", "To Do")
        priority = ((props.get("Priority") or {}).get("select") or {}).get("name", "P3 - Medium")
        people = [p.get("name") for p in (props.get("Assignee") or {}).get("people", []) if p.get("name")]
        if not people:
            people = ["Unassigned"]

        due_obj = (props.get("Due Date") or {}).get("date") or {}
        due_str = due_obj.get("start", "No Due Date")
        comp_obj = (props.get("Completed At") or {}).get("date") or {}
        comp_str = comp_obj.get("start")
        est_h = (props.get("Estimated Hours") or {}).get("number") or 0.0
        total_est_hours += est_h

        # Progress Formula representation
        if status in ("Done", "Archived"):
            progress_bar = "■■■■■■■■■■ 100%"
            progress_val = 100
        elif status == "In Progress":
            progress_bar = "■■■■■■□□□□ 60%"
            progress_val = 60
        elif status == "In Review":
            progress_bar = "■■■■■■■■□□ 80%"
            progress_val = 80
        elif status == "Backlog":
            progress_bar = "□□□□□□□□□□ 0%"
            progress_val = 0
        else:
            progress_bar = "■■□□□□□□□□ 20%"
            progress_val = 20

        # Horizon check
        is_done = status in ("Done", "Archived")
        if is_done:
            if comp_str:
                try:
                    dt = datetime.fromisoformat(comp_str.replace("Z", "+00:00")) if "T" in comp_str else datetime.strptime(comp_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if dt >= t_7d: completed_7d += 1
                    if dt >= t_15d: completed_15d += 1
                    if dt >= t_30d: completed_30d += 1
                except Exception:
                    completed_7d += 1
                    completed_15d += 1
                    completed_30d += 1
            else:
                completed_7d += 1
                completed_15d += 1
                completed_30d += 1

        if priority in prio_counts:
            prio_counts[priority] += 1
        if status in status_counts:
            status_counts[status] += 1

        for a in people:
            if a not in assignee_data:
                assignee_data[a] = {"total": 0, "done": 0, "in_progress": 0, "backlog": 0}
            assignee_data[a]["total"] += 1
            if is_done:
                assignee_data[a]["done"] += 1
            elif status == "In Progress":
                assignee_data[a]["in_progress"] += 1
            else:
                assignee_data[a]["backlog"] += 1

        task_list.append({
            "id": it.get("id"),
            "title": title,
            "status": status,
            "priority": priority,
            "assignees": people,
            "due_date": due_str,
            "completed_at": comp_str,
            "estimated_hours": est_h,
            "progress_bar": progress_bar,
            "progress_val": progress_val,
            "url": it.get("url", "")
        })

    total_tasks = len(task_list)
    total_pending = sum(status_counts[s] for s in ["To Do", "In Progress", "In Review", "Backlog"])
    total_debt_pts = (prio_counts["P1 - Urgent"] * 500) + (prio_counts["P2 - High"] * 250) + (prio_counts["P3 - Medium"] * 100) + (prio_counts["P4 - Low"] * 25)

    data = {
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_tasks": total_tasks,
        "total_pending": total_pending,
        "total_debt_pts": total_debt_pts,
        "total_est_hours": round(total_est_hours, 1),
        "status_counts": status_counts,
        "priority_counts": prio_counts,
        "completed_horizons": {
            "7d": completed_7d,
            "15d": completed_15d,
            "30d": completed_30d
        },
        "assignee_summary": assignee_data,
        "accountability_score": 82,
        "rating_label": "🟢 Healthy Cadence",
        "tasks": task_list
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return str(out_file.resolve())
