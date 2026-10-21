/**
 * 🐝 WASP Engine — Google Chat Interactive Task Intake Bot (Google Apps Script)
 * 100% Free • Zero Google Cloud Billing Required • Native Google Workspace
 *
 * When mentioned in any Google Chat Space (e.g. "@WASP task Setup payment gateway"):
 * 1. Opens an interactive Card v2 form with pre-filled title, priority, complexity, and due date.
 * 2. On submit, calls Notion API to create the deliverable in database 3fff1bcff9b881be9e4fd3df8f014a52.
 * 3. Replies with a confirmation card and 1-click "OPEN IN NOTION" button.
 */

// Notion Master Tasks Database ID
const NOTION_DATABASE_ID = "3fff1bcff9b881be9e4fd3df8f014a52";

/**
 * Triggered when a user mentions or sends a message to the bot in Google Chat.
 */
function onMessage(event) {
  const rawText = (event.message && (event.message.argumentText || event.message.text)) || "";
  const cleanTitle = rawText.replace(/@\S+/g, "").replace(/^(task|create|new|add)\s*/i, "").trim();
  const defaultTitle = cleanTitle || "New Deliverable";
  
  // Calculate default due date (2 days from now)
  const due = new Date();
  due.setDate(due.getDate() + 2);
  const defaultDueDate = Utilities.formatDate(due, "GMT+05:30", "yyyy-MM-dd");

  return {
    cardsV2: [{
      cardId: "wasp_intake_form_" + Date.now(),
      card: {
        header: {
          title: "📝 Raise Deliverable in Notion",
          subtitle: "WASP Engine • Interactive Intake Form",
          imageUrl: "https://cdn-icons-png.flaticon.com/512/3596/3596091.png",
          imageType: "CIRCLE"
        },
        sections: [{
          header: "Task Configuration",
          widgets: [
            {
              textInput: {
                name: "task_title",
                label: "Deliverable Title",
                type: "SINGLE_LINE",
                value: defaultTitle
              }
            },
            {
              selectionInput: {
                name: "priority",
                label: "Priority Tier",
                type: "DROPDOWN",
                items: [
                  { text: "🔴 P1 - Urgent (24h SLA)", value: "P1 - Urgent" },
                  { text: "🟠 P2 - High (48h SLA)", value: "P2 - High", selected: true },
                  { text: "🟡 P3 - Medium (Sprint SLA)", value: "P3 - Medium" },
                  { text: "🔵 P4 - Low (Backlog SLA)", value: "P4 - Low" }
                ]
              }
            },
            {
              selectionInput: {
                name: "complexity",
                label: "Complexity Sizing",
                type: "DROPDOWN",
                items: [
                  { text: "⭐ 1 - Trivial (<1h)", value: "⭐ 1 - Trivial" },
                  { text: "⭐⭐ 2 - Simple (1-4h)", value: "⭐⭐ 2 - Simple" },
                  { text: "⭐⭐⭐ 3 - Moderate (1-2d)", value: "⭐⭐⭐ 3 - Moderate", selected: true },
                  { text: "⭐⭐⭐⭐ 4 - Complex (3-5d)", value: "⭐⭐⭐⭐ 4 - Complex" },
                  { text: "⭐⭐⭐⭐⭐ 5 - Epic (>1w)", value: "⭐⭐⭐⭐⭐ 5 - Epic" }
                ]
              }
            },
            {
              textInput: {
                name: "due_date",
                label: "Target Due Date (YYYY-MM-DD)",
                type: "SINGLE_LINE",
                value: defaultDueDate
              }
            },
            {
              textInput: {
                name: "notes",
                label: "Notes / Definition of Done",
                type: "MULTIPLE_LINE",
                value: "Raised via Google Chat Space."
              }
            },
            {
              buttonList: {
                buttons: [{
                  text: "SUBMIT TO NOTION",
                  color: { red: 0.1, green: 0.72, blue: 0.45, alpha: 1.0 },
                  onClick: {
                    action: {
                      actionMethodName: "createTaskInNotion"
                    }
                  }
                }]
              }
            }
          ]
        }]
      }
    }]
  };
}

/**
 * Triggered when a user clicks a button or submits a card form.
 */
function onCardClick(event) {
  const actionName = event.action && event.action.actionMethodName;
  if (actionName === "createTaskInNotion") {
    return handleTaskCreation(event);
  }
  return { text: "Action received." };
}

/**
 * Creates the task in Notion database and responds with confirmation card.
 */
function handleTaskCreation(event) {
  const formInputs = (event.common && event.common.formInputs) || {};
  const title = (formInputs.task_title && formInputs.task_title.stringInputs && formInputs.task_title.stringInputs.value[0]) || "Untitled Deliverable";
  const priority = (formInputs.priority && formInputs.priority.stringInputs && formInputs.priority.stringInputs.value[0]) || "P2 - High";
  const complexity = (formInputs.complexity && formInputs.complexity.stringInputs && formInputs.complexity.stringInputs.value[0]) || "⭐ 3 - Moderate";
  const dueDate = (formInputs.due_date && formInputs.due_date.stringInputs && formInputs.due_date.stringInputs.value[0]) || Utilities.formatDate(new Date(), "GMT+05:30", "yyyy-MM-dd");
  const notes = (formInputs.notes && formInputs.notes.stringInputs && formInputs.notes.stringInputs.value[0]) || "Raised via Google Chat";
  const sender = (event.user && event.user.displayName) || "Team Member";

  // Retrieve Notion Token from Script Properties
  const notionToken = PropertiesService.getScriptProperties().getProperty("NOTION_TOKEN");
  if (!notionToken) {
    return {
      text: "⚠️ Notion Token not found! Please set NOTION_TOKEN in Script Properties at script.google.com."
    };
  }

  // Construct Notion API payload
  const payload = {
    parent: { database_id: NOTION_DATABASE_ID },
    properties: {
      "Task Name": {
        title: [{ text: { content: title } }]
      },
      "Priority": {
        select: { name: priority }
      },
      "Status": {
        status: { name: "To Do" }
      },
      "Complexity": {
        select: { name: complexity }
      },
      "Due Date": {
        date: { start: dueDate }
      },
      "Notes / Deliverables": {
        rich_text: [{ text: { content: "Author: " + sender + " • " + notes } }]
      }
    },
    icon: {
      type: "emoji",
      emoji: "🎯"
    }
  };

  const options = {
    method: "post",
    contentType: "application/json",
    headers: {
      "Authorization": "Bearer " + notionToken,
      "Notion-Version": "2022-06-28"
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    const response = UrlFetchApp.fetch("https://api.notion.com/v1/pages", options);
    const resData = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() >= 400) {
      return {
        text: "❌ Failed to create task in Notion: " + (resData.message || response.getContentText())
      };
    }

    const pageUrl = resData.url || ("https://notion.so/" + resData.id.replace(/-/g, ""));

    return {
      cardsV2: [{
        cardId: "task_success_" + Date.now(),
        card: {
          header: {
            title: "✅ Deliverable Created in Notion!",
            subtitle: "WASP Master Database Updated",
            imageUrl: "https://cdn-icons-png.flaticon.com/512/190/190411.png",
            imageType: "CIRCLE"
          },
          sections: [{
            widgets: [
              {
                decoratedText: {
                  topLabel: "Deliverable Name",
                  text: "<b>" + title + "</b>",
                  icon: { knownIcon: "DESCRIPTION" }
                }
              },
              {
                decoratedText: {
                  topLabel: "Priority & Sizing",
                  text: priority + " • " + complexity + " • Due: " + dueDate,
                  icon: { knownIcon: "STAR" }
                }
              },
              {
                buttonList: {
                  buttons: [{
                    text: "OPEN IN NOTION",
                    color: { red: 0.14, green: 0.51, blue: 0.89, alpha: 1.0 },
                    onClick: {
                      openLink: { url: pageUrl }
                    }
                  }]
                }
              }
            ]
          }]
        }
      }]
    };
  } catch (err) {
    return {
      text: "❌ Error calling Notion API: " + err.toString()
    };
  }
}
