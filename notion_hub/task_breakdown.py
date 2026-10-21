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
    """Generates a professional, modular architectural implementation plan."""
    t_lower = (task_title + " " + task_details).lower()
    if any(k in t_lower for k in ["reception", "visitor", "kiosk", "gate", "front desk"]):
        return (
            "Major Pillars:\n\n"
            "1. Architecture & Security Schemas\n"
            "- Visitor Schema & NDA Models (2.5h, Backend, P2) — Design Postgres tables, indexes, and encrypted storage for visitor logs & NDA records\n"
            "- Overstay Event Alert Worker (2.0h, Backend, P2) — Implement automated background worker tracking visit durations and triggering alerts\n\n"
            "2. Kiosk Experience & Hardware Drivers\n"
            "- Tablet Touchscreen Check-In UI (3.5h, Frontend, P2) — Build responsive self-registration kiosk with webcam photo capture\n"
            "- Thermal Badge Printer Integration (2.5h, Frontend, P3) — Generate and dispatch ESC/POS print jobs with scannable QR badge\n\n"
            "3. Hardening & Emergency Protocol\n"
            "- Host Google Chat Alert Service (2.0h, Backend, P2) — Dispatch real-time Card v2 notification to host employee upon visitor sign-in\n"
            "- Emergency Evacuation Headcount Roster (1.5h, QA & Security, P3) — 1-click real-time exportable headcount roster for building safety marshals"
        )
    elif any(k in t_lower for k in ["video", "film", "youtube", "media", "kotak", "bank"]):
        return (
            "Major Pillars:\n\n"
            "1. Narrative & Visual Storyboarding\n"
            "- Narrative Script & Compliance Review (2.0h, Product, P2) — Finalize messaging, hook, and regulatory compliance clearance\n"
            "- Visual Storyboard & Shot List (2.5h, Design, P3) — Produce scene-by-scene framing guide with corporate banking motifs\n\n"
            "2. Video Assembly & Motion Graphics\n"
            "- A-Roll Assembly & Multitrack Sync (3.5h, Design, P2) — Assemble rough timeline cut with synchronized dialogue and B-roll\n"
            "- Brand Motion Graphics & Lower-Thirds (3.0h, Design, P3) — Render animated brand title cards, lower-thirds, and transitions\n\n"
            "3. Sound Design & Master Delivery\n"
            "- Dialogue Balancing & Master Mix (1.5h, Design, P3) — Normalize vocal clarity to broadcast loudness standards\n"
            "- High-Bitrate Multi-Platform Export (1.5h, DevOps & Infra, P4) — Render optimized 4K master and social cuts"
        )
    elif any(k in t_lower for k in ["dashboard", "metric", "report", "upload", "chart", "form"]):
        return (
            "Major Pillars:\n\n"
            "1. Ingestion & Calculation Engine\n"
            "- Multi-Format File Intake Endpoint (3.0h, Backend, P2) — Build resilient upload endpoint with schema validation and sanitization\n"
            "- Metric Rollup & Weighted Caching (3.0h, Backend, P2) — Implement aggregation formulas, percentile ranking, and in-memory cache\n\n"
            "2. Visualization & Interactive Controls\n"
            "- Glassmorphic KPI Grid & Charts (3.5h, Frontend, P2) — Render dynamic Chart.js visualizations with responsive breakpoints\n"
            "- Column Filter & CSV Exporter (2.0h, Frontend, P3) — Implement multi-horizon filtering, search, and client-side data export\n\n"
            "3. Security & Cross-Device Hardening\n"
            "- Role-Based Scope Permissions (2.0h, QA & Security, P3) — Verify RBAC restrictions, sensitive metric masking, and audit logging\n"
            "- Cross-Browser Layout Polish (1.5h, Frontend, P4) — Verify responsive behavior across mobile, tablet, and desktop viewports"
        )
    else:
        return (
            f"Major Pillars:\n\n"
            f"1. Core Architecture & Specifications\n"
            f"- Data Schema & API Contract (3.0h, Backend, P2) — Define normalized database entities, migrations, and CRUD API specs for {task_title}\n"
            f"- Core Logic Engine & Validation (3.0h, Backend, P2) — Implement core business logic, input validation, and structured error handling\n\n"
            f"2. Interactive UI & User Workflow\n"
            f"- Responsive Component Views (3.5h, Frontend, P2) — Build interactive dashboard views, forms, and responsive data tables\n"
            f"- User Feedback & Loading States (2.0h, Frontend, P3) — Implement progress toasts, micro-interactions, and optimistic state updates\n\n"
            f"3. Hardening, QA & Delivery\n"
            f"- Integration & Edge Case Test Suite (2.0h, QA & Security, P3) — Write automated test coverage for critical paths and failure modes\n"
            f"- CI/CD Pipeline & Staging Verification (1.5h, DevOps & Infra, P4) — Deploy to staging environment, verify health check, and tag release"
        )


def generate_breakdown_notes_with_gemini(
    task_title: str,
    task_details: str = "",
    api_key: Optional[str] = None,
    model: str = "gemini-1.5-flash"
) -> str:
    """
    Uses Google Gemini to draft a high-caliber technical implementation plan,
    major architectural pillars, and sized subtasks.
    """
    key = api_key or os.getenv("GEMINI_API_KEY", "").strip()

    if not key:
        return generate_smart_fallback_notes(task_title, task_details)

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

    prompt = (
        f"You are a Principal Software Architect and Technical Lead.\n"
        f"Break down the project deliverable into a clean, modular, and professional engineering plan.\n\n"
        f"Deliverable: '{task_title}'\n"
        f"Context / Notes: '{task_details or 'Full-stack production feature'}'\n\n"
        f"Format your response strictly using this Markdown template (do NOT wrap in code blocks):\n\n"
        f"Major Pillars:\n\n"
        f"1. <Pillar 1 Name>\n"
        f"- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Crisp Acceptance Criteria / Definition of Done>\n"
        f"- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Crisp Acceptance Criteria / Definition of Done>\n\n"
        f"2. <Pillar 2 Name>\n"
        f"- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Crisp Acceptance Criteria / Definition of Done>\n"
        f"- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Crisp Acceptance Criteria / Definition of Done>\n\n"
        f"3. <Pillar 3 Name>\n"
        f"- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Crisp Acceptance Criteria / Definition of Done>\n\n"
        f"Strict Guidelines for Senior-Engineer Quality:\n"
        f"1. Subtask Title MUST be 3 to 6 words maximum. Keep it clean and punchy (e.g. 'Visitor Schema & NDA Models', NOT 'Design visitor log database models, NDA agreements and migration scripts').\n"
        f"2. NEVER prefix or repeat the parent deliverable name in the subtask title.\n"
        f"3. Estimated hours must be realistic: between 1.5h and 4.0h each (e.g., 2h, 2.5h, 3.5h).\n"
        f"4. Pod MUST be one of: Backend, Frontend, DevOps & Infra, Design, QA & Security, Product.\n"
        f"5. Priority MUST be one of: P1, P2, P3, P4.\n"
        f"6. Acceptance criteria after the em-dash '—' must be exactly one clear, technical sentence stating what makes it Done.\n"
        f"7. Provide 4 to 6 total subtasks across 2 to 3 major pillars.\n"
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
            "temperature": 0.35,
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

        # Separate title from acceptance criteria using em-dash '—', '--', or ':'
        criteria = ""
        if "—" in raw_text:
            parts = raw_text.split("—", 1)
            raw_title, criteria = parts[0].strip(), parts[1].strip()
        elif " -- " in raw_text:
            parts = raw_text.split(" -- ", 1)
            raw_title, criteria = parts[0].strip(), parts[1].strip()
        elif ":" in raw_text and not re.search(r'\b(?:http|https):', raw_text):
            parts = raw_text.split(":", 1)
            raw_title, criteria = parts[0].strip(), parts[1].strip()
        else:
            raw_title = raw_text

        # Clean subtask title by removing parenthetical metadata like "(3h, Backend, P2)"
        clean_title = re.sub(r'[\(\[].*?[\)\]]', '', raw_title).strip()
        clean_title = re.sub(r'\s+', ' ', clean_title).strip(' -:•')

        if not clean_title:
            clean_title = raw_title[:45].strip(' -:•')

        # Clean criteria string
        criteria = re.sub(r'[\(\[].*?[\)\]]', '', criteria).strip(' -:•')
        if not criteria:
            criteria = f"Verified implementation of {clean_title} under {current_pillar}."

        # Determine subtask complexity
        if hours <= 2.0:
            comp = "⭐ 1 - Trivial"
        elif hours <= 4.0:
            comp = "⭐⭐ 2 - Simple"
        else:
            comp = "⭐⭐⭐ 3 - Moderate"

        subtasks.append({
            "title": clean_title,
            "short_title": clean_title,
            "estimated_hours": hours,
            "priority": prio,
            "team": pod,
            "complexity": comp,
            "pillar": current_pillar,
            "acceptance_criteria": criteria
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
