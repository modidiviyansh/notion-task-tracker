# 🐝 WASP Engine — n8n & Google Workspace Automation Suite

Enterprise-grade automated workflows designed for the **WASP Engine** connected with **Google Workspace (Google Chat Spaces & Gmail)**.

---

## 📦 Included Automated Workflows

| Workflow File | Trigger Schedule | Target Channels | Operational Behavior |
| :--- | :--- | :--- | :--- |
| **`daily_critical_escalation_alert.json`** | Mon–Fri at 9:00 AM | **Google Chat Space** + **Gmail** | Scans for tasks with Score $\ge 250$ or `P1 - Urgent` $\to$ Posts interactive Google Chat Card v2 $\to$ Emails morning escalation briefing to Admin. |
| **`sprint_end_date_rollover_backlog.json`** | Sunday at Midnight | **Google Chat Space** | Scans for tasks where `End Date < today` and `Status != Done` $\to$ Automatically marks `Original Backlog Item = True` $\to$ Converts to `Backlog` $\to$ Posts Rollover Debt digest. |
| **`weekly_admin_accountability_digest.json`**| Friday at 5:00 PM | **Google Chat Space** + **Gmail** | Aggregates 7d / 15d / 30d velocity, conquered backlog items, and team pod distribution $\to$ Posts executive scorecard to Google Chat $\to$ Emails digest to Admin. |
| **`task_assignment_and_review_router.json`**| Every 15 Minutes | **Google Chat Space** | Scans for tasks in `In Review` or requiring peer signoff $\to$ Dispatches interactive Card v2 with 1-click `REVIEW TASK` button. |

---

## 🚀 Quick Setup Guide (3 Simple Steps)

### Step 1: Import into n8n
1. Open your **n8n instance** (self-hosted, Docker, or n8n Cloud).
2. Click **Workflows** in the sidebar $\to$ Click the **`...` (Options)** menu at the top right $\to$ Select **`Import from File`**.
3. Select any of the `.json` files in this directory:
   - `daily_critical_escalation_alert.json`
   - `sprint_end_date_rollover_backlog.json`
   - `weekly_admin_accountability_digest.json`
   - `task_assignment_and_review_router.json`

---

### Step 2: Configure Notion Credentials
1. In n8n, open any of the Notion HTTP Request nodes.
2. Under **Authentication**, select **Header Auth**.
3. Create a credential:
   - **Name**: `Authorization`
   - **Value**: `Bearer YOUR_NOTION_TOKEN` (the token from your `.env` file).

---

### Step 3: Configure Google Workspace (Google Chat & Gmail)

#### A. Google Chat Space Webhook (Takes 30 seconds):
1. In **Google Chat**, navigate to your team Space.
2. Click the Space name at the top $\to$ Select **`Apps & Integrations`** $\to$ Click **`Manage webhooks`**.
3. Set the name to `🐝 WASP Engine Bot` and click **Save**.
4. Copy the generated Webhook URL.
5. In n8n, set the environment variable `GOOGLE_CHAT_WEBHOOK_URL` (or paste the webhook URL directly into the HTTP Request node).

#### B. Gmail / Google Workspace Email:
1. In n8n, click on the **Gmail** node.
2. Connect your Google Workspace account via OAuth2 (or standard n8n Google credential).
3. The recipient is pre-configured to `diviyanshmodi@gcmconventschool.in` (customizable via `ADMIN_WORKSPACE_EMAIL`).

---

## 🔗 Live Connected Resources

- **Master Tasks Database**: [https://app.notion.com/3fff1bcff9b881be9e4fd3df8f014a52](https://app.notion.com/3fff1bcff9b881be9e4fd3df8f014a52)
- **Main WASP Dashboard**: [https://app.notion.com/p/WASP-Dashboard-Work-Analysis-System-Profile-Dashboard-3fff1bcff9b88188b004f044be8090fe](https://app.notion.com/p/WASP-Dashboard-Work-Analysis-System-Profile-Dashboard-3fff1bcff9b88188b004f044be8090fe)
- **WASP Personal Dashboard**: [https://app.notion.com/p/WASP-Personal-Dashboard-Work-Analysis-Profile-Cockpit-3fff1bcff9b8817f8023c5f897489080](https://app.notion.com/p/WASP-Personal-Dashboard-Work-Analysis-Profile-Cockpit-3fff1bcff9b8817f8023c5f897489080)
- **Personal Scoreboard Database**: [https://app.notion.com/3fff1bcff9b8818291f3c96e8ab12275](https://app.notion.com/3fff1bcff9b8818291f3c96e8ab12275)
