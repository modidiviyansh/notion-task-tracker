# 🐝 WASP Engine — Automation Architecture & n8n Suite

A production-grade hybrid automation architecture designed for **Notion + Self-Hosted n8n + GitHub Actions + Google Workspace**.

---

## 🏛️ Strategic Segmentation: GitHub Actions vs. n8n

| Automation Domain | Engine | Execution Trigger | Operational Behavior |
| :--- | :---: | :--- | :--- |
| **Static Web Dashboard & Live Data Publishing** | **GitHub Actions** | Push to `master` + Scheduled Cron (every 6h) | Exports Notion tasks to `docs/data.json`, compiles assets, and deploys directly to GitHub Pages (`modidiviyansh.github.io/notion-task-tracker`). |
| **🚨 Daily P1 SLA Breach Scanner & Team Alerts** | **n8n** | Mon–Fri at 9:00 AM | Scans for tasks with `Priority = P1 - Urgent` or `Score >= 250` sitting in backlog $\to$ Dispatches interactive Card v2 to Google Chat Space & Gmail. |
| **🔄 Sprint End Date Rollover & Backlog Debt Engine** | **n8n** | Sunday at Midnight | Scans for unfinished tasks past cutoff `End Date` $\to$ Automatically marks `Original Backlog Item = True` $\to$ Transitions status to `Backlog` $\to$ Posts Rollover Debt digest. |
| **👀 Peer Review Pipeline Router** | **n8n** | Polls every 15 Minutes | Detects deliverables entering `In Review` or requiring peer sign-off $\to$ Alerts reviewers with a direct 1-click `REVIEW TASK` button. |
| **📈 Weekly Executive Accountability Digest** | **n8n** | Friday at 5:00 PM | Aggregates 7d / 15d / 30d throughput and individual accountability scores $\to$ Posts executive scorecard to Google Chat & Gmail. |
| **⚡ On-Demand Webhook Rebuild** | **n8n** | Incoming Webhook | When triggered, calls GitHub API to rebuild and redeploy the live GitHub Pages dashboard instantly. |

---

## 📦 The 5 Pre-Built n8n Workflow JSONs

| Workflow File | Purpose | Channels / Actions |
| :--- | :--- | :--- |
| `daily_critical_escalation_alert.json` | Morning urgent escalation hotlist | Google Chat Space + Gmail |
| `sprint_end_date_rollover_backlog.json` | Automatic sprint debt rollover | Notion API + Google Chat |
| `task_assignment_and_review_router.json` | Review queue handoff notifications | Google Chat Space |
| `weekly_admin_accountability_digest.json` | Weekly performance scorecard | Google Chat Space + Gmail |
| `trigger_github_pages_rebuild.json` | Instant GitHub Pages rebuild trigger | GitHub API (`repository_dispatch`) |

---

## 🚀 3-Minute Setup on Your Self-Hosted n8n

### Step 1: Import Workflows into n8n
1. Open your self-hosted n8n web interface.
2. In the left navigation, click **Workflows**.
3. In the upper-right corner, click **`...` (More Options)** $\to$ Select **`Import from File`**.
4. Select any of the `.json` files in this directory.

---

### Step 2: Set Notion Header Auth Credential in n8n
1. In n8n, navigate to **Credentials** $\to$ **Add Credential** $\to$ Select **Header Auth**.
2. Configure:
   - **Credential Name**: `Notion API Token`
   - **Name**: `Authorization`
   - **Value**: `Bearer ntn_YOUR_NOTION_TOKEN_HERE`
3. Click **Save**. In any imported HTTP Request node querying Notion, select this credential.

---

### Step 3: Configure Target Channels

#### A. Google Chat Space Webhook:
1. In Google Chat, go to your team Space $\to$ click the Space title $\to$ **Apps & integrations** $\to$ **Manage webhooks**.
2. Add a webhook named `🐝 WASP Bot` and copy the URL.
3. In n8n, set an Environment Variable `GOOGLE_CHAT_WEBHOOK_URL` or paste the URL directly into the HTTP Request nodes.

#### B. Gmail Notifications (Optional):
1. In the Gmail node in n8n, authenticate with your Google Workspace account via OAuth2.
2. The recipient is pre-configured to `diviyanshmodi@gcmconventschool.in`.

#### C. On-Demand GitHub Pages Rebuild (Optional):
1. Create a GitHub Personal Access Token (classic or fine-grained) with `repo` scope.
2. In `trigger_github_pages_rebuild.json`, set Header Auth `Authorization: token YOUR_GITHUB_PAT`.
3. Whenever called, it triggers GitHub Actions to refresh the live dashboard immediately.

---

## 🔗 Live Production References

- **Live GitHub Pages Dashboard**: [https://modidiviyansh.github.io/notion-task-tracker/](https://modidiviyansh.github.io/notion-task-tracker/)
- **Master Notion Tasks Database**: [https://app.notion.com/3fff1bcff9b881be9e4fd3df8f014a52](https://app.notion.com/3fff1bcff9b881be9e4fd3df8f014a52)
- **Main Notion Dashboard**: [https://app.notion.com/p/Task-Tracker-3fff1bcff9b88188b004f044be8090fe](https://app.notion.com/p/Task-Tracker-3fff1bcff9b88188b004f044be8090fe)
