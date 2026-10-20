---
name: notion-project-workflow
description: >-
  Work with Notion API to manage project tasks, read specifications, create documentation,
  and track project delivery milestones together with the developer.
---

# Notion Project Workflow Skill

This skill provides step-by-step procedures for managing project tasks, architecture specifications, and documentation in Notion while pair programming.

## Authentication & Configuration

The Notion integration is pre-configured with the workspace integration token in `.env`.
All operations can be performed either via MCP server tools (when enabled) or using the local `notion_hub` CLI:

```bash
python3 -m notion_hub.cli <subcommand> [args]
```

## Common Workflows

### 1. Discover Workspace Pages & Databases
To see which databases and pages exist in Notion:

```bash
# List all databases (e.g. To Do List, Occurrences, Items)
python3 -m notion_hub.cli list-dbs

# List all pages
python3 -m notion_hub.cli list-pages

# Search by keyword
python3 -m notion_hub.cli search "Project"
```

### 2. Reading Specifications & Tasks
To read specifications, requirements, or tickets from Notion before writing code:

```bash
# Read a full page in Markdown format
python3 -m notion_hub.cli read <PAGE_ID>

# Query all items in a task database
python3 -m notion_hub.cli query-db <DATABASE_ID>
```

### 3. Creating & Updating Tasks
Keep tasks up to date as you build features:

```bash
# Create a new task with due date and notes
python3 -m notion_hub.cli create-task --db <DATABASE_ID> --title "Implement Auth Middleware" --due "2026-10-25" --notes "Add JWT validation and session handling."

# Mark a task as completed
python3 -m notion_hub.cli update-task <TASK_ID> --done

# Update a task's status
python3 -m notion_hub.cli update-task <TASK_ID> --status "In Progress"
```

### 4. Creating Rich Documentation & Architecture RFCs
Sync local markdown design documents, API specs, or READMEs to Notion:

```bash
# Create a new document under a parent page
python3 -m notion_hub.cli create-doc --parent <PAGE_ID> --title "System Architecture" --file "docs/architecture.md" --icon "📐"

# Append progress notes or logs to an existing page
python3 -m notion_hub.cli append --page <PAGE_ID> --content "### Sprint Update\n- Completed core API router\n- Added integration tests"
```

### 5. Bootstrapping a New Project Hub
To create a dedicated project dashboard with a Task Board, Architecture Docs, and Milestones under any existing page:

```bash
python3 -m notion_hub.cli init-hub --parent <PAGE_ID> --name "<PROJECT_NAME>"
```
