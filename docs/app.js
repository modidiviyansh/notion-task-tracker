// WASP Engine — Interactive GitHub Pages Dashboard Application
// Integrates live Notion dataset, dynamic Chart.js visualizations, and AI decomposition.

let dashboardData = null;
let currentAssigneeFilter = 'all';
let currentStatusFilter = 'all';
let currentSearchQuery = '';

let priorityChart = null;
let velocityChart = null;
let assigneeChart = null;

// Initial Fallback Data (Ensures instantaneous render even before fetch or offline)
const FALLBACK_DATA = {
  "total_tasks": 11,
  "total_pending": 10,
  "total_debt_pts": 1325,
  "total_est_hours": 18.7,
  "accountability_score": 82,
  "status_counts": { "To Do": 5, "In Progress": 2, "In Review": 1, "Backlog": 2, "Done": 1 },
  "priority_counts": { "P1 - Urgent": 2, "P2 - High": 1, "P3 - Medium": 5, "P4 - Low": 3 },
  "completed_horizons": { "7d": 1, "15d": 1, "30d": 1 },
  "assignee_summary": {
    "karanveer": { "total": 4, "done": 0, "in_progress": 1, "backlog": 3 },
    "Diviyansh Modi": { "total": 1, "done": 0, "in_progress": 0, "backlog": 1 },
    "Unassigned": { "total": 7, "done": 1, "in_progress": 1, "backlog": 5 }
  },
  "tasks": [
    { "id": "1", "title": "Sample Tasks", "status": "Done", "priority": "P1 - Urgent", "assignees": ["Unassigned"], "due_date": "2026-10-20", "progress_bar": "■■■■■■■■■■ 100%", "estimated_hours": 2.0 },
    { "id": "2", "title": "Kotak Mahindra Bank Video", "status": "In Progress", "priority": "P2 - High", "assignees": ["karanveer"], "due_date": "2026-10-20", "progress_bar": "■■■■■■□□□□ 60%", "estimated_hours": 4.0 },
    { "id": "3", "title": "Video Editing Skil Via Claude Code", "status": "To Do", "priority": "P4 - Low", "assignees": ["Unassigned"], "due_date": "2026-10-23", "progress_bar": "■■□□□□□□□□ 20%", "estimated_hours": 2.5 },
    { "id": "4", "title": "Meta Video Lineup", "status": "Backlog", "priority": "P3 - Medium", "assignees": ["Unassigned"], "due_date": "2026-10-24", "progress_bar": "□□□□□□□□□□ 0%", "estimated_hours": 3.0 },
    { "id": "5", "title": "Activity Tracker System", "status": "Backlog", "priority": "P3 - Medium", "assignees": ["Unassigned"], "due_date": "2026-10-24", "progress_bar": "□□□□□□□□□□ 0%", "estimated_hours": 3.5 },
    { "id": "6", "title": "Claude Carousel Generation", "status": "To Do", "priority": "P3 - Medium", "assignees": ["Unassigned"], "due_date": "2026-10-21", "progress_bar": "■■□□□□□□□□ 20%", "estimated_hours": 2.0 },
    { "id": "7", "title": "ERP Sis Go Through", "status": "To Do", "priority": "P3 - Medium", "assignees": ["Unassigned"], "due_date": "2026-10-21", "progress_bar": "■■□□□□□□□□ 20%", "estimated_hours": 3.0 },
    { "id": "8", "title": "Google Chat", "status": "In Progress", "priority": "P4 - Low", "assignees": ["Unassigned"], "due_date": "2026-10-20", "progress_bar": "■■■■■■□□□□ 60%", "estimated_hours": 1.5 },
    { "id": "9", "title": "Dashboarding Form for Various Uploads", "status": "To Do", "priority": "P1 - Urgent", "assignees": ["karanveer"], "due_date": "2026-10-20", "progress_bar": "■■□□□□□□□□ 20%", "estimated_hours": 3.0 },
    { "id": "10", "title": "Notion", "status": "In Review", "priority": "P4 - Low", "assignees": ["karanveer", "Diviyansh Modi"], "due_date": "2026-10-20", "progress_bar": "■■■■■■■■□□ 80%", "estimated_hours": 2.0 },
    { "id": "11", "title": "Reception Management System", "status": "To Do", "priority": "P3 - Medium", "assignees": ["karanveer"], "due_date": "2026-10-22", "progress_bar": "■■□□□□□□□□ 20%", "estimated_hours": 3.5 }
  ]
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', async () => {
  await loadDashboardData();
  setupEventListeners();
  initDecompositionStudio();
});

async function loadDashboardData() {
  try {
    const res = await fetch('data.json');
    if (res.ok) {
      dashboardData = await res.json();
      console.log('Loaded live data.json');
    } else {
      dashboardData = FALLBACK_DATA;
    }
  } catch (e) {
    console.warn('Using fallback data:', e);
    dashboardData = FALLBACK_DATA;
  }
  updateUI();
}

function updateUI() {
  updateKPICards();
  renderCharts();
  renderTasksTable();
  populateDecomposeTaskDropdown();
}

function updateKPICards() {
  document.getElementById('val-score').textContent = dashboardData.accountability_score || 82;
  document.getElementById('val-backlog').textContent = dashboardData.total_pending || 10;
  document.getElementById('val-debt-pts').textContent = `${(dashboardData.total_debt_pts || 1325).toLocaleString()} weighted debt pts`;
  document.getElementById('val-wip').textContent = (dashboardData.status_counts && dashboardData.status_counts['In Progress']) || 2;
  document.getElementById('val-completed-7d').textContent = (dashboardData.completed_horizons && dashboardData.completed_horizons['7d']) || 1;
}

function renderCharts() {
  // Chart 1: Priority Mix Donut
  const ctxPriority = document.getElementById('chart-priority-mix');
  if (ctxPriority) {
    if (priorityChart) priorityChart.destroy();
    const pCounts = dashboardData.priority_counts || { "P1 - Urgent": 1, "P2 - High": 1, "P3 - Medium": 5, "P4 - Low": 3 };

    priorityChart = new Chart(ctxPriority, {
      type: 'doughnut',
      data: {
        labels: ['P1 - Urgent', 'P2 - High', 'P3 - Medium', 'P4 - Low'],
        datasets: [{
          data: [
            pCounts['P1 - Urgent'] || 0,
            pCounts['P2 - High'] || 0,
            pCounts['P3 - Medium'] || 0,
            pCounts['P4 - Low'] || 0
          ],
          backgroundColor: ['#EF4444', '#F59E0B', '#EAB308', '#3B82F6'],
          borderColor: '#0F172A',
          borderWidth: 3,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#94A3B8', font: { family: 'Inter', size: 12 }, padding: 16 }
          }
        },
        cutout: '65%'
      }
    });
  }

  // Chart 2: Multi-Horizon Velocity Bar Chart
  const ctxVelocity = document.getElementById('chart-velocity-bars');
  if (ctxVelocity) {
    if (velocityChart) velocityChart.destroy();
    const h = dashboardData.completed_horizons || { '7d': 1, '15d': 1, '30d': 1 };
    const wip = (dashboardData.status_counts && dashboardData.status_counts['In Progress']) || 2;
    const pending = dashboardData.total_pending || 10;

    velocityChart = new Chart(ctxVelocity, {
      type: 'bar',
      data: {
        labels: ['7d Sprint', '15d Mid-Cycle', '30d Monthly', 'In Flight WIP', 'Pending Backlog'],
        datasets: [{
          label: 'Deliverables',
          data: [h['7d'] || 1, h['15d'] || 1, h['30d'] || 1, wip, pending],
          backgroundColor: ['#10B981', '#06B6D4', '#8B5CF6', '#F59E0B', '#EF4444'],
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { color: '#94A3B8', stepSize: 1, font: { family: 'JetBrains Mono' } },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          },
          x: {
            ticks: { color: '#CBD5E1', font: { family: 'Inter', size: 11 } },
            grid: { display: false }
          }
        }
      }
    });
  }

  // Chart 3: Assignee Workload Breakdown (Horizontal Bar)
  const ctxAssignee = document.getElementById('chart-assignee-workload');
  if (ctxAssignee) {
    if (assigneeChart) assigneeChart.destroy();
    const aSummary = dashboardData.assignee_summary || {};
    const labels = Object.keys(aSummary);
    const doneVals = labels.map(l => aSummary[l].done || 0);
    const wipVals = labels.map(l => aSummary[l].in_progress || 0);
    const backlogVals = labels.map(l => aSummary[l].backlog || 0);

    assigneeChart = new Chart(ctxAssignee, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          { label: 'Done', data: doneVals, backgroundColor: '#10B981', borderRadius: 4 },
          { label: 'In Flight (WIP)', data: wipVals, backgroundColor: '#3B82F6', borderRadius: 4 },
          { label: 'Backlog / In Review', data: backlogVals, backgroundColor: '#F59E0B', borderRadius: 4 }
        ]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#94A3B8', font: { family: 'Inter', size: 12 }, padding: 14 } }
        },
        scales: {
          x: {
            stacked: true,
            beginAtZero: true,
            ticks: { color: '#94A3B8', stepSize: 1, font: { family: 'JetBrains Mono' } },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          },
          y: {
            stacked: true,
            ticks: { color: '#F1F5F9', font: { family: 'Inter', weight: '600' } },
            grid: { display: false }
          }
        }
      }
    });
  }
}

function renderTasksTable() {
  const tbody = document.getElementById('tasks-tbody');
  if (!tbody || !dashboardData.tasks) return;

  const filtered = dashboardData.tasks.filter(t => {
    // Assignee filter
    if (currentAssigneeFilter !== 'all') {
      const hasAssignee = t.assignees.some(a => a.toLowerCase().includes(currentAssigneeFilter.toLowerCase()));
      if (!hasAssignee) return false;
    }
    // Status filter
    if (currentStatusFilter !== 'all') {
      if (t.status !== currentStatusFilter) return false;
    }
    // Search query
    if (currentSearchQuery) {
      const q = currentSearchQuery.toLowerCase();
      const matchTitle = t.title.toLowerCase().includes(q);
      const matchAssignee = t.assignees.some(a => a.toLowerCase().includes(q));
      const matchPriority = t.priority.toLowerCase().includes(q);
      if (!matchTitle && !matchAssignee && !matchPriority) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:2rem; color:#94A3B8;">No deliverables match the selected filter criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(t => {
    const pClass = t.priority.includes('P1') ? 'badge-p1' : (t.priority.includes('P2') ? 'badge-p2' : (t.priority.includes('P3') ? 'badge-p3' : 'badge-p4'));
    const sClass = t.status === 'Done' ? 'status-done' : (t.status === 'In Progress' ? 'status-wip' : (t.status === 'In Review' ? 'status-review' : (t.status === 'Backlog' ? 'status-backlog' : 'status-todo')));
    const assigneeList = t.assignees.join(', ');

    return `
      <tr>
        <td><strong>${escapeHtml(t.title)}</strong></td>
        <td><span class="table-badge ${pClass}">${escapeHtml(t.priority)}</span></td>
        <td><span class="badge-status ${sClass}">${escapeHtml(t.status)}</span></td>
        <td><span class="assignee-chip">👤 ${escapeHtml(assigneeList)}</span></td>
        <td>${escapeHtml(t.due_date)}</td>
        <td><span class="progress-mono">${t.progress_bar || '■■□□□□□□□□ 20%'}</span></td>
        <td>
          <button class="btn btn-outline btn-decompose-row" data-id="${t.id}" data-title="${escapeHtml(t.title)}" style="padding:0.25rem 0.55rem; font-size:0.75rem; margin-right:0.35rem;" title="Decompose with Notes & Pillars">🧩 Plan</button>
          <a href="https://app.notion.com/p/Task-Tracker-3fff1bcff9b88188b004f044be8090fe" target="_blank" class="btn btn-outline" style="padding:0.25rem 0.55rem; font-size:0.75rem;">View</a>
        </td>
      </tr>
    `;
  }).join('');
}

function setupEventListeners() {
  // Search Box
  const searchInput = document.getElementById('filter-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      currentSearchQuery = e.target.value.trim();
      renderTasksTable();
    });
  }

  // Assignee Pills
  document.querySelectorAll('#assignee-pills .pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#assignee-pills .pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentAssigneeFilter = btn.dataset.assignee;
      renderTasksTable();
    });
  });

  // Status Pills
  document.querySelectorAll('#status-pills .pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#status-pills .pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentStatusFilter = btn.dataset.status;
      renderTasksTable();
    });
  });

  // Refresh Sync Button
  const refreshBtn = document.getElementById('btn-refresh-data');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      refreshBtn.disabled = true;
      refreshBtn.textContent = 'Syncing...';
      await loadDashboardData();
      setTimeout(() => {
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg> Sync Data`;
        alert('Dashboard synced successfully!');
      }, 500);
    });
  }

  // AI Breakdown Presets
  document.querySelectorAll('.preset-chips .chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const title = chip.dataset.title;
      document.getElementById('breakdown-input').value = title;
      renderDecompositionPreset(title);
    });
  });

  // AI Breakdown Trigger
  const runBreakdownBtn = document.getElementById('btn-run-breakdown');
  if (runBreakdownBtn) {
    runBreakdownBtn.addEventListener('click', () => {
      const input = document.getElementById('breakdown-input').value.trim();
      if (input) {
        renderDecompositionPreset(input);
      }
    });
  }

  // Webhook Simulator Buttons
  const p1Btn = document.getElementById('btn-trigger-p1-alert');
  if (p1Btn) {
    p1Btn.addEventListener('click', () => {
      alert('🔔 [Google Chat Simulator]: Card v2 Alert dispatched for P1 SLA breach (Dashboarding Form for Various Uploads).');
    });
  }
  const digestBtn = document.getElementById('btn-trigger-digest-alert');
  if (digestBtn) {
    digestBtn.addEventListener('click', () => {
      alert('📢 [Google Chat Simulator]: Weekly Executive Digest Card v2 dispatched to space.');
    });
  }

  // Task Intake Modal
  const modal = document.getElementById('task-modal');
  const openModalBtn = document.getElementById('btn-open-task-modal');
  const closeModalBtn = document.getElementById('btn-close-modal');
  const cancelModalBtn = document.getElementById('btn-cancel-modal');
  const taskForm = document.getElementById('task-form');

  if (openModalBtn && modal) {
    openModalBtn.addEventListener('click', () => {
      modal.classList.add('open');
      const dueInput = document.getElementById('modal-due');
      if (dueInput && !dueInput.value) {
        const d = new Date();
        d.setDate(d.getDate() + 2);
        dueInput.value = d.toISOString().split('T')[0];
      }
    });
  }
  const closeModal = () => modal && modal.classList.remove('open');
  if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
  if (cancelModalBtn) cancelModalBtn.addEventListener('click', closeModal);
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });
  }

  if (taskForm) {
    taskForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const title = document.getElementById('modal-title').value.trim();
      const priority = document.getElementById('modal-priority').value;
      const complexity = document.getElementById('modal-complexity').value;
      const assignee = document.getElementById('modal-assignee').value;
      const dueDate = document.getElementById('modal-due').value;
      const notes = document.getElementById('modal-notes').value.trim();

      const newTask = {
        id: 'user_' + Date.now(),
        title: title,
        priority: priority,
        status: 'To Do',
        assignees: [assignee],
        due_date: dueDate || 'Upcoming',
        progress_bar: '■■□□□□□□□□ 20%',
        estimated_hours: 3.0
      };

      if (!dashboardData.tasks) dashboardData.tasks = [];
      dashboardData.tasks.unshift(newTask);
      if (dashboardData.priority_counts && dashboardData.priority_counts[priority] !== undefined) {
        dashboardData.priority_counts[priority]++;
      }
      if (dashboardData.status_counts) {
        dashboardData.status_counts['To Do']++;
      }
      dashboardData.total_tasks++;
      dashboardData.total_pending++;

      updateUI();
      closeModal();
      taskForm.reset();
      alert(`🎉 Deliverable "${title}" added to active queue!\nPriority: ${priority} • Owner: ${assignee}`);
    });
  }
}

// ============================================================================
// Deliverable Decomposition Studio (Human-Directed Notes & Pillars)
// ============================================================================

let currentDecompPlan = null;
const NOTION_DATABASE_ID = "3fff1bcff9b881be9e4fd3df8f014a52";

function initDecompositionStudio() {
  const taskSelect = document.getElementById('decomp-task-select');
  const notesTextarea = document.getElementById('decomp-notes-textarea');
  const insertTemplateBtn = document.getElementById('btn-insert-template');
  const clearNotesBtn = document.getElementById('btn-clear-notes');
  const parseNotesBtn = document.getElementById('btn-parse-notes');
  const copyCliBtn = document.getElementById('btn-copy-cli-command');
  const commitBtn = document.getElementById('btn-commit-subtasks-notion');
  const aiDraftBtn = document.getElementById('btn-ai-draft-gemini');
  const toggleConfigBtn = document.getElementById('btn-toggle-config');
  const configBox = document.getElementById('decomp-config-box');

  const notionTokenInput = document.getElementById('notion-api-token-input');
  const saveNotionBtn = document.getElementById('btn-save-notion-token');
  const clearNotionBtn = document.getElementById('btn-clear-notion-token');
  const notionStatusPill = document.getElementById('notion-token-status-pill');

  const geminiKeyInput = document.getElementById('gemini-api-key-input');
  const saveGeminiBtn = document.getElementById('btn-save-gemini-key');
  const clearGeminiBtn = document.getElementById('btn-clear-gemini-key');
  const geminiStatusPill = document.getElementById('gemini-key-status-pill');

  // Load saved credentials
  function refreshCredsUI() {
    const savedNotion = localStorage.getItem('notion_token');
    if (savedNotion) {
      if (notionTokenInput) notionTokenInput.value = savedNotion;
      if (notionStatusPill) {
        notionStatusPill.textContent = '🟢 Direct Sync Active';
        notionStatusPill.className = 'badge-status status-done';
      }
    } else {
      if (notionStatusPill) {
        notionStatusPill.textContent = 'Not Set';
        notionStatusPill.className = 'badge-status status-pending';
      }
    }

    const savedGemini = localStorage.getItem('gemini_api_key');
    if (savedGemini) {
      if (geminiKeyInput) geminiKeyInput.value = savedGemini;
      if (geminiStatusPill) {
        geminiStatusPill.textContent = '🟢 Gemini 1.5 Active';
        geminiStatusPill.className = 'badge-status status-done';
      }
    } else {
      if (geminiStatusPill) {
        geminiStatusPill.textContent = 'Smart Synthesizer';
        geminiStatusPill.className = 'badge-status status-pending';
      }
    }
  }

  refreshCredsUI();

  if (toggleConfigBtn && configBox) {
    toggleConfigBtn.addEventListener('click', () => {
      configBox.style.display = configBox.style.display === 'none' ? 'block' : 'none';
      if (configBox.style.display === 'block' && notionTokenInput) notionTokenInput.focus();
    });
  }

  if (saveNotionBtn && notionTokenInput) {
    saveNotionBtn.addEventListener('click', () => {
      const val = notionTokenInput.value.trim();
      if (!val) {
        alert('Please enter your Notion Integration Token (starts with secret_).');
        return;
      }
      localStorage.setItem('notion_token', val);
      refreshCredsUI();
      alert('✓ Notion Token saved! Direct sync is now active.');
    });
  }

  if (clearNotionBtn) {
    clearNotionBtn.addEventListener('click', () => {
      localStorage.removeItem('notion_token');
      if (notionTokenInput) notionTokenInput.value = '';
      refreshCredsUI();
    });
  }

  if (saveGeminiBtn && geminiKeyInput) {
    saveGeminiBtn.addEventListener('click', () => {
      const val = geminiKeyInput.value.trim();
      if (!val) {
        alert('Please enter a valid Gemini API key (starts with AIzaSy).');
        return;
      }
      localStorage.setItem('gemini_api_key', val);
      refreshCredsUI();
      alert('✓ Google Gemini API Key saved! AI drafting will now use live Gemini 1.5 Flash.');
    });
  }

  if (clearGeminiBtn) {
    clearGeminiBtn.addEventListener('click', () => {
      localStorage.removeItem('gemini_api_key');
      if (geminiKeyInput) geminiKeyInput.value = '';
      refreshCredsUI();
    });
  }

  if (aiDraftBtn) {
    aiDraftBtn.addEventListener('click', draftNotesWithGemini);
  }

  if (taskSelect) {
    taskSelect.addEventListener('change', () => {
      const opt = taskSelect.options[taskSelect.selectedIndex];
      const sizingSpan = document.getElementById('decomp-current-sizing');
      if (opt && opt.value) {
        sizingSpan.textContent = opt.dataset.complexity || 'Unrated';
        sizingSpan.className = 'badge-status ' + (opt.dataset.status === 'Done' ? 'status-done' : 'status-wip');
      } else {
        sizingSpan.textContent = 'None';
        sizingSpan.className = 'badge-status';
      }
    });
  }

  // Row "Plan" Button in Tasks Table
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-decompose-row');
    if (btn) {
      const taskId = btn.dataset.id;
      if (taskSelect) {
        taskSelect.value = taskId;
        taskSelect.dispatchEvent(new Event('change'));
      }
      const studio = document.getElementById('decomposition-studio');
      if (studio) {
        studio.scrollIntoView({ behavior: 'smooth' });
      }
      if (notesTextarea) {
        notesTextarea.focus();
      }
    }
  });

  if (insertTemplateBtn) {
    insertTemplateBtn.addEventListener('click', () => {
      const opt = taskSelect && taskSelect.options[taskSelect.selectedIndex];
      const parentTitle = (opt && opt.dataset.title) || 'Deliverable';
      notesTextarea.value = `Major Pillars:

1. Specifications & Core Architecture
- Database Schema & Data Models (2.5h, Backend, P2) — Design schema entities, indexes, and migrations for ${parentTitle}
- Core Service Pipeline & Rules (2.5h, Backend, P2) — Implement core business validation logic and error handlers

2. Client Interface & User Workflow
- Interactive Dashboard Views (3.5h, Frontend, P2) — Build responsive UI layout, interactive forms, and feedback states
- System Notifications & Webhooks (2.0h, Backend, P3) — Configure automated event triggers and alert notifications

3. Verification & Launch Hardening
- Automated Edge Case Test Suite (2.0h, QA & Security, P3) — Verify end-to-end integration flows and security boundaries
- Deployment Verification & Sign-Off (1.5h, DevOps & Infra, P4) — Staging deployment, smoke testing, and owner sign-off`;
      parseAndRenderNotes();
    });
  }

  if (clearNotesBtn) {
    clearNotesBtn.addEventListener('click', () => {
      if (notesTextarea) notesTextarea.value = '';
      currentDecompPlan = null;
      document.getElementById('subtasks-output').innerHTML = `
        <div class="empty-state-card">
          <div class="empty-icon">📝</div>
          <div class="empty-text">Select a deliverable above, enter your major pillars and execution steps, and click <b>Parse & Review Subtasks</b>.</div>
        </div>
      `;
      document.getElementById('decomp-summary-stats').style.display = 'none';
      document.getElementById('decomp-results-header').style.display = 'none';
    });
  }

  if (parseNotesBtn) {
    parseNotesBtn.addEventListener('click', parseAndRenderNotes);
  }

  if (copyCliBtn) {
    copyCliBtn.addEventListener('click', copyCliCommand);
  }

  if (commitBtn) {
    commitBtn.addEventListener('click', commitSubtasksToNotion);
  }
}

async function draftNotesWithGemini() {
  const taskSelect = document.getElementById('decomp-task-select');
  const notesTextarea = document.getElementById('decomp-notes-textarea');
  const aiDraftBtn = document.getElementById('btn-ai-draft-gemini');

  if (!taskSelect) return;
  const opt = taskSelect.options[taskSelect.selectedIndex];
  if (!opt || !opt.value) {
    alert('Please select a target deliverable from the dropdown first.');
    taskSelect.focus();
    return;
  }

  const parentTitle = opt.dataset.title || 'Deliverable';
  const originalBtnHtml = aiDraftBtn.innerHTML;
  aiDraftBtn.disabled = true;
  aiDraftBtn.innerHTML = '<span>✨ Drafting with Gemini...</span>';

  const geminiKey = localStorage.getItem('gemini_api_key');

  try {
    let generatedNotes = "";
    if (geminiKey) {
      const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiKey}`;
      const prompt = `You are a Principal Software Architect and Technical Lead.
Break down the project deliverable into a clean, modular, and professional engineering plan.

Deliverable: "${parentTitle}"

Format your response strictly using this Markdown template (do NOT wrap in code blocks):

Major Pillars:

1. <Pillar 1 Name>
- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Crisp Acceptance Criteria / Definition of Done>
- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Crisp Acceptance Criteria / Definition of Done>

2. <Pillar 2 Name>
- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Crisp Acceptance Criteria / Definition of Done>
- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Crisp Acceptance Criteria / Definition of Done>

3. <Pillar 3 Name>
- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Crisp Acceptance Criteria / Definition of Done>

Strict Guidelines for Senior-Engineer Quality:
1. Subtask Title MUST be 3 to 6 words maximum. Keep it clean and punchy (e.g. 'Visitor Schema & NDA Models', NOT 'Design visitor log database models, NDA agreements and migration scripts').
2. NEVER prefix or repeat the parent deliverable name in the subtask title.
3. Estimated hours must be realistic: between 1.5h and 4.0h each (e.g., 2h, 2.5h, 3.5h).
4. Pod MUST be one of: Backend, Frontend, DevOps & Infra, Design, QA & Security, Product.
5. Priority MUST be one of: P1, P2, P3, P4.
6. Acceptance criteria after the em-dash '—' must be exactly one clear, technical sentence stating what makes it Done.
7. Provide 4 to 6 total subtasks across 2 to 3 major pillars.`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0.35, maxOutputTokens: 1024 }
        })
      });

      if (response.ok) {
        const json = await response.json();
        const candidateText = json.candidates?.[0]?.content?.parts?.[0]?.text;
        if (candidateText) {
          generatedNotes = candidateText.replace(/^```(?:markdown)?\s*/i, '').replace(/\s*```$/i, '').trim();
        }
      } else {
        console.warn('Gemini API call returned non-200, falling back to smart synthesizer');
      }
    }

    if (!generatedNotes) {
      generatedNotes = generateSmartFallbackNotesClient(parentTitle);
    }

    if (notesTextarea) {
      notesTextarea.value = generatedNotes;
      parseAndRenderNotes();
    }
  } catch (err) {
    console.error('Error drafting notes with Gemini:', err);
    if (notesTextarea) {
      notesTextarea.value = generateSmartFallbackNotesClient(parentTitle);
      parseAndRenderNotes();
    }
  } finally {
    aiDraftBtn.disabled = false;
    aiDraftBtn.innerHTML = originalBtnHtml;
  }
}

function generateSmartFallbackNotesClient(taskTitle) {
  const t = (taskTitle || '').toLowerCase();
  if (t.includes('reception') || t.includes('visitor') || t.includes('kiosk') || t.includes('gate') || t.includes('front desk')) {
    return `Major Pillars:

1. Architecture & Security Schemas
- Visitor Schema & NDA Models (2.5h, Backend, P2) — Design Postgres tables, indexes, and encrypted storage for visitor logs & NDA records
- Overstay Event Alert Worker (2.0h, Backend, P2) — Implement automated background worker tracking visit durations and triggering alerts

2. Kiosk Experience & Hardware Drivers
- Tablet Touchscreen Check-In UI (3.5h, Frontend, P2) — Build responsive self-registration kiosk with webcam photo capture
- Thermal Badge Printer Integration (2.5h, Frontend, P3) — Generate and dispatch ESC/POS print jobs with scannable QR badge

3. Hardening & Emergency Protocol
- Host Google Chat Alert Service (2.0h, Backend, P2) — Dispatch real-time Card v2 notification to host employee upon visitor sign-in
- Emergency Evacuation Headcount Roster (1.5h, QA & Security, P3) — 1-click real-time exportable headcount roster for building safety marshals`;
  } else if (t.includes('video') || t.includes('kotak') || t.includes('media') || t.includes('film')) {
    return `Major Pillars:

1. Narrative & Visual Storyboarding
- Narrative Script & Compliance Review (2.0h, Product, P2) — Finalize messaging, hook, and regulatory compliance clearance
- Visual Storyboard & Shot List (2.5h, Design, P3) — Produce scene-by-scene framing guide with corporate banking motifs

2. Video Assembly & Motion Graphics
- A-Roll Assembly & Multitrack Sync (3.5h, Design, P2) — Assemble rough timeline cut with synchronized dialogue and B-roll
- Brand Motion Graphics & Lower-Thirds (3.0h, Design, P3) — Render animated brand title cards, lower-thirds, and transitions

3. Sound Design & Master Delivery
- Dialogue Balancing & Master Mix (1.5h, Design, P3) — Normalize vocal clarity to broadcast loudness standards
- High-Bitrate Multi-Platform Export (1.5h, DevOps & Infra, P4) — Render optimized 4K master and social cuts`;
  } else if (t.includes('dashboard') || t.includes('metric') || t.includes('upload') || t.includes('form') || t.includes('report')) {
    return `Major Pillars:

1. Ingestion & Calculation Engine
- Multi-Format File Intake Endpoint (3.0h, Backend, P2) — Build resilient upload endpoint with schema validation and sanitization
- Metric Rollup & Weighted Caching (3.0h, Backend, P2) — Implement aggregation formulas, percentile ranking, and in-memory cache

2. Visualization & Interactive Controls
- Glassmorphic KPI Grid & Charts (3.5h, Frontend, P2) — Render dynamic Chart.js visualizations with responsive breakpoints
- Column Filter & CSV Exporter (2.0h, Frontend, P3) — Implement multi-horizon filtering, search, and client-side data export

3. Security & Cross-Device Hardening
- Role-Based Scope Permissions (2.0h, QA & Security, P3) — Verify RBAC restrictions, sensitive metric masking, and audit logging
- Cross-Browser Layout Polish (1.5h, Frontend, P4) — Verify responsive behavior across mobile, tablet, and desktop viewports`;
  } else {
    return `Major Pillars:

1. Core Architecture & Specifications
- Data Schema & API Contract (3.0h, Backend, P2) — Define normalized database entities, migrations, and CRUD API specs for ${taskTitle}
- Core Logic Engine & Validation (3.0h, Backend, P2) — Implement core business logic, input validation, and structured error handling

2. Interactive UI & User Workflow
- Responsive Component Views (3.5h, Frontend, P2) — Build interactive dashboard views, forms, and responsive data tables
- User Feedback & Loading States (2.0h, Frontend, P3) — Implement progress toasts, micro-interactions, and optimistic state updates

3. Hardening, QA & Delivery
- Integration & Edge Case Test Suite (2.0h, QA & Security, P3) — Write automated test coverage for critical paths and failure modes
- CI/CD Pipeline & Staging Verification (1.5h, DevOps & Infra, P4) — Deploy to staging environment, verify health check, and tag release`;
  }
}

function populateDecomposeTaskDropdown() {
  const select = document.getElementById('decomp-task-select');
  if (!select || !dashboardData || !dashboardData.tasks) return;

  const currentVal = select.value;
  select.innerHTML = '<option value="">-- Choose Deliverable to Decompose --</option>';

  const activeTasks = dashboardData.tasks.filter(t => t.status !== 'Done' && t.status !== 'Archived');
  const otherTasks = dashboardData.tasks.filter(t => t.status === 'Done' || t.status === 'Archived');

  activeTasks.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.id;
    opt.dataset.title = t.title;
    opt.dataset.priority = t.priority;
    opt.dataset.status = t.status;
    opt.dataset.complexity = t.complexity || 'Unrated';
    opt.textContent = `${t.title} (${t.priority} • ${t.status})`;
    select.appendChild(opt);
  });

  if (otherTasks.length > 0) {
    const grp = document.createElement('optgroup');
    grp.label = "Completed / Archived";
    otherTasks.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.dataset.title = t.title;
      opt.dataset.priority = t.priority;
      opt.dataset.status = t.status;
      opt.dataset.complexity = t.complexity || 'Completed';
      opt.textContent = `✓ ${t.title} (${t.status})`;
      grp.appendChild(opt);
    });
    select.appendChild(grp);
  }

  if (currentVal) {
    select.value = currentVal;
    select.dispatchEvent(new Event('change'));
  } else if (activeTasks.length > 0) {
    select.selectedIndex = 1;
    select.dispatchEvent(new Event('change'));
  }
}

function parseAndRenderNotes() {
  const taskSelect = document.getElementById('decomp-task-select');
  const notesTextarea = document.getElementById('decomp-notes-textarea');
  if (!taskSelect || !notesTextarea) return;

  const opt = taskSelect.options[taskSelect.selectedIndex];
  if (!opt || !opt.value) {
    alert('Please select a target deliverable from the dropdown first.');
    taskSelect.focus();
    return;
  }

  const parentTitle = opt.dataset.title || 'Deliverable';
  const notesText = notesTextarea.value.trim();
  if (!notesText) {
    alert('Please enter your implementation notes and major pillars in the text box.');
    notesTextarea.focus();
    return;
  }

  const plan = parseNotesIntoSubtasksClient(parentTitle, notesText);
  currentDecompPlan = { ...plan, parent_id: opt.value };

  renderDecomposedSubtasks(currentDecompPlan);
}

function parseNotesIntoSubtasksClient(parentTitle, text) {
  const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
  const subtasks = [];
  let currentPillar = "Execution";
  let totalHours = 0.0;

  const hoursRegex = /(\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hours)\b/i;
  const prioRegex = /\b(P1|P2|P3|P4|Urgent|High|Medium|Low)\b/i;

  const podKeywords = {
    frontend: "Frontend", ui: "Frontend", ux: "Frontend", web: "Frontend", client: "Frontend",
    backend: "Backend", api: "Backend", database: "Backend", db: "Backend", sql: "Backend",
    design: "Design", figma: "Design", video: "Design", motion: "Design",
    qa: "QA & Security", security: "QA & Security", test: "QA & Security", audit: "QA & Security",
    devops: "DevOps & Infra", infra: "DevOps & Infra", cloud: "DevOps & Infra", docker: "DevOps & Infra",
    product: "Product", spec: "Product", ops: "Operations & Chores"
  };

  for (let line of lines) {
    if (/^(?:#+\s*)?(?:major\s+pillars?|implementation\s+plan|notes?)\s*:?$/i.test(line)) {
      continue;
    }

    let isPillarHeader = false;
    if (line.startsWith('#')) {
      isPillarHeader = true;
      currentPillar = line.replace(/^#+\s*/, '').trim();
    } else if (/^(?:pillar|phase|milestone|section)\s*\d*[:\s-]/i.test(line)) {
      isPillarHeader = true;
      currentPillar = line.replace(/^(?:pillar|phase|milestone|section)\s*\d*[:\s-]\s*/i, '').trim();
    } else if (/^\d+[\.:\)]\s*[A-Za-z]/.test(line) && !hoursRegex.test(line) && !line.startsWith('-')) {
      isPillarHeader = true;
      currentPillar = line.replace(/^\d+[\.:\)]\s*/, '').trim();
    }

    if (isPillarHeader) continue;

    const bulletMatch = line.match(/^(?:[-*•]\s*(?:\[[\sx]\]\s*)?|\d+[\.)]\s*)(.*)$/);
    const rawText = bulletMatch ? bulletMatch[1].trim() : line;
    if (!rawText) continue;

    const hrsMatch = rawText.match(hoursRegex);
    const hours = hrsMatch ? parseFloat(hrsMatch[1]) : 2.5;
    totalHours += hours;

    let prio = "P2 - High";
    const prMatch = rawText.match(prioRegex);
    if (prMatch) {
      const p = prMatch[1].toLowerCase();
      if (p.includes('p1') || p.includes('urgent')) prio = "P1 - Urgent";
      else if (p.includes('p2') || p.includes('high')) prio = "P2 - High";
      else if (p.includes('p3') || p.includes('medium')) prio = "P3 - Medium";
      else if (p.includes('p4') || p.includes('low')) prio = "P4 - Low";
    }

    let pod = "Backend";
    const lower = rawText.toLowerCase();
    for (let k in podKeywords) {
      if (new RegExp('\\b' + k + '\\b').test(lower)) {
        pod = podKeywords[k];
        break;
      }
    }

    // Separate clean title from acceptance criteria using em-dash '—', '--', or ':'
    let criteria = "";
    let rawTitle = rawText;
    if (rawText.includes("—")) {
      const parts = rawText.split("—");
      rawTitle = parts[0].trim();
      criteria = parts.slice(1).join("—").trim();
    } else if (rawText.includes(" -- ")) {
      const parts = rawText.split(" -- ");
      rawTitle = parts[0].trim();
      criteria = parts.slice(1).join(" -- ").trim();
    } else if (rawText.includes(":") && !/https?:\/\//i.test(rawText)) {
      const parts = rawText.split(":");
      rawTitle = parts[0].trim();
      criteria = parts.slice(1).join(":").trim();
    }

    let cleanTitle = rawTitle.replace(/[\(\[].*?[\)\]]/g, '').trim();
    cleanTitle = cleanTitle.replace(/\s+/g, ' ').replace(/^[-:\s•]+|[-:\s•]+$/g, '');
    if (!cleanTitle) cleanTitle = rawTitle.slice(0, 45).trim();

    criteria = criteria.replace(/[\(\[].*?[\)\]]/g, '').trim();
    if (!criteria) criteria = `Verified implementation of ${cleanTitle} under ${currentPillar}.`;

    let comp = "⭐⭐ 2 - Simple";
    if (hours <= 2.0) comp = "⭐ 1 - Trivial";
    else if (hours <= 4.0) comp = "⭐⭐ 2 - Simple";
    else comp = "⭐⭐⭐ 3 - Moderate";

    subtasks.push({
      title: cleanTitle,
      short_title: cleanTitle,
      estimated_hours: hours,
      priority: prio,
      team: pod,
      complexity: comp,
      pillar: currentPillar,
      acceptance_criteria: criteria
    });
  }

  let parentComp = "⭐⭐ 2 - Simple";
  if (totalHours >= 25.0) parentComp = "⭐⭐⭐⭐⭐ 5 - Epic";
  else if (totalHours >= 15.0) parentComp = "⭐⭐⭐⭐ 4 - Complex";
  else if (totalHours >= 6.0) parentComp = "⭐⭐⭐ 3 - Moderate";
  else if (totalHours >= 3.0) parentComp = "⭐⭐ 2 - Simple";
  else parentComp = "⭐ 1 - Trivial";

  return {
    parent_title: parentTitle,
    total_hours: Math.round(totalHours * 10) / 10,
    parent_complexity: parentComp,
    subtasks: subtasks,
    raw_notes: text
  };
}

function renderDecomposedSubtasks(plan) {
  const container = document.getElementById('subtasks-output');
  const summaryStats = document.getElementById('decomp-summary-stats');
  const resultsHeader = document.getElementById('decomp-results-header');
  const parentNameSpan = document.getElementById('decomp-parent-name-display');

  if (!container || !plan) return;

  if (parentNameSpan) parentNameSpan.textContent = plan.parent_title;
  if (summaryStats) {
    summaryStats.style.display = 'flex';
    document.getElementById('stat-subtask-count').textContent = `${plan.subtasks.length} Subtasks`;
    document.getElementById('stat-total-hours').textContent = `⏱️ ${plan.total_hours} hrs total`;
    document.getElementById('stat-calc-complexity').textContent = plan.parent_complexity;
  }
  if (resultsHeader) resultsHeader.style.display = 'flex';

  if (plan.subtasks.length === 0) {
    container.innerHTML = `
      <div class="empty-state-card">
        <div class="empty-icon">⚠️</div>
        <div class="empty-text">Could not identify any subtask bullet points. Please add lines starting with <code>-</code> with task details.</div>
      </div>
    `;
    return;
  }

  container.innerHTML = plan.subtasks.map((st, i) => {
    const pClass = st.priority.includes('P1') ? 'badge-p1' : (st.priority.includes('P2') ? 'badge-p2' : (st.priority.includes('P3') ? 'badge-p3' : 'badge-p4'));
    return `
      <div class="subtask-card">
        <div class="subtask-top">
          <span class="table-badge ${pClass}">${st.priority}</span>
          <span class="pillar-tag">${escapeHtml(st.pillar)}</span>
        </div>
        <div class="subtask-title">${i + 1}. ${escapeHtml(st.title)}</div>
        <span class="parent-tag">🔗 Parent: ${escapeHtml(plan.parent_title)}</span>
        <div class="subtask-desc">🎯 ${escapeHtml(st.acceptance_criteria)}</div>
        <div class="subtask-meta">
          <span>⏱️ ${st.estimated_hours} hrs</span>
          <span>Pod: <b>${escapeHtml(st.team)}</b></span>
          <span>${st.complexity}</span>
        </div>
      </div>
    `;
  }).join('');
}

async function commitSubtasksToNotion() {
  if (!currentDecompPlan || !currentDecompPlan.subtasks || currentDecompPlan.subtasks.length === 0) {
    alert('Please parse your notes into subtasks before creating them.');
    return;
  }

  let notionToken = localStorage.getItem('notion_token');
  if (!notionToken || !notionToken.trim()) {
    const entered = prompt(
      "🔑 Notion Integration Token Required:\n\n" +
      "To create subtasks directly in your Notion database, please paste your Notion API token (starts with secret_):\n\n" +
      "(This is saved securely in your browser's local storage so you never have to re-type it)"
    );
    if (entered && entered.trim()) {
      notionToken = entered.trim();
      localStorage.setItem('notion_token', notionToken);
      const notionStatusPill = document.getElementById('notion-token-status-pill');
      if (notionStatusPill) {
        notionStatusPill.textContent = '🟢 Direct Sync Active';
        notionStatusPill.className = 'badge-status status-done';
      }
    } else {
      alert("⚠️ Direct Notion sync cancelled. You can also run the 1-click CLI command by clicking 'Copy CLI Command'.");
      const configBox = document.getElementById('decomp-config-box');
      if (configBox) configBox.style.display = 'block';
      return;
    }
  }

  const commitBtn = document.getElementById('btn-commit-subtasks-notion');
  const originalText = commitBtn ? commitBtn.innerHTML : '';
  if (commitBtn) {
    commitBtn.disabled = true;
    commitBtn.innerHTML = '<span>⏳ Connecting to Notion API...</span>';
  }

  const cleanParentId = currentDecompPlan.parent_id.replace(/-/g, '');
  const total = currentDecompPlan.subtasks.length;
  let successCount = 0;

  try {
    for (let i = 0; i < total; i++) {
      const st = currentDecompPlan.subtasks[i];
      if (commitBtn) {
        commitBtn.innerHTML = `<span>⏳ Creating ${i + 1}/${total}: ${escapeHtml(st.title.slice(0, 22))}...</span>`;
      }

      const pagePayload = {
        parent: { database_id: NOTION_DATABASE_ID },
        properties: {
          "Task Name": { title: [{ text: { content: st.title } }] },
          "Priority": { select: { name: st.priority } },
          "Status": { status: { name: "To Do" } },
          "Complexity": { select: { name: st.complexity } },
          "Estimated Hours": { number: st.estimated_hours },
          "Team / Pod": { select: { name: st.team } },
          "Parent Task": { relation: [{ id: cleanParentId }] },
          "Task Details": { rich_text: [{ text: { content: `🎯 [${st.pillar}] ${st.acceptance_criteria}` } }] }
        },
        icon: { type: "emoji", emoji: "🔹" }
      };

      const resp = await fetch("https://api.notion.com/v1/pages", {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + notionToken,
          "Notion-Version": "2022-06-28",
          "Content-Type": "application/json"
        },
        body: JSON.stringify(pagePayload)
      });

      if (!resp.ok) {
        const errJson = await resp.json().catch(() => ({}));
        throw new Error(errJson.message || `Notion HTTP ${resp.status}`);
      }
      successCount++;
    }

    // Update parent task Estimated Hours and Complexity
    if (commitBtn) {
      commitBtn.innerHTML = `<span>⏳ Updating parent deliverable metrics...</span>`;
    }

    await fetch(`https://api.notion.com/v1/pages/${cleanParentId}`, {
      method: "PATCH",
      headers: {
        "Authorization": "Bearer " + notionToken,
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        properties: {
          "Estimated Hours": { number: currentDecompPlan.total_hours },
          "Complexity": { select: { name: currentDecompPlan.parent_complexity } }
        }
      })
    }).catch(e => console.warn('Parent patch warning:', e));

    alert(`🎉 Success! Created ${successCount} subtasks directly in Notion linked to "${currentDecompPlan.parent_title}".`);

    // Add created subtasks to local tasks array for instant UI update
    currentDecompPlan.subtasks.forEach((st, idx) => {
      dashboardData.tasks.unshift({
        id: `sub_${Date.now()}_${idx}`,
        title: st.title,
        priority: st.priority,
        status: 'To Do',
        assignees: ['Unassigned'],
        due_date: 'Sprint Horizon',
        progress_bar: '■■□□□□□□□□ 20%',
        estimated_hours: st.estimated_hours,
        complexity: st.complexity
      });
      dashboardData.total_tasks++;
      dashboardData.total_pending++;
    });

    updateUI();
  } catch (err) {
    console.error('Error committing subtasks:', err);
    alert(`⚠️ Notion API error: ${err.message}\n\nPlease verify your Notion Integration Token has access to the database, or use the 1-click terminal command.`);
  } finally {
    if (commitBtn) {
      commitBtn.disabled = false;
      commitBtn.innerHTML = originalText;
    }
  }
}

function copyCliCommand() {
  const taskSelect = document.getElementById('decomp-task-select');
  const notesTextarea = document.getElementById('decomp-notes-textarea');
  if (!taskSelect || !notesTextarea) return;

  const opt = taskSelect.options[taskSelect.selectedIndex];
  const parentTitle = (opt && opt.dataset.title) || 'Deliverable';
  const notes = notesTextarea.value.trim();

  if (!notes) {
    alert('Please enter your implementation notes and pillars first.');
    notesTextarea.focus();
    return;
  }

  const cleanNotes = notes.replace(/"/g, '\\"').replace(/\n/g, '\\n');
  const cmd = `python3 -m notion_hub.cli decompose --task "${parentTitle}" --notes "${cleanNotes}" --apply`;

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(cmd).then(() => {
      alert(`📋 Copied terminal command to clipboard!\n\nRun it anytime:\n${cmd}`);
    }).catch(() => {
      prompt('Copy this CLI command to execute:', cmd);
    });
  } else {
    prompt('Copy this CLI command to execute:', cmd);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
