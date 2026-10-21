"""
AI-Powered Task Sizing, Decomposition, and Subtask Generation Engine.
Decomposes complex deliverables into sized, prioritized subtasks (1-5 ⭐ complexity),
establishes native parent-subtask relations, and enriches parent Notion pages
with interactive Definition of Done & Acceptance Criteria checklists.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from .client import NotionClient

# Standardized Select Options matching Database Schema 3fff1bcff9b881be9e4fd3df8f014a52
COMPLEXITY_OPTIONS = {
    1: "⭐ 1 - Trivial",
    2: "⭐⭐ 2 - Simple",
    3: "⭐⭐⭐ 3 - Moderate",
    4: "⭐⭐⭐⭐ 4 - Complex",
    5: "⭐⭐⭐⭐⭐ 5 - Epic"
}

CATEGORY_OPTIONS = {
    "product": "🚀 Product & Feature",
    "engineering": "🛠️ Engineering & Tech",
    "design": "🎨 UI / UX Design",
    "growth": "📈 Growth & Marketing",
    "operations": "⚙️ Operations & Chores",
    "research": "💡 Research & Strategy"
}

POD_OPTIONS = [
    "Frontend",
    "Backend",
    "DevOps & Infra",
    "Design",
    "Product",
    "QA & Security"
]

EISENHOWER_OPTIONS = {
    "q1": "Q1: Do First (Urgent & Important)",
    "q2": "Q2: Schedule (Important & Not Urgent)",
    "q3": "Q3: Delegate (Urgent & Not Important)",
    "q4": "Q4: Eliminate (Low Urgency & Low Impact)"
}

# Domain archetypes tailored to project deliverables
DOMAIN_ARCHETYPES = {
    "sis_marks": {
        "domain": "School SIS / Examination & Marks Management",
        "keywords": ["sis", "marks", "templatization", "grade", "report card", "exam", "grading"],
        "parent_complexity": 4,
        "parent_pod": "Backend",
        "parent_category": "engineering",
        "eisenhower": "q1",
        "overview": "Implement a standardized, configurable SIS examination and grading templatization system supporting batch mark entry, automatic grade boundaries, validation, and PDF export.",
        "subtasks": [
            ("Evaluation Scheme & Grade Boundary Modeling", 3.0, "P2 - High", "Backend", "⭐ 1 - Trivial", "Define schema for assessment types, weightages, grade cutoffs, and pass/fail thresholds."),
            ("Mark Entry Grid UI & Real-Time Calculation Engine", 4.0, "P2 - High", "Frontend", "⭐⭐ 2 - Simple", "Build responsive grid table with keyboard navigation, live percentage computation, and autosave."),
            ("Bulk CSV / Excel Import & Validation Parser", 3.0, "P3 - Medium", "Backend", "⭐⭐ 2 - Simple", "Implement asynchronous bulk upload parser with row-level error reporting for invalid marks."),
            ("Report Card PDF Templatization & Export Pipeline", 3.5, "P2 - High", "Backend", "⭐⭐ 2 - Simple", "Design printable HTML/PDF report card layout with dynamic school crest, remarks, and performance charts."),
            ("Audit Trail, Verification & Role-Based Publishing Lock", 2.0, "P3 - Medium", "QA & Security", "⭐ 1 - Trivial", "Add verification step where teacher submits marks and principal/admin signs off before publishing.")
        ]
    },
    "fees_management": {
        "domain": "Institutional Fees Accountability & Financial Reconciliation",
        "keywords": ["fee", "fees", "accountability", "handling", "tuition", "payment", "reconciliation", "invoice", "receipt"],
        "parent_complexity": 4,
        "parent_pod": "Backend",
        "parent_category": "engineering",
        "eisenhower": "q1",
        "overview": "Architect an end-to-end fee structure, tracking, and reconciliation engine ensuring zero accounting leakage, automated payment ledger balancing, and defalcation audit logs.",
        "subtasks": [
            ("Fee Head Catalog & Installment Schedule Definition", 3.0, "P2 - High", "Backend", "⭐⭐ 2 - Simple", "Model quarterly/monthly fee categories, transport/hostel surcharges, and discount structures."),
            ("Payment Gateway Webhook & Dual-Entry Ledger Reconciliation", 4.0, "P1 - Urgent", "Backend", "⭐⭐ 2 - Simple", "Implement idempotent payment webhook listener, duplicate-charge prevention, and ledger journal entries."),
            ("Defaulter Flagging, Aging Alerts & Concession Approvals", 3.0, "P2 - High", "Backend", "⭐⭐ 2 - Simple", "Automatic cron flagging overdue accounts (>15d, >30d), calculating late fines, and concession workflows."),
            ("Automated Digital Receipt Generator & GST Invoice PDF", 3.0, "P3 - Medium", "Backend", "⭐⭐ 2 - Simple", "Produce tamper-evident digital fee receipts with unique voucher numbers and SMS/WhatsApp delivery."),
            ("Finance Executive Dashboard & Daily Cash Flow Balancing", 2.5, "P3 - Medium", "Frontend", "⭐⭐ 2 - Simple", "Visual breakdown of collected vs pending dues, gateway fee deductions, and bank deposit reconciliations.")
        ]
    },
    "reception_system": {
        "domain": "Reception & Visitor Management System",
        "keywords": ["reception", "visitor", "front desk", "guest", "check-in", "pass", "badge"],
        "parent_complexity": 3,
        "parent_pod": "Product",
        "parent_category": "product",
        "eisenhower": "q2",
        "overview": "Deliver an automated Front Desk Reception kiosk allowing visitor pre-registration, QR code badge printing, instant host alerts, and real-time security logging.",
        "subtasks": [
            ("Visitor Self Check-In Kiosk & Purpose Selection UI", 3.0, "P2 - High", "Frontend", "⭐⭐ 2 - Simple", "Clean tablet interface for visitor sign-in, NDA acceptance, photo capture, and department selection."),
            ("Instant Host Notification Dispatch via Chat & SMS", 2.5, "P2 - High", "Backend", "⭐⭐ 2 - Simple", "Webhook dispatch to Google Chat / SMS alerting host employee with 1-click 'Allow' or 'Please wait' button."),
            ("Visitor Log Database Schema & Overstay Monitoring", 3.0, "P3 - Medium", "Backend", "⭐⭐ 2 - Simple", "Real-time ledger tracking active on-premise visitors, entry timestamps, and overstay threshold alerts."),
            ("QR Digital Pass & Thermal Printer Integration", 2.5, "P3 - Medium", "Frontend", "⭐⭐ 2 - Simple", "Generate scannable QR badge with visitor name, host name, valid hours, and thermal printer formatting."),
            ("Emergency Evacuation Headcount Sheet & Security Sign-Off", 2.0, "P4 - Low", "QA & Security", "⭐ 1 - Trivial", "One-click evacuation roster generating live list of all currently checked-in visitors and contractors.")
        ]
    },
    "erp_sis": {
        "domain": "Enterprise ERP / SIS Workflow Audit & Gap Analysis",
        "keywords": ["erp", "sis go through", "go through", "audit", "system review", "walkthrough", "architecture review"],
        "parent_complexity": 3,
        "parent_pod": "Product",
        "parent_category": "research",
        "eisenhower": "q2",
        "overview": "Perform a structured architectural and functional deep-dive across all ERP/SIS modules, identifying data sync latency, UX bottlenecks, and module dependencies.",
        "subtasks": [
            ("Module Inventory & Critical User Journey Mapping", 3.0, "P2 - High", "Product", "⭐⭐ 2 - Simple", "Document end-to-end user journeys for Administrators, Teachers, Students, and Accountants."),
            ("Data Schema Normalization & Entity Relationship Audit", 3.5, "P2 - High", "Backend", "⭐⭐ 2 - Simple", "Inspect database normalization, foreign key constraints, indexing bottlenecks, and legacy schemas."),
            ("Frontend Latency Profiling & Form Usability Audit", 2.5, "P3 - Medium", "Frontend", "⭐⭐ 2 - Simple", "Benchmark page load speeds across 3G/broadband connections and catalog form validation friction points."),
            ("Role-Based Access Control (RBAC) & Security Policy Audit", 2.5, "P2 - High", "QA & Security", "⭐⭐ 2 - Simple", "Review permission inheritance, privilege escalation risks, and sensitive student record encryption."),
            ("Executive Gap Analysis Matrix & Sprint Prioritization Roadmap", 2.0, "P3 - Medium", "Product", "⭐ 1 - Trivial", "Consolidate findings into a prioritized RICE matrix with actionable development sprints.")
        ]
    },
    "video_editing": {
        "domain": "Automated Video Production & Claude Code Tooling",
        "keywords": ["video editing", "claude code", "cut", "footage", "clip", "subtitles", "render", "ffmpeg"],
        "parent_complexity": 3,
        "parent_pod": "Backend",
        "parent_category": "engineering",
        "eisenhower": "q2",
        "overview": "Build an automated video editing script and skill utilizing Claude Code CLI, FFmpeg, and Whisper AI for automated clipping, pacing cuts, and caption synchronization.",
        "subtasks": [
            ("Video Processing Scripting & FFmpeg Automation Wrapper", 3.0, "P2 - High", "Backend", "⭐⭐ 2 - Simple", "Python wrapper automating scene detection, loss-less splitting, audio extraction, and speed ramping."),
            ("Claude Code Prompt Engineering for Edit Decision Lists (EDL)", 3.0, "P2 - High", "Backend", "⭐⭐ 2 - Simple", "Develop prompts that parse raw transcripts and generate structured JSON timelines of keep/cut ranges."),
            ("Automated Dynamic Caption Burn-in & Visual Transitions", 3.0, "P3 - Medium", "Backend", "⭐⭐ 2 - Simple", "Integrate Whisper subtitle alignment with stylized Word-by-Word animated subtitles and zoom transitions."),
            ("Sample Benchmark Suite & Automated Render Quality Check", 2.0, "P3 - Medium", "QA & Security", "⭐ 1 - Trivial", "Test pipeline against 3 varied raw video files, verifying audio sync, color space, and encoding bitrate.")
        ]
    },
    "meta_video": {
        "domain": "Social Media Ad Creative & Meta Video Pipeline",
        "keywords": ["meta", "ad", "lineup", "creative", "commercial", "reels", "short", "hook", "storyboard"],
        "parent_complexity": 3,
        "parent_pod": "Design",
        "parent_category": "growth",
        "eisenhower": "q2",
        "overview": "Execute a high-converting Meta Video Ad series with tested visual hooks, high-retention pacing, and multiple format exports optimized for Instagram & Facebook feeds.",
        "subtasks": [
            ("3-Second Hook Ideation & Storyboard Scripting", 2.5, "P2 - High", "Design", "⭐⭐ 2 - Simple", "Script 3 alternative opening hooks (Problem/Agitate, Curious Stat, Pattern Interrupt) with visuals."),
            ("Footage Assembly, Audio Pacing & Jump-Cut Sequencing", 3.5, "P2 - High", "Design", "⭐⭐ 2 - Simple", "Rough cut timeline optimized for sub-60s retention with sound effects and beat matching."),
            ("High-Pacing Motion Graphics, Callout Stickers & Brand Overlay", 3.0, "P2 - High", "Design", "⭐⭐ 2 - Simple", "Add animated kinetic typography, social proof badges, and clear end-screen CTA banners."),
            ("Multi-Ratio Master Export (9:16 Vertical, 1:1 Square, 16:9)", 2.0, "P3 - Medium", "Design", "⭐ 1 - Trivial", "Produce optimized H.264 exports with verified platform bitrate compression and safe-zone margins.")
        ]
    },
    "carousel_generation": {
        "domain": "AI-Powered Social Carousel Generation",
        "keywords": ["carousel", "slides", "linkedin carousel", "instagram carousel", "slide generation"],
        "parent_complexity": 3,
        "parent_pod": "Design",
        "parent_category": "growth",
        "eisenhower": "q2",
        "overview": "Implement a repeatable AI pipeline generating high-engagement, multi-slide educational carousels with compelling narrative arcs and export-ready visual layouts.",
        "subtasks": [
            ("Carousel Narrative Framework & Hook Copy Drafting", 2.0, "P2 - High", "Product", "⭐ 1 - Trivial", "Write 8-slide structured narrative: Hook Slide, Problem, 3 Core Pillars, Case Study, and Action CTA."),
            ("Claude Prompt Workflow for Slide-by-Slide Content Structuring", 2.5, "P2 - High", "Backend", "⭐⭐ 2 - Simple", "Prompt templates producing clean JSON output containing headline, body, bullet highlights, and visual cue."),
            ("Figma / HTML-to-Image Visual Template & Typography System", 3.0, "P3 - Medium", "Design", "⭐⭐ 2 - Simple", "Create reusable high-contrast dark/light design system with progress bar, author pill, and iconography."),
            ("Automated Multi-Slide PDF / PNG Export & Verification", 1.5, "P3 - Medium", "QA & Security", "⭐ 1 - Trivial", "Automate lossless export of slides with strict dimension checking (1080x1350 4:5 portrait).")
        ]
    },
    "activity_tracker": {
        "domain": "Activity & Audit Trail Tracking Engine",
        "keywords": ["activity tracker", "activity", "event log", "telemetry", "tracking system", "time tracker"],
        "parent_complexity": 3,
        "parent_pod": "Backend",
        "parent_category": "engineering",
        "eisenhower": "q2",
        "overview": "Construct an event telemetry and activity timeline engine logging user actions, state mutations, and developer contributions with real-time stream aggregation.",
        "subtasks": [
            ("Event Ingestion API & Flexible Activity Schema Modeling", 3.0, "P2 - High", "Backend", "⭐⭐ 2 - Simple", "Model event envelopes (actor, action, entity, metadata, timestamp) with high-throughput ingestion endpoint."),
            ("Stream Processing & Daily Rollup Aggregation Pipeline", 3.5, "P2 - High", "Backend", "⭐⭐ 2 - Simple", "Aggregate micro-events into daily contributor summaries, heatmaps, and velocity metrics."),
            ("Interactive Activity Timeline UI & Filter Feed", 3.0, "P3 - Medium", "Frontend", "⭐⭐ 2 - Simple", "Build searchable, filterable timeline stream with user avatars, badge tags, and expandable JSON details."),
            ("Data Retention Policy, Indexing & Audit Log Security", 2.0, "P3 - Medium", "DevOps & Infra", "⭐ 1 - Trivial", "Implement partitioned indexing, 90-day cold storage archival, and tamper-evident append-only guarantees.")
        ]
    },
    "default_system": {
        "domain": "Full-Stack Software Architecture & Platform",
        "keywords": ["system", "platform", "backend", "portal", "engine", "service", "infrastructure"],
        "parent_complexity": 3,
        "parent_pod": "Backend",
        "parent_category": "engineering",
        "eisenhower": "q2",
        "overview": "Architect, implement, and verify the end-to-end software module following domain-driven design, robust API schemas, and automated testing.",
        "subtasks": [
            ("Architecture Blueprint & Data Schema Design", 3.0, "P2 - High", "Backend", "⭐⭐ 2 - Simple", "Entity relationship models, interface contracts, and database migration scripts."),
            ("Core Business Logic & API Endpoint Implementation", 4.0, "P2 - High", "Backend", "⭐⭐ 2 - Simple", "Implement primary service layer, request validation, error handlers, and business rules."),
            ("Responsive User Interface & Interactive State Handling", 3.5, "P3 - Medium", "Frontend", "⭐⭐ 2 - Simple", "Build responsive views, loading skeletons, error states, and optimistic UI updates."),
            ("Integration Testing, RBAC Security & Deployment Verification", 2.0, "P3 - Medium", "QA & Security", "⭐ 1 - Trivial", "Write automated tests, verify permission matrices, and perform staging sanity runs.")
        ]
    },
    "default_generic": {
        "domain": "General Deliverable Execution",
        "keywords": [],
        "parent_complexity": 2,
        "parent_pod": "Product",
        "parent_category": "product",
        "eisenhower": "q2",
        "overview": "Execute deliverable systematically from requirements definition through development, quality review, and documentation handoff.",
        "subtasks": [
            ("Requirements Scoping & Acceptance Criteria Definition", 2.0, "P2 - High", "Product", "⭐ 1 - Trivial", "Document functional boundaries, acceptance criteria, dependencies, and deliverables."),
            ("Primary Deliverable Build & Implementation", 4.0, "P2 - High", "Backend", "⭐⭐ 2 - Simple", "Core implementation work according to technical specification."),
            ("Quality Review, Verification & Edge Case Testing", 2.5, "P3 - Medium", "QA & Security", "⭐⭐ 2 - Simple", "Test validation against boundary conditions and verify cross-platform functionality."),
            ("Documentation, User Guide & Team Handoff", 1.5, "P4 - Low", "Operations", "⭐ 1 - Trivial", "Create usage documentation, release notes, and demonstrate to stakeholders.")
        ]
    }
}


def match_domain_archetype(title: str, description: str = "") -> Dict[str, Any]:
    """Matches task title and context against specialized domain archetypes."""
    text = f"{title.lower()} {description.lower()}"

    # Priority matches for specific domains
    for key, archetype in DOMAIN_ARCHETYPES.items():
        if key in ["default_system", "default_generic"]:
            continue
        for kw in archetype["keywords"]:
            if kw in text:
                return archetype

    if any(k in text for k in ["system", "platform", "backend", "api", "engine", "service", "portal"]):
        return DOMAIN_ARCHETYPES["default_system"]

    return DOMAIN_ARCHETYPES["default_generic"]


def plan_task_decomposition(title: str, description: str = "") -> Dict[str, Any]:
    """
    Computes full AI decomposition and sizing plan for a deliverable:
    - Sized subtasks with estimated hours and individual complexity
    - Total estimated hours for the deliverable
    - Overall deliverable complexity (1 to 5 ⭐)
    - Recommended Pod and Category
    """
    archetype = match_domain_archetype(title, description)
    subtasks_raw = archetype["subtasks"]

    subtasks = []
    total_hours = 0.0

    for sub_title, hours, prio, pod, comp, criteria in subtasks_raw:
        full_sub_title = f"{title} — {sub_title}"
        total_hours += hours
        subtasks.append({
            "title": full_sub_title,
            "short_title": sub_title,
            "estimated_hours": hours,
            "priority": prio,
            "team": pod,
            "complexity": comp,
            "acceptance_criteria": criteria,
            "category": CATEGORY_OPTIONS.get(archetype["parent_category"], "🛠️ Engineering & Tech")
        })

    # Determine parent complexity based on total hours
    if total_hours >= 25.0:
        parent_comp_num = 5
    elif total_hours >= 15.0:
        parent_comp_num = 4
    elif total_hours >= 6.0:
        parent_comp_num = 3
    elif total_hours >= 3.0:
        parent_comp_num = 2
    else:
        parent_comp_num = 1

    parent_comp_str = COMPLEXITY_OPTIONS[parent_comp_num]

    return {
        "domain": archetype["domain"],
        "overview": archetype["overview"],
        "parent_complexity": parent_comp_str,
        "parent_complexity_num": parent_comp_num,
        "parent_est_hours": round(total_hours, 1),
        "parent_team": archetype["parent_pod"],
        "parent_category": CATEGORY_OPTIONS.get(archetype["parent_category"], "🛠️ Engineering & Tech"),
        "parent_eisenhower": EISENHOWER_OPTIONS.get(archetype["eisenhower"], "Q2: Schedule (Important & Not Urgent)"),
        "subtasks": subtasks
    }


def find_task_in_database(client: NotionClient, db_id: str, identifier: str) -> Optional[Dict[str, Any]]:
    """Locates a task in the Notion database by ID or fuzzy title match."""
    clean_id = db_id.replace("-", "")
    clean_ident = identifier.replace("-", "").strip().lower()

    # If identifier looks like a full UUID (32 hex chars), attempt direct fetch
    if len(clean_ident) == 32:
        try:
            return client.get_page(clean_ident)
        except Exception:
            pass

    # Query database and scan by ID or title
    items = client.query_database(clean_id, page_size=100)
    for it in items:
        it_id = it.get("id", "").replace("-", "").lower()
        if it_id == clean_ident:
            return it

    # Title match (exact or substring)
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


def apply_decomposition_to_notion(
    client: NotionClient,
    db_id: str,
    parent_task_item: Dict[str, Any],
    plan: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Applies the AI decomposition plan to Notion:
    1. Updates parent task properties (Complexity, Estimated Hours, Team, Category, Eisenhower).
    2. Creates each subtask with native Parent Task relation.
    3. Appends structured Acceptance Criteria & Definition of Done checklist into parent page.
    """
    clean_db_id = db_id.replace("-", "")
    parent_id = parent_task_item.get("id", "").replace("-", "")
    parent_props = parent_task_item.get("properties", {})
    parent_title = parent_props.get("Task Name", {}).get("title", [{}])[0].get("plain_text", "Deliverable")

    # 1. Update Parent Task Properties
    update_payload = {
        "Complexity": {"select": {"name": plan["parent_complexity"]}},
        "Estimated Hours": {"number": plan["parent_est_hours"]},
        "Team / Pod": {"select": {"name": plan["parent_team"]}},
        "Category": {"select": {"name": plan["parent_category"]}},
        "Eisenhower Matrix": {"select": {"name": plan["parent_eisenhower"]}}
    }
    client.update_page(parent_id, update_payload)

    # 2. Create Linked Subtasks in Database
    created_subtasks = []
    for st in plan["subtasks"]:
        subtask_props = {
            "Task Name": {"title": [{"text": {"content": st["title"]}}]},
            "Priority": {"select": {"name": st["priority"]}},
            "Status": {"status": {"name": "To Do"}},
            "Estimated Hours": {"number": st["estimated_hours"]},
            "Complexity": {"select": {"name": st["complexity"]}},
            "Team / Pod": {"select": {"name": st["team"]}},
            "Category": {"select": {"name": st["category"]}},
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

    # 3. Append Structured Checklist to Parent Page Body
    checklist_lines = [
        "---",
        "## 🎯 Deliverable Objective & Scope",
        plan["overview"],
        "",
        "## 🧩 Subtasks & Acceptance Criteria",
    ]
    for st in plan["subtasks"]:
        checklist_lines.append(
            f"- [ ] **{st['short_title']}** ({st['estimated_hours']}h • {st['team']} • {st['complexity']}): {st['acceptance_criteria']}"
        )

    checklist_lines.extend([
        "",
        "## 🛡️ Verification & Definition of Done",
        "- [ ] All linked subtasks executed and verified in staging",
        "- [ ] Edge cases tested and zero regressions logged",
        "- [ ] Deliverable documentation updated and signed off by Pod Lead"
    ])

    markdown_body = "\n".join(checklist_lines)
    client.append_markdown(parent_id, markdown_body)

    return {
        "parent_id": parent_id,
        "parent_title": parent_title,
        "parent_complexity": plan["parent_complexity"],
        "parent_est_hours": plan["parent_est_hours"],
        "subtasks_created": len(created_subtasks),
        "subtasks": created_subtasks
    }
