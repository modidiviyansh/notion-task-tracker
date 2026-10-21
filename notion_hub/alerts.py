"""
Google Workspace & Webhook Alert Engine for WASP Task Hub.
Dispatches Google Chat Card v2 interactive messages and Gmail briefings.
Compatible with n8n webhooks and direct Google Chat Space webhooks.
"""
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .client import NotionClient

DEFAULT_GOOGLE_CHAT_WEBHOOK = os.environ.get("GOOGLE_CHAT_WEBHOOK_URL", "")
DEFAULT_ADMIN_EMAIL = os.environ.get("ADMIN_WORKSPACE_EMAIL", "diviyanshmodi@gcmconventschool.in")


def build_google_chat_p1_alert_card(task: Dict[str, Any], database_url: str = "") -> Dict[str, Any]:
    """Builds a high-priority Google Chat Card v2 alert for P1 SLA breaches."""
    props = task.get("properties", {})
    t_list = props.get("Task Name", {}).get("title", [])
    title = t_list[0].get("plain_text", "").strip() if t_list else "Untitled Deliverable"
    status = ((props.get("Status") or {}).get("status") or {}).get("name", "To Do")
    assignees = [p.get("name") for p in (props.get("Assignee") or {}).get("people", []) if p.get("name")]
    assignee_str = ", ".join(assignees) if assignees else "⚠️ Unassigned (Triage Needed)"
    due = (props.get("Due Date") or {}).get("date") or {}
    due_str = due.get("start", "No Date Set")
    est_hours = (props.get("Estimated Hours") or {}).get("number") or 0.0
    task_url = task.get("url", database_url)

    card = {
        "cardsV2": [{
            "cardId": f"p1-alert-{task.get('id', 'item')}",
            "card": {
                "header": {
                    "title": "🚨 URGENT P1 SLA BREACH ALERT",
                    "subtitle": "WASP Task Engine • 24h SLA Active",
                    "imageUrl": "https://img.icons8.com/color/96/high-priority.png",
                    "imageType": "CIRCLE"
                },
                "sections": [
                    {
                        "header": "Deliverable Details",
                        "widgets": [
                            {
                                "decoratedText": {
                                    "topLabel": "Task Name",
                                    "text": f"<b>{title}</b>",
                                    "icon": {"knownIcon": "DESCRIPTION"}
                                }
                            },
                            {
                                "decoratedText": {
                                    "topLabel": "Current Status & Assignee",
                                    "text": f"<b>{status}</b> • Owner: {assignee_str}",
                                    "icon": {"knownIcon": "PERSON"}
                                }
                            },
                            {
                                "decoratedText": {
                                    "topLabel": "Due Date & Effort Sizing",
                                    "text": f"📅 {due_str} • Effort: {est_hours} hrs",
                                    "icon": {"knownIcon": "CLOCK"}
                                }
                            }
                        ]
                    },
                    {
                        "widgets": [
                            {
                                "buttonList": {
                                    "buttons": [
                                        {
                                            "text": "OPEN IN NOTION",
                                            "color": {"red": 0.85, "green": 0.2, "blue": 0.2, "alpha": 1.0},
                                            "onClick": {
                                                "openLink": {"url": task_url}
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        }]
    }
    return card


def build_weekly_digest_card(metrics: Dict[str, Any], dashboard_url: str) -> Dict[str, Any]:
    """Builds a weekly executive scorecard Card v2 for Google Chat."""
    card = {
        "cardsV2": [{
            "cardId": f"weekly-digest-{int(datetime.now().timestamp())}",
            "card": {
                "header": {
                    "title": "🐝 WASP Weekly Executive Digest",
                    "subtitle": f"Sprint Horizon Throughput • Score: {metrics.get('wasp_score', 82)}/100",
                    "imageUrl": "https://img.icons8.com/color/96/line-chart.png",
                    "imageType": "CIRCLE"
                },
                "sections": [
                    {
                        "header": "Performance Cockpit",
                        "widgets": [
                            {
                                "decoratedText": {
                                    "topLabel": "Accountability Score",
                                    "text": f"<b>{metrics.get('wasp_score', 82)} / 100 Pts</b> (🟢 Healthy Cadence)",
                                    "icon": {"knownIcon": "STAR"}
                                }
                            },
                            {
                                "decoratedText": {
                                    "topLabel": "Multi-Horizon Throughput",
                                    "text": f"⚡ 7d: <b>{metrics.get('completed_7d', 1)}</b> • 🗓️ 15d: <b>{metrics.get('completed_15d', 1)}</b> • 📈 30d: <b>{metrics.get('completed_30d', 1)}</b>",
                                    "icon": {"knownIcon": "TICKET"}
                                }
                            },
                            {
                                "decoratedText": {
                                    "topLabel": "Backlog Queue & Slipped Debt",
                                    "text": f"📦 <b>{metrics.get('backlog_count', 10)} pending</b> ({metrics.get('total_debt_pts', 1325)} weighted pts)",
                                    "icon": {"knownIcon": "BOOKMARK"}
                                }
                            }
                        ]
                    },
                    {
                        "widgets": [
                            {
                                "buttonList": {
                                    "buttons": [
                                        {
                                            "text": "VIEW TASK TRACKER",
                                            "onClick": {
                                                "openLink": {"url": dashboard_url}
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        }]
    }
    return card


def send_google_chat_webhook(payload: Dict[str, Any], webhook_url: Optional[str] = None) -> Dict[str, Any]:
    """Sends a message payload to a Google Chat Space webhook URL."""
    url = webhook_url or DEFAULT_GOOGLE_CHAT_WEBHOOK
    if not url:
        return {
            "status": "simulated",
            "message": "No GOOGLE_CHAT_WEBHOOK_URL set. Payload generated in test mode.",
            "payload": payload
        }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json; charset=UTF-8"})
    try:
        with urllib.request.urlopen(req) as resp:
            return {"status": "sent", "http_code": resp.status, "response": resp.read().decode("utf-8")}
    except urllib.error.HTTPError as e:
        return {"status": "error", "http_code": e.code, "error": e.read().decode("utf-8")}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def scan_and_dispatch_p1_alerts(client: NotionClient, db_id: str, webhook_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """Scans for active P1 Urgent tasks and dispatches alerts."""
    items = client.query_database(db_id.replace("-", ""), page_size=100)
    alerts = []
    for it in items:
        props = it.get("properties", {})
        status = ((props.get("Status") or {}).get("status") or {}).get("name", "")
        priority = ((props.get("Priority") or {}).get("select") or {}).get("name", "")
        if priority == "P1 - Urgent" and status not in ("Done", "Archived"):
            card = build_google_chat_p1_alert_card(it)
            dispatch_res = send_google_chat_webhook(card, webhook_url)
            t_list = props.get("Task Name", {}).get("title", [])
            title = t_list[0].get("plain_text", "").strip() if t_list else "Untitled"
            alerts.append({"task_id": it["id"], "task_title": title, "dispatch": dispatch_res})
    return alerts


def rollover_overdue_tasks_to_backlog(
    client: NotionClient,
    db_id: str,
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Scans for non-completed deliverables whose Due Date (or End Date) has passed.
    1. Flips Status to 'Backlog'
    2. Sets 'Original Backlog Item' to True
    3. Builds and dispatches a Google Chat Card v2 rollover summary card.
    """
    clean_db = db_id.replace("-", "")
    items = client.query_database(clean_db, page_size=100)
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    overdue_tasks = []
    for it in items:
        props = it.get("properties", {})
        status = ((props.get("Status") or {}).get("status") or {}).get("name", "")
        if status in ("Done", "Archived", "Backlog"):
            continue

        due_obj = (props.get("Due Date") or {}).get("date") or {}
        end_obj = (props.get("End Date") or {}).get("date") or {}
        due_date_str = due_obj.get("start") or end_obj.get("start")
        if not due_date_str:
            continue

        if due_date_str < today_str:
            t_list = props.get("Task Name", {}).get("title", [])
            title = t_list[0].get("plain_text", "").strip() if t_list else "Untitled Deliverable"
            priority = ((props.get("Priority") or {}).get("select") or {}).get("name", "P3 - Medium")
            complexity = ((props.get("Complexity") or {}).get("select") or {}).get("name", "⭐⭐⭐ 3 - Moderate")
            assignees = [p.get("name") for p in (props.get("Assignee") or {}).get("people", []) if p.get("name")]
            assignee_str = ", ".join(assignees) if assignees else "Unassigned"

            client.update_page(it["id"], {
                "Status": {"status": {"name": "Backlog"}},
                "Original Backlog Item": {"checkbox": True}
            })

            overdue_tasks.append({
                "id": it["id"],
                "title": title,
                "prev_status": status,
                "priority": priority,
                "complexity": complexity,
                "due_date": due_date_str,
                "assignee": assignee_str,
                "url": it.get("url", f"https://notion.so/{it['id'].replace('-', '')}")
            })

    dispatch_res = {"status": "none", "message": "No overdue tasks found."}
    if overdue_tasks:
        widgets = [
            {
                "textParagraph": {
                    "text": f"<b>🌙 3:00 AM IST Daily Rollover Scan</b>: <b>{len(overdue_tasks)} incomplete deliverables</b> missed their deadline and were moved to <b>Backlog Debt</b> for sprint triage."
                }
            }
        ]
        for t in overdue_tasks[:6]:
            widgets.append({
                "decoratedText": {
                    "topLabel": f"Missed Due Date: {t['due_date']} • Prev: {t['prev_status']}",
                    "text": f"• <b>{t['title']}</b> ({t['priority']} | {t['complexity']})",
                    "bottomLabel": f"Owner: {t['assignee']}",
                    "icon": {"knownIcon": "CLOCK"}
                }
            })

        card = {
            "cardsV2": [{
                "cardId": f"wasp_rollover_{int(datetime.now().timestamp())}",
                "card": {
                    "header": {
                        "title": "🐝 WASP Engine — Overdue Backlog Rollover",
                        "subtitle": f"{len(overdue_tasks)} Incomplete Tasks Rolled Into Backlog Debt",
                        "imageUrl": "https://cdn-icons-png.flaticon.com/512/3281/3281307.png",
                        "imageType": "CIRCLE"
                    },
                    "sections": [
                        {
                            "header": "Rolled-Over Deliverables Summary",
                            "widgets": widgets
                        },
                        {
                            "widgets": [
                                {
                                    "buttonList": {
                                        "buttons": [
                                            {
                                                "text": "OPEN NOTION DASHBOARD",
                                                "color": {"red": 0.14, "green": 0.51, "blue": 0.89, "alpha": 1.0},
                                                "onClick": {
                                                    "openLink": {"url": "https://app.notion.com/3fff1bcff9b881be9e4fd3df8f014a52"}
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            }]
        }
        dispatch_res = send_google_chat_webhook(card, webhook_url)

    return {
        "overdue_count": len(overdue_tasks),
        "tasks": overdue_tasks,
        "dispatch": dispatch_res
    }

