"""
Human-Driven Task Decomposition & Notes Breakdown Engine.
Allows developers to select a Notion task and provide their own execution notes,
major pillars, and implementation steps. Decomposes the notes into individual subtasks
linked with native Parent-Child relations to the original task.
"""
import json
import os
import re
import urllib.request
import urllib.error
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


def generate_smart_fallback_notes(task_title: str, task_details: str = "") -> str:
    """Generates an architectural implementation plan when offline or without API key."""
    t_lower = (task_title + " " + task_details).lower()
    if any(k in t_lower for k in ["reception", "visitor", "kiosk", "gate", "front desk"]):
        return (
            "Major Pillars:\n"
            "1. Core Visitor Architecture & Security Schema\n"
            "- Design visitor log database models, NDA agreements & migration scripts (3.0h, Backend, P2) — Schema migrations and indexes applied\n"
            "- Implement host employee automated overstay notification trigger (2.5h, Backend, P3) — Webhook triggers after 4h threshold\n"
            "\n"
            "2. Tablet Kiosk & Visitor UX\n"
            "- Build touchscreen self-registration interface with photo capture (3.5h, Frontend, P2) — Camera preview and instant registration\n"
            "- Integrate thermal badge printer for QR visitor passes (2.5h, Frontend, P3) — Print job dispatched upon sign-in\n"
            "\n"
            "3. Emergency Protocol & Audit Logging\n"
            "- Real-time host notification dispatch via Google Chat (2.0h, Backend, P2) — Host alerted with visitor snapshot\n"
            "- One-click evacuation headcount roster for security personnel (1.5h, QA & Security, P4) — Instant exportable headcount table"
        )
    elif any(k in t_lower for k in ["video", "film", "youtube", "media", "kotak", "bank"]):
        return (
            "Major Pillars:\n"
            "1. Scripting & Visual Storyboarding\n"
            "- Finalize narrative script, hook and compliance sign-off (2.0h, Product, P2) — Approved narrative script\n"
            "- Create visual storyboard and shot list with banking visual motifs (2.5h, Design, P3) — Shot breakdown with timing\n"
            "\n"
            "2. Video Assembly & Motion Graphics\n"
            "- Assemble A-roll interview footage and sync multitrack audio (3.5h, Design, P2) — Rough cut timeline completed\n"
            "- Build 2D motion graphics, brand title cards and lower-thirds (3.0h, Design, P3) — Brand kit animations rendered\n"
            "\n"
            "3. Sound Design & Multi-Platform Mastering\n"
            "- Audio balancing, dialogue clarity normalization and music bed (1.5h, Design, P3) — Broadcast standard loudness\n"
            "- High-bitrate 4K rendering and YouTube/social cuts export (1.5h, DevOps & Infra, P4) — Multi-aspect ratio deliverables"
        )
    elif any(k in t_lower for k in ["dashboard", "metric", "report", "upload", "chart"]):
        return (
            "Major Pillars:\n"
            "1. Data Ingestion & Calculation Engine\n"
            "- Build resilient file upload endpoint with schema validation (3.0h, Backend, P2) — Multi-format file intake\n"
            "- Implement metric rollup formulas, weighted scores and caching (3.0h, Backend, P2) — Sub-100ms analytics retrieval\n"
            "\n"
            "2. Responsive Visualization & Controls\n"
            "- Design glassmorphic KPI cards grid and interactive charts (3.5h, Frontend, P2) — Dynamic Chart.js visualizations\n"
            "- Implement date range filters, column search and CSV exporter (2.5h, Frontend, P3) — Instant filtering & export\n"
            "\n"
            "3. Cross-Browser QA & Permission Scopes\n"
            "- Role-based view access control and data redaction (2.0h, QA & Security, P3) — RBAC permissions verified\n"
            "- Responsive viewport polish across mobile, tablet and desktop (1.5h, Frontend, P4) — Zero layout shifts"
        )
    else:
        return (
            f"Major Pillars:\n"
            f"1. Core Architecture & Backend Services\n"
            f"- Define domain data models, validation schemas and API endpoints for {task_title} (3.5h, Backend, P2) — Complete CRUD API specs\n"
            f"- Implement business logic engine, error handling and event logging (3.0h, Backend, P2) — Resilient error handling\n"
            f"\n"
            f"2. User Interface & Interactive Experience\n"
            f"- Build responsive UI components, state management and data tables (3.5h, Frontend, P2) — Clean interactive workflow\n"
            f"- Add user feedback toasts, progress indicators and loading states (2.0h, Frontend, P3) — Intuitive micro-interactions\n"
            f"\n"
            f"3. Verification, Security & Deployment\n"
            f"- Write automated unit and integration test suite (2.0h, QA & Security, P3) — 85%+ coverage on critical paths\n"
            f"- Configure CI/CD deployment pipeline and monitoring alerts (1.5h, DevOps & Infra, P4) — Staging verification complete"
        )


def generate_breakdown_notes_with_gemini(
    task_title: str,
    task_details: str = "",
    api_key: Optional[str] = None,
    model: str = "gemini-1.5-flash"
) -> str:
    """
    Uses Google Gemini (Gemini 1.5 Flash / 2.0 Flash) to draft an implementation plan,
    major architectural pillars, and sized subtask steps for a deliverable.
    Falls back gracefully to smart domain synthesis if no key is provided.
    """
    key = api_key or os.getenv("GEMINI_API_KEY", "").strip()

    if not key:
        return generate_smart_fallback_notes(task_title, task_details)

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

    prompt = (
        f"You are an expert technical product manager and software architect.\n"
        f"Break down the following project deliverable into a concrete, actionable implementation plan:\n"
        f"Deliverable Title: '{task_title}'\n"
        f"Context / Details: '{task_details or 'None provided'}'\n\n"
        f"Format your response strictly using this format (do NOT wrap in markdown code blocks):\n"
        f"Major Pillars:\n"
        f"1. <Pillar 1 Name>\n"
        f"- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Acceptance criteria>\n"
        f"- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Acceptance criteria>\n\n"
        f"2. <Pillar 2 Name>\n"
        f"- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Acceptance criteria>\n"
        f"- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Acceptance criteria>\n\n"
        f"3. <Pillar 3 Name>\n"
        f"- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Acceptance criteria>\n\n"
        f"Requirements:\n"
        f"- Subtasks must be concrete, technical and sized (between 1.0h and 5.0h each, e.g. 2h, 3.5h).\n"
        f"- Pod must be one of: Backend, Frontend, DevOps & Infra, Design, QA & Security, Product.\n"
        f"- Priority must be one of: P1, P2, P3, P4.\n"
        f"- Include 4 to 6 total subtasks across 2 to 3 major pillars.\n"
    )

    req_body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1024
        }
    }

    try:
        data = json.dumps(req_body).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    raw_text = parts[0].get("text", "").strip()
                    # Strip markdown code fences if model enclosed it
                    raw_text = re.sub(r'^```(?:markdown)?\s*', '', raw_text)
                    raw_text = re.sub(r'\s*```$', '', raw_text)
                    return raw_text.strip()
    except Exception as e:
        print(f"⚠️ Gemini API note: {e}. Using smart architectural synthesizer.")

    return generate_smart_fallback_notes(task_title, task_details)


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
