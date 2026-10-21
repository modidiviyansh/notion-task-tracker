# Notion Integration & Project Pair-Programming Hub

High-class Notion integration built for **Antigravity** and developer collaboration. It allows us to manage project tasks, write architecture specs, track sprints, and build projects together seamlessly.

---

## 🚀 Integration Overview

- **Integration Bot**: `AntigravityToken`
- **Workspace**: `Diviyansh Modi’s Space`
- **Integration Protocols**:
  1. **Antigravity Plugin & MCP Server**: Configured with `@notionhq/notion-mcp-server` under `.agents/plugins/notion/`.
  2. **Python SDK & CLI (`notion_hub`)**: Fast, resilient, zero-dependency toolkit for reading/writing Notion pages, databases, and blocks directly.
  3. **Antigravity Rules & Skills**: Automated guidance for syncing tasks, documentation, and progress during development.

---

## 🛠️ CLI Reference (`notion_hub`)

You and Antigravity can interact with Notion using `python3 -m notion_hub.cli`:

### 1. Account & Health Check
```bash
python3 -m notion_hub.cli whoami
```

### 2. Search & Discovery
```bash
# List all accessible databases
python3 -m notion_hub.cli list-dbs

# List all accessible pages
python3 -m notion_hub.cli list-pages

# Search across pages and databases
python3 -m notion_hub.cli search "query"
```

### 3. Read Page Content (Markdown-First)
```bash
python3 -m notion_hub.cli read <PAGE_ID>
```

### 4. Database & Task Management
```bash
# Query items in a database
python3 -m notion_hub.cli query-db <DATABASE_ID>

# Create a new task with due date & notes
python3 -m notion_hub.cli create-task --db <DATABASE_ID> --title "Build User Auth" --due "2026-10-25" --notes "Implement JWT flow."

# Mark a task as done
python3 -m notion_hub.cli update-task <TASK_ID> --done

# Update status
python3 -m notion_hub.cli update-task <TASK_ID> --status "In Progress"
```

### 5. Create Rich Docs & Specs
```bash
# Create a new doc from a local markdown file
python3 -m notion_hub.cli create-doc --parent <PAGE_ID> --title "System Architecture" --file "docs/architecture.md" --icon "📐"

# Append notes or logs to a page
python3 -m notion_hub.cli append --page <PAGE_ID> --content "### Progress Update\n- Integrated database layer"
```

### 6. Deliverable Decomposition Studio (Human-Directed Notes-to-Subtasks)
```bash
# Preview parsing notes into structured subtasks (dry run)
python3 -m notion_hub.cli decompose --task "Reception Management System" --notes-file "plan.md"

# Apply subtasks directly to Notion (with Parent Task link & plan notes appended to parent page)
python3 -m notion_hub.cli decompose --task "Reception Management System" --notes-file "plan.md" --apply
```
> **Note**: You can also use the interactive **Decomposition Studio** right on the GitHub Pages live dashboard to select any deliverable, write pillars/steps in the "Notes Thingy", review the cards, and create them directly into Notion.

### 7. Initialize a Full Project Hub
```bash
# Creates a Hub Page, Task Board Database, and Specs Page under a parent page
python3 -m notion_hub.cli init-hub --parent <PAGE_ID> --name "My Awesome Project"
```

---

## 🐝 WASP Dashboard : Work Analysis System & Profile Dashboard

A high-performance Native Notion Work Analysis System & Profile Dashboard equipped with automatic priority-dominant aging formulas, End-Date-driven backlog construction, 6-header standardized blueprints, multi-user Profile accountability, and n8n automations for Google Workspace (Google Chat Card v2 & Gmail).

### 🚀 Quick Start Commands

```bash
# 1. Initialize fresh WASP Dashboard & Master Database in Notion
python3 -m notion_hub.cli wasp-setup

# 2. View live Work Analysis & Profile metrics (including Complexity & Horizon breakdown)
python3 -m notion_hub.cli wasp-metrics

# 3. Progressive Organization: Stage 1 — Quick Friction-Free Capture (Inbox)
python3 -m notion_hub.cli wasp-raise --title "Check database connection spike"

# 4. Progressive Organization: Stage 2 & 3 — Clarify, Size Complexity (1-5), and Assign
python3 -m notion_hub.cli wasp-raise \
  --title "Implement Distributed Cache Cluster" \
  --priority "P1 - Urgent" \
  --complexity 4 \
  --end-date "2026-10-25" \
  --team "Backend" \
  --action-by "Assignee (In Flight)" \
  --category "Engineering" \
  --details "Deploy Redis caching layer to offload primary database cluster." \
  --est-hours 8 \
  --eisenhower "Q1: Do First (Urgent & Important)"

# 5. Refresh and sync live Task Dashboard directly onto your Notion Hub Page
python3 -m notion_hub.cli wasp-sync
```

### 🎧 Deep Work & Productivity Suite

Integrated right at the top of your Notion Dashboard:
- 🍅 **Pomodoro Timer (25m Focus / 5m Rest)**: Direct links to Pomofocus (`https://pomofocus.io`) for time-boxed sprint intervals.
- ⏱️ **Task Time Tracker**: Direct integration with Toggl Track & Clockify for tracking `Estimated Hours` vs `Actual Hours`.
- 🎧 **24/7 Lo-Fi Focus Music Radio**: Embedded native YouTube video player streaming deep work ambient audio directly in Notion.

### 📥 Progressive Organization Workflow

Designed around the proven GTD & PARA progressive sizing methodology:
1. **Stage 1 — Raw Capture (Inbox)**: Fast, friction-free idea dump. No mandatory fields.
2. **Stage 2 — Clarify & Triage**: Review inbox items, assign Priority tier, End Date cutoff, and Pod ownership.
3. **Stage 3 — Sizing & Execution**: Add Complexity rating (`⭐ 1 - Trivial` to `⭐⭐⭐⭐⭐ 5 - Epic`), estimated hours, and subtasks.

### ⭐ Complexity Rating & Sizing Scale

- `⭐ 1 - Trivial`: Typo fixes, minor config changes (<1 hour).
- `⭐⭐ 2 - Simple`: Small bug fixes, isolated function tweaks (1-4 hours).
- `⭐⭐⭐ 3 - Moderate`: Standard feature delivery, component refactoring (1-2 days).
- `⭐⭐⭐⭐ 4 - Complex`: Multi-module integrations, database optimizations, security audits (3-5 days).
- `⭐⭐⭐⭐⭐ 5 - Epic`: Architectural overhauls, major migrations, platform redesigns (>1 week).

### 🗓️ Visual Workflow Horizons (As shown in Task Dashboard)

- 🗓️ **TODO Today & Sprint Focus**: Primary execution queue filtered by `End Date / Due Date is Today` or `Status is In Progress`.
- ⚠️ **Past Due / Rolled-Over Debt**: Urgent overdue deliverables that slipped past their cutoff.
- 📥 **Capture Inbox**: Unclarified raw captures awaiting triage.
- 📅 **Due in Next 7 Days**: Active sprint deliverables scheduled within the 7-day horizon.

### 👤 Personalized Workbenches (Multi-User Accountability)

- **Personalized "My Action Items" (`Assignee is @me`)**: Dynamically personalizes the Notion workbench for whoever is currently viewing the board.
- **Tasks Created by Me (`Created By is @me`)**: Keeps track of deliverables you authored or delegated.
- **People Database Relation (`Profile / Contributor`)**: Bi-directionally links tasks to individual contributor profiles in the workspace `People` database (`d3df1bcf-f9b8-82df-b0d8-014512d331ec`).
- **Grab-and-Go Sprint Pool (`Assignee is empty`)**: Available sprint candidate items ready for team members to claim.
- **Peer Review Pipeline (`Status is In Review`)**: Explicit handoff queue so PRs, designs, and specs receive prompt sign-off.
- **Pod Allocation**: Grouped by `Frontend`, `Backend`, `DevOps & Infra`, `Design`, `Product`, or `QA & Security`.

### 🧭 Visual Views: Kanban, Calendar & Hierarchy

1. 🗂️ **Status Kanban**: `Backlog` $\to$ `To Do` $\to$ `In Progress` $\to$ `In Review` $\to$ `Done` $\to$ `Archived`.
2. 🎯 **Priority Kanban**: `P1 - Urgent` $\to$ `P2 - High` $\to$ `P3 - Medium` $\to$ `P4 - Low`.
3. 🗓️ **Calendar Delivery View**: Full monthly schedule plotted by `End Date` and `Due Date`.
4. ⭐ **Complexity Matrix**: Tasks categorized by difficulty level (⭐ 1 to ⭐ 5).
5. 🌳 **Parent & Subtask Hierarchy**: Native Notion sub-items tree view.

### 🤖 Google Workspace & n8n Automation Workflows (`n8n_workflows/`)

Includes 3 ready-to-import production n8n workflows:
1. `daily_critical_escalation_alert.json`: Daily 9:00 AM scan for score $\ge 250$ $\to$ posts Card v2 to **Google Chat Space** & emails briefing via **Gmail**.
2. `sprint_end_date_rollover_backlog.json`: Sunday midnight scan for missed End Dates $\to$ rolls them into Backlog Debt $\to$ pings Google Chat.
3. `weekly_admin_accountability_digest.json`: Friday 5:00 PM executive rollup of 7d/15d/30d velocity and backlog clearance $\to$ Google Chat & Gmail.

### 📌 Standardized 6-Header Task Blueprint

Every task page contains 6 structured headers:
1. `# 📌 Task Overview & Definition of Done`: Objectives and Acceptance Criteria checkboxes.
2. `# ⚡ Urgency & Priority Metrics`: Priority tier, cutoff date, and scoring details.
3. `# 👤 Profile & Team Ownership`: Functional pod, assignee, reviewer, and action routing.
4. `# 🧩 Subtasks Breakdown`: Interactive checklist linked via parent-subtask relations.
5. `# ⏱️ Effort Estimation & Time Log`: Estimated vs actual hours tracking.
6. `# 📝 Notes & Architecture Decisions`: Meeting notes, links, and design records.

### 🧭 Curated Database Views Guide

1. 👑 **Admin Accountability Matrix**: Team throughput grouped by `Assignee` $\to$ `Status`.
2. 🔥 **Escalation Hotlist**: Active tasks sorted by Priority Score descending.
3. 👤 **My Action Items**: Dynamic 1-click personal workbench (`Assignee contains @me`).
4. 🎯 **Open Sprint Grab-and-Go**: Available sprint pool (`Assignee is empty`).
5. 👀 **Peer Review Board**: Handoff queue for code/design sign-offs (`Status is In Review`).
6. 🗓️ **End Date Horizon Planner**: Visual timeline & calendar view of deliverables.
7. ⚡ **7-Day Sprint Horizon**: Tasks due in the next 7 days or completed within 7 days.
8. 🏢 **Team Pod Workload Board**: Grouped by `Team / Pod` (Frontend, Backend, DevOps, Design, Product, QA).
9. 📥 **Backlog Cleared & Rolled-Over Queue**: Backlog tasks sorted by Days Elapsed (oldest first).
10. 🎯 **Eisenhower Matrix Board**: Categorized into 4 quadrants (Q1 Do First, Q2 Schedule, Q3 Delegate, Q4 Eliminate).
11. 🌳 **Parent & Subtask Hierarchy**: Native Notion sub-items tree view.

---

### 🚀 Phase 2: Automation, AI Breakdown & GitHub Pages Dashboard

1. **Lightweight GitHub Pages Dashboard (`docs/`)**:
   - High-performance, dark-mode glassmorphism dashboard built with Vanilla CSS & Chart.js.
   - Deploys instantly to GitHub Pages with automatic deployment workflow (`.github/workflows/deploy-pages.yml`).
   - Interactive filtering by Assignee, Status, and real-time text search.
   - Export latest Notion data anytime with:
     ```bash
     python3 -m notion_hub.cli export-dashboard
     ```

2. **AI Task Sizing & Subtask Decomposition Engine (`notion_hub/task_breakdown.py`)**:
   - Analyzes deliverables across domain archetypes (School SIS/ERP, Fees Accountability, Reception Systems, Video Pipelines, Analytics Engines).
   - Sizes overall deliverable complexity (`⭐ 1 - Trivial` to `⭐⭐⭐⭐⭐ 5 - Epic`) and computes total estimated hours.
   - Decomposes into 3–5 sized subtasks and links them with native Notion **Parent-Child relations**.
   - Enriches parent Notion page bodies with interactive **Acceptance Criteria & Definition of Done checklists**.
     ```bash
     # Preview generated sizing, hours, pod, and subtask breakdown
     python3 -m notion_hub.cli breakdown --task "Reception Management System"

     # Apply sizing, link subtasks, and write checklists directly in Notion
     python3 -m notion_hub.cli breakdown --task "Reception Management System" --apply

     # Batch scan all active un-sized deliverables and preview recommendations
     python3 -m notion_hub.cli breakdown-all

     # Batch auto-size and link subtasks for ALL un-sized active deliverables
     python3 -m notion_hub.cli breakdown-all --apply
     ```

3. **Google Workspace & Google Chat Alerts (`notion_hub/alerts.py`)**:
   - Dispatches interactive Google Chat Card v2 messages and Gmail briefs:
     ```bash
     # Scan and alert on active P1 Urgent SLA items
     python3 -m notion_hub.cli alert-p1

     # Compile and dispatch weekly executive digest scorecard
     python3 -m notion_hub.cli weekly-digest
     ```

---

## 📁 Repository Structure

```text
├── .env                               # Notion Token (gitignored)
├── .env.example                       # Token template
├── .gitignore                         # Protects secrets & caches
├── README.md                          # Project & integration documentation
├── .github/                           # GitHub Actions CI/CD
│   └── workflows/
│       └── deploy-pages.yml           # Automated GitHub Pages deployment
├── docs/                              # GitHub Pages Live Dashboard
│   ├── index.html                     # Semantic responsive HTML structure
│   ├── styles.css                     # Glassmorphism dark mode design system
│   ├── app.js                         # Dynamic Chart.js visualizations & search
│   └── data.json                      # Live Notion export dataset
├── n8n_workflows/                     # Ready-to-import n8n automations
│   ├── README.md                      # n8n setup guide for Google Workspace
│   ├── daily_critical_escalation_alert.json
│   ├── sprint_end_date_rollover_backlog.json
│   ├── task_assignment_and_review_router.json
│   └── weekly_admin_accountability_digest.json
├── notion_hub/                        # Python SDK & WASP engine
│   ├── __init__.py
│   ├── client.py                      # Core Notion HTTP client
│   ├── converter.py                   # Bi-directional Markdown <-> Notion blocks converter
│   ├── wasp_engine.py                 # WASP schema, formulas, analytics, and blueprints
│   ├── personal_engine.py             # Accountability matrix & multi-horizon formulas
│   ├── sync_filtered_analytics.py     # Native tables, QuickChart visualizations & sync engine
│   ├── alerts.py                      # Google Chat Card v2 & webhook alert dispatcher
│   ├── task_breakdown.py              # Human-directed deliverable decomposition & notes-to-subtasks engine
│   ├── export_dashboard.py            # Static dashboard dataset exporter for GitHub Pages
│   ├── task_manager.py                # Legacy task manager module
│   └── cli.py                         # Full-featured command line interface
└── .agents/                           # Antigravity Customizations
    └── plugins/
        └── notion/
            ├── plugin.json            # Plugin manifest
            ├── mcp_config.json        # Official Notion MCP server configuration
            ├── rules/
            │   └── AGENTS.md          # Pair-programming & sync rules
            └── skills/
                └── notion-project-workflow/
                    └── SKILL.md       # Interactive Notion workflow skill
```
