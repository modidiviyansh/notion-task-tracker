# 🐝 WASP Google Chat Bot (via Google Apps Script)
### 100% Free • No Google Cloud Billing Required • Zero External Servers

Run your interactive Google Chat task intake bot natively inside Google Workspace without needing Google Cloud billing or paid infrastructure.

---

## 🚀 60-Second Setup Guide

### Step 1: Create a Google Apps Script Project
1. Open [**script.google.com**](https://script.google.com/) in your browser.
2. Click **New project** (top-left).
3. Name the project: `WASP Task Bot`.

---

### Step 2: Paste the Code
1. In the editor, open `Code.gs`.
2. Replace everything with the contents of [`Code.js`](Code.js).
3. Click the gear icon (**Project Settings**) in the left sidebar:
   - Check the box: **Show "appsscript.json" manifest file in editor**.
4. Go back to the **Editor** (`< >` icon) $\to$ click `appsscript.json` $\to$ replace contents with [`appsscript.json`](appsscript.json).
5. Click **Save** (💾 icon).

---

### Step 3: Add Your Notion Token (Script Properties)
1. In the left sidebar, click **Project Settings** (gear icon).
2. Scroll down to **Script Properties** $\to$ click **Add script property**:
   - **Property**: `NOTION_TOKEN`
   - **Value**: `ntn_...` *(Your Notion integration token)*
3. Click **Save script properties**.

---

### Step 4: Deploy the Bot (Zero Billing)
1. At the top-right of Apps Script, click **Deploy** $\to$ **New deployment**.
2. Click the gear icon next to "Select type" $\to$ Select **Google Chat app** (or **Add-on**).
3. Set Description to `v1 - Interactive Task Intake`.
4. Click **Deploy**.
5. Copy the Deployment ID.

---

### Step 5: Try It in Google Chat!
In any Google Chat Space:
1. Type `@WASP Task Bot Setup payment gateway` (or `/task`).
2. An interactive **Card Form** appears immediately with pre-filled title, priority dropdown (P1-P4), complexity rating, and due date.
3. Click **SUBMIT TO NOTION**.
4. The task is instantly saved to your Notion master database, and the bot replies with a direct **OPEN IN NOTION** button!
