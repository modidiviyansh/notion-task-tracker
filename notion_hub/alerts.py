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
