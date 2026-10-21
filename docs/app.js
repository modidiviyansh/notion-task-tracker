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
  renderDecompositionPreset('Reception Management System');
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
          <a href="https://app.notion.com/p/Task-Tracker-3fff1bcff9b88188b004f044be8090fe" target="_blank" class="btn btn-outline" style="padding:0.25rem 0.6rem; font-size:0.75rem;">View</a>
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

function renderDecompositionPreset(title) {
  const container = document.getElementById('subtasks-output');
  if (!container) return;

  const isVideo = title.toLowerCase().includes('video');
  const isDashboard = title.toLowerCase().includes('dashboard') || title.toLowerCase().includes('form');

  let subtasks = [];
  if (isVideo) {
    subtasks = [
      { name: 'Scripting, Storyboard & Visual Narrative', hours: 2.5, prio: 'P2 - High', team: 'Design', desc: 'Narrative structure, key message beats, and asset list.' },
      { name: 'Raw Footage Assembly & Rough Cut', hours: 3.5, prio: 'P2 - High', team: 'Design', desc: 'Timeline editing, transitions, and audio pacing.' },
      { name: 'Motion Graphics, Titles & Brand Polish', hours: 2.5, prio: 'P3 - Medium', team: 'Design', desc: 'Title animations, lower-thirds, and visual effects.' },
      { name: 'Final Audio Mastering & Multi-Platform Export', hours: 1.5, prio: 'P3 - Medium', team: 'Design', desc: 'Sound normalization and high-bitrate encodes.' }
    ];
  } else if (isDashboard) {
    subtasks = [
      { name: 'Data Aggregation & Metric Calculation Logic', hours: 2.5, prio: 'P2 - High', team: 'Backend', desc: 'Calculation formulas, weighted scores, and query filters.' },
      { name: 'Visual Layout Grid & Interactive KPI Cards', hours: 2.5, prio: 'P2 - High', team: 'Frontend', desc: 'Responsive card grid, status indicators, and typography.' },
      { name: 'Multi-Horizon Filters & Text Search Engine', hours: 3.0, prio: 'P3 - Medium', team: 'Frontend', desc: 'Dynamic filtering by assignee, priority, and date range.' },
      { name: 'User Testing & Cross-Device Polish', hours: 1.5, prio: 'P4 - Low', team: 'QA & Security', desc: 'Verification on desktop and mobile browsers.' }
    ];
  } else {
    // System / ERP Archetype
    subtasks = [
      { name: 'Architecture & Data Schema Modeling', hours: 3.0, prio: 'P2 - High', team: 'Backend', desc: 'Entity relationships, schema constraints, and state transitions.' },
      { name: 'Core Backend API & Logic Implementation', hours: 4.5, prio: 'P2 - High', team: 'Backend', desc: 'Validation logic, CRUD endpoints, and access control.' },
      { name: 'User Interface & Interactive Workflows', hours: 3.5, prio: 'P3 - Medium', team: 'Frontend', desc: 'Responsive dashboard views, forms, and feedback states.' },
      { name: 'Integration Testing, Permissions & Audit Logging', hours: 2.0, prio: 'P3 - Medium', team: 'QA & Security', desc: 'RBAC permissions, audit trail logging, and edge case tests.' }
    ];
  }

  container.innerHTML = subtasks.map((st, i) => {
    const pClass = st.prio.includes('P1') ? 'badge-p1' : (st.prio.includes('P2') ? 'badge-p2' : (st.prio.includes('P3') ? 'badge-p3' : 'badge-p4'));
    return `
      <div class="subtask-card">
        <div class="subtask-top">
          <span class="table-badge ${pClass}">${st.prio}</span>
          <span class="chip" style="margin:0;">${st.team}</span>
        </div>
        <div class="subtask-title">${i + 1}. ${escapeHtml(title)} — ${escapeHtml(st.name)}</div>
        <div class="subtask-desc">${escapeHtml(st.desc)}</div>
        <div class="subtask-meta">
          <span>⏱️ ${st.hours} hrs effort</span>
          <span>Complexity: 3 ⭐</span>
        </div>
      </div>
    `;
  }).join('');
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
