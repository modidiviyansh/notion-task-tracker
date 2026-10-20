# Notion Project Collaboration Rules

When collaborating on projects in this workspace, Notion serves as the single source of truth for project tasks, roadmaps, architecture decisions, and documentation.

## Guidelines for Antigravity

1. **Task & Requirement Awareness**:
   - Before implementing complex features or milestones, check Notion for existing task tickets or requirement documents.
   - Use `python3 -m notion_hub.cli query-db <DATABASE_ID>` or `python3 -m notion_hub.cli search <QUERY>` to retrieve context.

2. **Progress & Status Syncing**:
   - When completing tasks, features, or bug fixes, update the corresponding Notion task item:
     - `python3 -m notion_hub.cli update-task <TASK_ID> --done` (or `--status Done`)
   - If new follow-up tasks, bugs, or technical debt items are identified during development, create them in the Notion database:
     - `python3 -m notion_hub.cli create-task --db <DATABASE_ID> --title "<TASK TITLE>" --notes "<DETAILS>"`

3. **Architecture & Documentation**:
   - Important architectural decisions, API schemas, or technical specs should be synced to Notion pages:
     - `python3 -m notion_hub.cli create-doc --parent <PAGE_ID> --title "<DOC TITLE>" --file <PATH_TO_MD>`
   - To append meeting notes, progress updates, or changelogs:
     - `python3 -m notion_hub.cli append --page <PAGE_ID> --content "<MARKDOWN>"`

4. **Security & Credentials**:
   - Never commit `.env` or raw Notion API tokens into git.
   - The integration token is securely loaded from `.env`.
