# 🐝 WASP Google Chat & Task Intake (Google Apps Script)
### 100% Free • Zero Paid Cloud Billing Required • Native Google Workspace

This Google Apps Script automates task intake directly into your Notion Master Database (`3fff1bcff9b881be9e4fd3df8f014a52`).

You can deploy it in **two ways**, both completely free with **zero billing**:
- **Option A (Instant / 30 seconds)**: **Web App** — Generates a 1-click interactive form link you can pin or share in any Google Chat Space. *Requires zero GCP setup.*
- **Option B (Native Chat Bot / 2 minutes)**: **Google Chat App** — Mentions in Chat (`@WASP`) pop up the form directly inside the Space. *Uses a free standard GCP project without any credit card or billing.*

---

## ⚠️ Resolving the "Apps Script-managed GCP project" Notice

If you saw:
> *"This Apps Script project is using an Apps Script-managed Google Cloud Platform (GCP) project. To deploy an Add-on to the Google Workspace Marketplace, you'll need to switch this Apps Script project to use a user-managed Google Cloud Platform (GCP) project."*

### Why this happens:
By default, Apps Script runs on a hidden default GCP project. Google requires a standard project number for Chat Apps and Marketplace Add-ons.
**You do NOT need Marketplace, and you do NOT need a billing account.**

Choose your preferred path below:

---

## ⚡ Option A: Instant Web App (No GCP Setup, Zero Billing)

If you just want an interactive form for your team that directly writes to Notion:

1. In the Apps Script Editor, click **Deploy** $\to$ **New deployment**.
2. Click the **gear icon ⚙️** next to "Select type" $\to$ select **Web app** *(Do NOT select "Add-on")*.
3. Configure:
   - **Description**: `WASP Intake Form`
   - **Execute as**: `Me`
   - **Who has access**: `Anyone with Google Account` (or `Anyone`)
4. Click **Deploy**.
5. Copy the **Web App URL** (e.g. `https://script.google.com/macros/s/.../exec`).
6. Pin or share this URL in your Google Chat Space as:
   > 📌 **[ 📝 Click Here to Raise a Deliverable in Notion ]**

---

## 🤖 Option B: Native Google Chat Bot (In-Space Mentions)

If you want the bot directly in Google Chat Spaces where typing `@WASP <task>` pops up cards:

### Step 1: Create a Free Standard GCP Project (No Billing Account Needed)
1. Open [**console.cloud.google.com**](https://console.cloud.google.com) (logged in with your Google Workspace / Gmail account).
2. Click the project dropdown at the top $\to$ **New Project**.
3. Name it `WASP-Bot` $\to$ click **Create**.
   *(Google Cloud creates projects for free — no billing or credit card is required!)*
4. In the Project Dashboard (or **Project settings**), copy the numeric **Project Number** (e.g. `104829104812`).

### Step 2: Link the Project Number in Apps Script
1. Go back to your [Apps Script project](https://script.google.com).
2. In the left sidebar, click **Project Settings** (gear icon ⚙️).
3. Scroll down to **Google Cloud Platform (GCP) Project**.
4. Click **Change project**.
5. Paste your **Project Number** and click **Set project**.
   *(The notice is now permanently gone!)*

### Step 3: Add Notion Token in Script Properties
1. Still in **Project Settings** (gear icon ⚙️), scroll down to **Script Properties**.
2. Click **Add script property**:
   - **Property**: `NOTION_TOKEN`
   - **Value**: `ntn_...` *(Your Notion integration token)*
3. Click **Save script properties**.

### Step 4: Enable Google Chat API in GCP Console
1. In [console.cloud.google.com](https://console.cloud.google.com), open **APIs & Services** $\to$ **Library**.
2. Search for **Google Chat API** $\to$ click **Enable**.
3. Once enabled, click **Configuration** (in the left menu under Google Chat API):
   - **App name**: `WASP Task Tracker`
   - **Avatar URL**: `https://cdn-icons-png.flaticon.com/512/3596/3596091.png`
   - **Description**: `Interactive task intake bot for Notion Master Database`
   - Check **Enable interactive features**
   - Check **Join spaces and group conversations** & **Receive 1:1 messages**
   - Under **Connection settings**, select **Apps Script**
   - Under **Deployment ID**:
     - Go back to Apps Script $\to$ click **Deploy** $\to$ **Test deployments** (or **New deployment**) $\to$ copy the **Deployment ID**.
     - Paste it into GCP Configuration.
   - Under **Visibility**: Select **Make available to everyone in [your domain]** (or specific people).
   - Click **Save**.

### Step 5: Test in Google Chat!
In any Google Chat Space:
1. Type `@WASP Task Tracker Setup payment gateway`.
2. An interactive **Card Form** appears immediately with pre-filled title, priority dropdown (P1-P4), complexity rating, and due date.
3. Click **SUBMIT TO NOTION**.
4. The task is saved directly to your Notion master database `3fff1bcff9b881be9e4fd3df8f014a52`!

