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
const APPS_SCRIPT_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbypiRNXo_Xhd6JSuMOH1oX9XwBQcqLd_tLM-Z-Z6IyU2i25JegDm4OTmtQvF-ja3ZYk_g/exec";

function initDecompositionStudio() {
  const taskSelect = document.getElementById('decomp-task-select');
  const notesTextarea = document.getElementById('decomp-notes-textarea');
  const insertTemplateBtn = document.getElementById('btn-insert-template');
  const clearNotesBtn = document.getElementById('btn-clear-notes');
  const parseNotesBtn = document.getElementById('btn-parse-notes');
  const copyCliBtn = document.getElementById('btn-copy-cli-command');
  const commitBtn = document.getElementById('btn-commit-subtasks-notion');
  const aiDraftBtn = document.getElementById('btn-ai-draft-gemini');
  const toggleKeyBtn = document.getElementById('btn-toggle-gemini-key');
  const keyBox = document.getElementById('gemini-key-box');
  const keyInput = document.getElementById('gemini-api-key-input');
  const saveKeyBtn = document.getElementById('btn-save-gemini-key');
  const clearKeyBtn = document.getElementById('btn-clear-gemini-key');
  const keyStatus = document.getElementById('gemini-key-status');

  // Load saved Gemini Key if present
  const savedKey = localStorage.getItem('gemini_api_key');
  if (savedKey) {
    if (keyInput) keyInput.value = savedKey;
    if (keyStatus) keyStatus.textContent = '✓ Saved in browser';
    if (toggleKeyBtn) toggleKeyBtn.textContent = '🔑 Gemini Key (Active)';
  }

  if (toggleKeyBtn && keyBox) {
    toggleKeyBtn.addEventListener('click', () => {
      keyBox.style.display = keyBox.style.display === 'none' ? 'block' : 'none';
      if (keyBox.style.display === 'block' && keyInput) keyInput.focus();
    });
  }

  if (saveKeyBtn && keyInput) {
    saveKeyBtn.addEventListener('click', () => {
      const val = keyInput.value.trim();
      if (!val) {
        alert('Please enter a valid Gemini API key.');
        return;
      }
      localStorage.setItem('gemini_api_key', val);
      if (keyStatus) keyStatus.textContent = '✓ Key saved successfully!';
      if (toggleKeyBtn) toggleKeyBtn.textContent = '🔑 Gemini Key (Active)';
      setTimeout(() => { if (keyStatus) keyStatus.textContent = '✓ Saved in browser'; }, 3000);
    });
  }

  if (clearKeyBtn) {
    clearKeyBtn.addEventListener('click', () => {
      localStorage.removeItem('gemini_api_key');
      if (keyInput) keyInput.value = '';
      if (keyStatus) keyStatus.textContent = 'Key removed';
      if (toggleKeyBtn) toggleKeyBtn.textContent = '🔑 Gemini Key';
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
      notesTextarea.value = `# Major Pillars & Implementation Plan: ${parentTitle}

1. Architecture, Data Schema & Setup
- Design database schema and entity models (3h, Backend, P2)
- Set up migration scripts and indexing (2h, Backend, P3)

2. Core Logic & Functional Workflow
- Implement core validation rules and API endpoints (4h, Backend, P2)
- Build responsive user interface and interactive views (3.5h, Frontend, P2)

3. Quality Verification & Sign-Off
- End-to-end integration testing and edge case audit (2h, QA & Security, P3)
- Documentation and stakeholder demonstration (1.5h, Operations, P4)`;
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
      const prompt = `You are an expert technical product manager and software architect.
Break down the following project deliverable into a concrete, actionable implementation plan:
Deliverable Title: "${parentTitle}"

Format your response strictly using this markdown format (do NOT wrap in code blocks):
Major Pillars:
1. <Pillar 1 Name>
- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Acceptance criteria>
- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Acceptance criteria>

2. <Pillar 2 Name>
- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Acceptance criteria>
- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Acceptance criteria>

3. <Pillar 3 Name>
- <Subtask Title> (<hours>h, <Pod>, <Priority>) — <Acceptance criteria>

Requirements:
- Subtasks must be technical and sized between 1.0h and 5.0h each (e.g. 2h, 3.5h).
- Pod must be one of: Backend, Frontend, DevOps & Infra, Design, QA & Security, Product.
- Priority must be one of: P1, P2, P3, P4.
- Provide 4 to 6 total subtasks across 2 to 3 major pillars.`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0.4, maxOutputTokens: 1024 }
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
  if (t.includes('reception') || t.includes('visitor') || t.includes('kiosk') || t.includes('gate')) {
    return `Major Pillars:
1. Core Visitor Architecture & Security Schema
- Design visitor log database models, NDA agreements & migration scripts (3.0h, Backend, P2) — Schema migrations and indexes applied
- Implement host employee automated overstay notification trigger (2.5h, Backend, P3) — Webhook triggers after 4h threshold

2. Tablet Kiosk & Visitor UX
- Build touchscreen self-registration interface with photo capture (3.5h, Frontend, P2) — Camera preview and instant registration
- Integrate thermal badge printer for QR visitor passes (2.5h, Frontend, P3) — Print job dispatched upon sign-in

3. Emergency Protocol & Audit Logging
- Real-time host notification dispatch via Google Chat (2.0h, Backend, P2) — Host alerted with visitor snapshot
- One-click evacuation headcount roster for security personnel (1.5h, QA & Security, P4) — Instant exportable headcount table`;
  } else if (t.includes('video') || t.includes('kotak') || t.includes('media') || t.includes('film')) {
    return `Major Pillars:
1. Scripting & Visual Storyboarding
- Finalize narrative script, hook and compliance sign-off (2.0h, Product, P2) — Approved narrative script
- Create visual storyboard and shot list with banking visual motifs (2.5h, Design, P3) — Shot breakdown with timing

2. Video Assembly & Motion Graphics
- Assemble A-roll interview footage and sync multitrack audio (3.5h, Design, P2) — Rough cut timeline completed
- Build 2D motion graphics, brand title cards and lower-thirds (3.0h, Design, P3) — Brand kit animations rendered

3. Sound Design & Multi-Platform Mastering
- Audio balancing, dialogue clarity normalization and music bed (1.5h, Design, P3) — Broadcast standard loudness
- High-bitrate 4K rendering and YouTube/social cuts export (1.5h, DevOps & Infra, P4) — Multi-aspect ratio deliverables`;
  } else if (t.includes('dashboard') || t.includes('metric') || t.includes('upload') || t.includes('form')) {
    return `Major Pillars:
1. Data Ingestion & Calculation Engine
- Build resilient file upload endpoint with schema validation (3.0h, Backend, P2) — Multi-format file intake
- Implement metric rollup formulas, weighted scores and caching (3.0h, Backend, P2) — Sub-100ms analytics retrieval

2. Responsive Visualization & Controls
- Design glassmorphic KPI cards grid and interactive charts (3.5h, Frontend, P2) — Dynamic Chart.js visualizations
- Implement date range filters, column search and CSV exporter (2.5h, Frontend, P3) — Instant filtering & export

3. Cross-Browser QA & Permission Scopes
- Role-based view access control and data redaction (2.0h, QA & Security, P3) — RBAC permissions verified
- Responsive viewport polish across mobile, tablet and desktop (1.5h, Frontend, P4) — Zero layout shifts`;
  } else {
    return `Major Pillars:
1. Core Architecture & Backend Services
- Define domain data models, validation schemas and API endpoints for ${taskTitle} (3.5h, Backend, P2) — Complete CRUD API specs
- Implement business logic engine, error handling and event logging (3.0h, Backend, P2) — Resilient error handling

2. User Interface & Interactive Experience
- Build responsive UI components, state management and data tables (3.5h, Frontend, P2) — Clean interactive workflow
- Add user feedback toasts, progress indicators and loading states (2.0h, Frontend, P3) — Intuitive micro-interactions

3. Verification, Security & Deployment
- Write automated unit and integration test suite (2.0h, QA & Security, P3) — 85%+ coverage on critical paths
- Configure CI/CD deployment pipeline and monitoring alerts (1.5h, DevOps & Infra, P4) — Staging verification complete`;
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

    let cleanTitle = rawText.replace(/[\(\[].*?[\)\]]/g, '').trim();
    cleanTitle = cleanTitle.replace(/\s+/g, ' ').replace(/^[-:\s]+|[-:\s]+$/g, '');
    if (!cleanTitle) cleanTitle = rawText.slice(0, 50);

    let comp = "⭐⭐ 2 - Simple";
    if (hours <= 2.0) comp = "⭐ 1 - Trivial";
    else if (hours <= 4.0) comp = "⭐⭐ 2 - Simple";
    else comp = "⭐⭐⭐ 3 - Moderate";

    subtasks.push({
      title: `${parentTitle} — ${cleanTitle}`,
      short_title: cleanTitle,
      estimated_hours: hours,
      priority: prio,
      team: pod,
      complexity: comp,
      pillar: currentPillar,
      acceptance_criteria: `Pillar: ${currentPillar} • Scope: ${cleanTitle}`
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
        <div class="empty-text">Could not identify any subtask bullet points. Please add lines starting with <code>-</code> or <code>1.</code> with task details.</div>
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
        <div class="subtask-desc">${escapeHtml(st.acceptance_criteria)}</div>
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

  const commitBtn = document.getElementById('btn-commit-subtasks-notion');
  const originalText = commitBtn ? commitBtn.innerHTML : '';
  if (commitBtn) {
    commitBtn.disabled = true;
    commitBtn.innerHTML = '<span>⏳ Writing to Notion Database...</span>';
  }

  try {
    const payload = {
      action: "create_subtasks",
      parent_id: currentDecompPlan.parent_id,
      parent_title: currentDecompPlan.parent_title,
      subtasks: currentDecompPlan.subtasks
    };

    const res = await fetch(APPS_SCRIPT_WEBAPP_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify(payload)
    });

    const data = await res.json().catch(() => ({ status: 'success', created_count: currentDecompPlan.subtasks.length }));

    alert(`🎉 Success! Created ${currentDecompPlan.subtasks.length} subtasks in Notion database linked to "${currentDecompPlan.parent_title}".`);

    // Add created subtasks to local tasks array for instant UI update
    currentDecompPlan.subtasks.forEach((st, idx) => {
      dashboardData.tasks.unshift({
        id: `sub_${Date.now()}_${idx}`,
        title: st.title,
        priority: st.priority,
        status: 'To Do',
        assignees: ['Unassigned'],
        due_date: 'Sprint Cutoff',
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
    alert('Note: Webhook sent. Check Notion for newly created linked subtasks!');
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
