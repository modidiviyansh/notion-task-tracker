"""
Human-Driven Task Decomposition & Notes Breakdown Engine.
Allows developers to select a Notion task and provide their own execution notes,
major pillars, and implementation steps. Decomposes the notes into individual subtasks
linked with native Parent-Child relations to the original task.
"""
import re
from typing import Dict, Any, List, Optional
from .client import NotionClient

COMPLEXITY_OPTIONS = {
    1: "⭐ 1 - Trivial",
    2: "⭐⭐ 2 - Simple",
    3: "⭐⭐⭐ 3 - Moderate",
    4: "⭐⭐⭐⭐ 4 - Complex",
    5: "⭐⭐⭐⭐⭐ 5 - Epic"
}

POD_KEYWORDS = {
    "frontend": "Frontend", "ui": "Frontend", "ux": "Frontend", "web": "Frontend", "client": "Frontend", "css": "Frontend", "html": "Frontend",
    "backend": "Backend", "api": "Backend", "database": "Backend", "db": "Backend", "server": "Backend", "postgres": "Backend", "sql": "Backend",
    "design": "Design", "figma": "Design", "video": "Design", "creative": "Design", "motion": "Design",
    "qa": "QA & Security", "security": "QA & Security", "test": "QA & Security", "audit": "QA & Security", "testing": "QA & Security",
    "devops": "DevOps & Infra", "infra": "DevOps & Infra", "cloud": "DevOps & Infra", "docker": "DevOps & Infra", "ci": "DevOps & Infra",
    "product": "Product", "spec": "Product", "requirements": "Product",
    "operations": "Operations & Chores", "ops": "Operations & Chores"
}

PRIORITY_MAP = {
    "p1": "P1 - Urgent",
    "urgent": "P1 - Urgent",
    "critical": "P1 - Urgent",
    "p2": "P2 - High",
    "high": "P2 - High",
    "p3": "P3 - Medium",
    "medium": "P3 - Medium",
    "p4": "P4 - Low",
    "low": "P4 - Low"
}


def parse_notes_into_subtasks(
    parent_title: str,
    notes_text: str,
    default_pod: str = "Backend",
    default_priority: str = "P2 - High"
) -> Dict[str, Any]:
    """
    Parses developer notes, major pillars, and bulleted implementation steps
    into a structured subtask decomposition plan.
    """
    lines = [l for l in notes_text.splitlines() if l.strip()]
    subtasks = []
    current_pillar = "Execution"
    total_hours = 0.0

    hours_re = re.compile(r'(\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hours)\b', re.IGNORECASE)
    prio_re = re.compile(r'\b(P1|P2|P3|P4|Urgent|High|Medium|Low)\b', re.IGNORECASE)

    for line in lines:
        stripped = line.strip()

        # Skip generic top-level headers
        if re.match(r'^(?:#+\s*)?(?:major\s+pillars?|implementation\s+plan|notes?)\s*:?$', stripped, re.IGNORECASE):
            continue

        # Check if line is a Pillar / Phase / Milestone header
        # e.g. "Pillar 1: Data Architecture", "## Pillar 1", "1. Architecture & Database"
        is_pillar_header = False
        if stripped.startswith("#"):
            is_pillar_header = True
            current_pillar = stripped.lstrip("#").strip()
        elif re.match(r'^(?:pillar|phase|milestone|section)\s*\d*[:\s-]', stripped, re.IGNORECASE):
            is_pillar_header = True
            current_pillar = re.sub(r'^(?:pillar|phase|milestone|section)\s*\d*[:\s-]\s*', '', stripped, flags=re.IGNORECASE).strip()
        elif re.match(r'^\d+[\.:\)]\s*[A-Za-z]', stripped) and not hours_re.search(stripped) and not stripped.startswith("-"):
            # Numbered pillar header without hours (e.g. "1. Architecture & Database")
            is_pillar_header = True
            current_pillar = re.sub(r'^\d+[\.:\)]\s*', '', stripped).strip()

        if is_pillar_header:
            continue

        # Extract item text by stripping bullet prefixes: -, *, •, 1., etc.
        m_bullet = re.match(r'^(?:[-*•]\s*(?:\[[\sx]\]\s*)?|\d+[\.)]\s*)(.*)$', stripped)
        raw_text = m_bullet.group(1).strip() if m_bullet else stripped

        if not raw_text:
            continue

        # Extract estimated hours
        m_hrs = hours_re.search(raw_text)
        hours = float(m_hrs.group(1)) if m_hrs else 2.5
        total_hours += hours

        # Extract priority
        m_pr = prio_re.search(raw_text)
        prio = default_priority
        if m_pr:
            p_key = m_pr.group(1).lower()
            prio = PRIORITY_MAP.get(p_key, default_priority)

        # Extract team/pod
        pod = default_pod
        lower_raw = raw_text.lower()
        for k, v in POD_KEYWORDS.items():
            if re.search(r'\b' + k + r'\b', lower_raw):
                pod = v
                break

        # Clean subtask title by removing parenthetical metadata like "(3h, Backend, P2)"
        clean_title = re.sub(r'[\(\[].*?[\)\]]', '', raw_text).strip()
        clean_title = re.sub(r'\s+', ' ', clean_title).strip(' -:')

        if not clean_title:
            clean_title = raw_text[:50]

        # Determine subtask complexity
        if hours <= 2.0:
            comp = "⭐ 1 - Trivial"
        elif hours <= 4.0:
            comp = "⭐⭐ 2 - Simple"
        else:
            comp = "⭐⭐⭐ 3 - Moderate"

        subtasks.append({
            "title": f"{parent_title} — {clean_title}",
            "short_title": clean_title,
            "estimated_hours": hours,
            "priority": prio,
            "team": pod,
            "complexity": comp,
            "pillar": current_pillar,
            "acceptance_criteria": f"Pillar: {current_pillar} • Deliverable: {clean_title}"
        })

    # Determine overall parent deliverable complexity
    if total_hours >= 25.0:
        parent_comp = COMPLEXITY_OPTIONS[5]
    elif total_hours >= 15.0:
        parent_comp = COMPLEXITY_OPTIONS[4]
    elif total_hours >= 6.0:
        parent_comp = COMPLEXITY_OPTIONS[3]
    elif total_hours >= 3.0:
        parent_comp = COMPLEXITY_OPTIONS[2]
    else:
        parent_comp = COMPLEXITY_OPTIONS[1]

    return {
        "parent_title": parent_title,
        "total_hours": round(total_hours, 1),
        "parent_complexity": parent_comp,
        "raw_notes": notes_text.strip(),
        "subtasks": subtasks
    }


def find_task_in_database(client: NotionClient, db_id: str, identifier: str) -> Optional[Dict[str, Any]]:
    """Locates a task in the Notion database by ID or fuzzy title match."""
    clean_id = db_id.replace("-", "")
    clean_ident = identifier.replace("-", "").strip().lower()

    # Direct fetch if 32 hex chars
    if len(clean_ident) == 32:
        try:
            return client.get_page(clean_ident)
        except Exception:
            pass

    items = client.query_database(clean_id, page_size=100)
    for it in items:
        it_id = it.get("id", "").replace("-", "").lower()
        if it_id == clean_ident:
            return it

    ident_lower = identifier.strip().lower()
    for it in items:
        props = it.get("properties", {})
        title_objs = props.get("Task Name", {}).get("title", [])
        title = title_objs[0].get("plain_text", "").strip().lower() if title_objs else ""
        if title == ident_lower:
            return it

    for it in items:
        props = it.get("properties", {})
        title_objs = props.get("Task Name", {}).get("title", [])
        title = title_objs[0].get("plain_text", "").strip().lower() if title_objs else ""
        if ident_lower in title:
            return it

    return None


def apply_user_decomposition_to_notion(
    client: NotionClient,
    db_id: str,
    parent_task_item: Dict[str, Any],
    plan: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Creates human-defined subtasks in Notion with native Parent Task relations,
    updates parent task hours/complexity, and appends the user's execution plan & checklist.
    """
    clean_db_id = db_id.replace("-", "")
    parent_id = parent_task_item.get("id", "").replace("-", "")
    parent_props = parent_task_item.get("properties", {})
    parent_title = parent_props.get("Task Name", {}).get("title", [{}])[0].get("plain_text", "Deliverable")

    # 1. Update Parent Task Properties
    client.update_page(parent_id, {
        "Complexity": {"select": {"name": plan["parent_complexity"]}},
        "Estimated Hours": {"number": plan["total_hours"]}
    })

    # 2. Create Linked Subtasks in Notion Database
    created_subtasks = []
    for st in plan["subtasks"]:
        subtask_props = {
            "Task Name": {"title": [{"text": {"content": st["title"]}}]},
            "Priority": {"select": {"name": st["priority"]}},
            "Status": {"status": {"name": "To Do"}},
            "Estimated Hours": {"number": st["estimated_hours"]},
            "Complexity": {"select": {"name": st["complexity"]}},
            "Team / Pod": {"select": {"name": st["team"]}},
            "Action Required By": {"select": {"name": "Assignee (In Flight)"}},
            "Parent Task": {"relation": [{"id": parent_id}]},
            "Task Details": {"rich_text": [{"text": {"content": f"🎯 Criteria: {st['acceptance_criteria']}"}}]}
        }
        res = client._request("POST", "/pages", {
            "parent": {"database_id": clean_db_id},
            "properties": subtask_props,
            "icon": {"type": "emoji", "emoji": "🔹"}
        })
        created_subtasks.append({
            "id": res.get("id"),
            "title": st["title"],
            "url": res.get("url") or f"https://notion.so/{res.get('id', '').replace('-', '')}"
        })

    # 3. Append Notes, Pillars & Interactive Checklist into Parent Page Body
    doc_lines = [
        "---",
        "## 📝 Implementation Notes & Major Pillars",
        plan["raw_notes"],
        "",
        "## 🧩 Decomposed Subtasks Checklist",
    ]
    for st in plan["subtasks"]:
        doc_lines.append(
            f"- [ ] **{st['short_title']}** ({st['estimated_hours']}h • {st['team']} • {st['priority']}): {st['pillar']}"
        )

    doc_lines.extend([
        "",
        "## 🛡️ Definition of Done",
        "- [ ] All linked subtasks completed and verified",
        "- [ ] Acceptance criteria signed off by task owner"
    ])

    client.append_markdown(parent_id, "\n".join(doc_lines))

    return {
        "parent_id": parent_id,
        "parent_title": parent_title,
        "parent_complexity": plan["parent_complexity"],
        "total_hours": plan["total_hours"],
        "subtasks_created": len(created_subtasks),
        "subtasks": created_subtasks
    }
