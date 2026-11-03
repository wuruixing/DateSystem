let currentPage = 1;
let searchKeyword = '';
let currentProject = '';

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadDashboard();
    loadProjects();
    loadReminders();
    bindEvents();
});

function bindEvents() {
    document.getElementById('searchInput').addEventListener('input', debounce(function() {
        searchKeyword = this.value.trim();
        currentPage = 1;
        loadReminders();
    }, 300));

    document.getElementById('saveReminder').addEventListener('click', saveReminder);
}

// ==================== 监控面板 ====================

function loadDashboard() {
    fetch('/api/dashboard')
        .then(r => r.json())
        .then(data => {
            if (data.code === 0) renderDashboard(data.data);
        });
}

function renderDashboard(d) {
    document.getElementById('todayDue').textContent = d.today_due;
    document.getElementById('weekDue').textContent = d.week_due;
    document.getElementById('monthDue').textContent = d.month_due;
    document.getElementById('overdue').textContent = d.overdue;

    const ps = document.getElementById('projectStats');
    if (d.project_stats.length === 0) {
        ps.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:1rem;width:100%">暂无项目，点击上方「新建项目」创建</p>';
    } else {
        ps.innerHTML = d.project_stats.map(p => `
            <div class="project-stat-card">
                <div class="project-stat-color" style="background:${p.color}"></div>
                <div class="project-stat-info">
                    <div class="project-stat-name">${escapeHtml(p.name)}</div>
                    <div class="project-stat-count">${p.count} <small style="font-size:0.8rem;color:var(--text-secondary)">个提醒</small></div>
                </div>
            </div>
        `).join('');
    }
}

// ==================== 统计 ====================

function loadStats() {
    fetch('/api/stats')
        .then(r => r.json())
        .then(data => {
            if (data.code === 0) {
                animateNumber('totalReminders', data.data.total_reminders);
                animateNumber('activeReminders', data.data.active_reminders);
                animateNumber('totalLogs', data.data.total_logs);
                animateNumber('successLogs', data.data.success_logs);
            }
        });
}

function animateNumber(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const current = parseInt(el.textContent) || 0;
    const diff = target - current;
    const steps = 20;
    let step = 0;
    const timer = setInterval(() => {
        step++;
        if (step >= steps) { el.textContent = target; clearInterval(timer); }
        else { el.textContent = Math.round(current + (diff / steps) * step); }
    }, 30);
}

// ==================== 项目 ====================

function loadProjects() {
    fetch('/api/projects')
        .then(r => r.json())
        .then(data => {
            if (data.code === 0) {
                renderProjectTabs(data.data);
                renderProjectSelect(data.data);
            }
        });
}

function renderProjectTabs(projects) {
    const container = document.getElementById('projectTabs');
    let html = `<button class="project-tab ${currentProject === '' ? 'active' : ''}" data-project="" onclick="filterByProject('')">全部</button>`;
    projects.forEach(p => {
        html += `<button class="project-tab ${currentProject == p.id ? 'active' : ''}" data-project="${p.id}" onclick="filterByProject(${p.id})" style="border-left: 3px solid ${p.color}">${escapeHtml(p.name)}</button>`;
    });
    container.innerHTML = html;
}

function renderProjectSelect(projects) {
    const select = document.getElementById('projectId');
    select.innerHTML = '<option value="">未分组</option>' +
        projects.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('');
}

function filterByProject(projectId) {
    currentProject = projectId;
    currentPage = 1;
    loadProjects();
    loadReminders();
}

function openProjectModal() {
    document.getElementById('projectName').value = '';
    document.querySelector('input[name="projectColor"][value="#6366f1"]').checked = true;
    new bootstrap.Modal(document.getElementById('projectModal')).show();
}

function saveProject() {
    const name = document.getElementById('projectName').value.trim();
    if (!name) return showToast('请输入项目名称');

    const color = document.querySelector('input[name="projectColor"]:checked').value;

    fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, color })
    })
    .then(r => r.json())
    .then(data => {
        if (data.code === 0) {
            showToast('项目创建成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('projectModal')).hide();
            loadProjects();
            loadDashboard();
        } else {
            showToast(data.msg);
        }
    });
}

// ==================== 提醒卡片 ====================

function loadReminders() {
    const url = `/api/reminders?page=${currentPage}&per_page=100&keyword=${encodeURIComponent(searchKeyword)}&project_id=${currentProject}`;
    fetch(url)
        .then(r => r.json())
        .then(data => {
            if (data.code === 0) renderCards(data.data.list);
        });
}

function renderCards(reminders) {
    const container = document.getElementById('reminderCards');

    if (reminders.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="bi bi-calendar-x"></i><p>暂无提醒记录</p></div>';
        return;
    }

    container.innerHTML = reminders.map(r => {
        const daysLeft = getDaysLeft(r.target_date);
        const cc = daysLeft < 0 ? 'countdown-overdue' : daysLeft === 0 ? 'countdown-today' : daysLeft <= 3 ? 'countdown-soon' : 'countdown-normal';
        const ct = daysLeft < 0 ? `已过期${Math.abs(daysLeft)}天` : daysLeft === 0 ? '今天' : daysLeft === 1 ? '明天' : `还有${daysLeft}天`;

        return `
            <div class="reminder-card" style="--card-color: ${r.project_color}">
                <div class="card-header-row">
                    <span class="card-project">${escapeHtml(r.project_name)}</span>
                    <span class="card-status ${r.is_active ? 'active' : 'inactive'}">${r.is_active ? '启用' : '停用'}</span>
                </div>
                <div class="card-title">${escapeHtml(r.title)}</div>
                <div class="card-date">
                    <i class="bi bi-calendar"></i>
                    <span class="date-value">${r.target_date}</span>
                    <span class="countdown-badge ${cc}">${ct}</span>
                </div>
                <div class="card-meta">
                    <span class="card-meta-item"><i class="bi bi-clock"></i> 提前${r.reminder_days.split(',').join('/')}天</span>
                    <span class="card-meta-item"><i class="bi bi-bell"></i> ${r.reminder_times}</span>
                    ${r.mention_list ? `<span class="card-meta-item"><i class="bi bi-person"></i> @${r.mention_list}</span>` : ''}
                </div>
                ${r.note ? `<div class="card-note"><i class="bi bi-sticky"></i> ${escapeHtml(r.note)}</div>` : ''}
                <div class="card-actions">
                    <button class="action-btn" onclick="sendNow(${r.id})" title="立即发送"><i class="bi bi-send-fill"></i></button>
                    <button class="action-btn" onclick="viewLogs(${r.id})" title="日志"><i class="bi bi-clock-history"></i></button>
                    <button class="action-btn" onclick="editReminder(${r.id})" title="编辑"><i class="bi bi-pencil"></i></button>
                    <button class="action-btn delete" onclick="deleteReminder(${r.id})" title="删除"><i class="bi bi-trash"></i></button>
                </div>
            </div>
        `;
    }).join('');
}

// ==================== 提醒操作 ====================

function openReminderModal() {
    resetForm();
    new bootstrap.Modal(document.getElementById('reminderModal')).show();
}

function saveReminder() {
    const id = document.getElementById('reminderId').value;
    const title = document.getElementById('title').value.trim();
    const targetDate = document.getElementById('targetDate').value;

    if (!title) return showToast('请输入标题');
    if (!targetDate) return showToast('请选择目标日期');

    const reminderDays = Array.from(document.querySelectorAll('.reminder-day:checked')).map(el => el.value).join(',');
    const reminderTimes = Array.from(document.querySelectorAll('.reminder-time:checked')).map(el => el.value).join(',');

    if (!reminderDays) return showToast('请至少选择一个提前提醒天数');
    if (!reminderTimes) return showToast('请至少选择一个提醒时间');

    const projectId = document.getElementById('projectId').value;

    const data = {
        title, target_date: targetDate,
        project_id: projectId ? parseInt(projectId) : null,
        reminder_days: reminderDays, reminder_times: reminderTimes,
        note: document.getElementById('note').value.trim(),
        mention_list: document.getElementById('mentionList').value.trim(),
        is_active: document.getElementById('isActive').checked
    };

    fetch(id ? `/api/reminders/${id}` : '/api/reminders', {
        method: id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(data => {
        if (data.code === 0) {
            showToast(id ? '更新成功' : '创建成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('reminderModal')).hide();
            loadReminders();
            loadStats();
            loadDashboard();
            loadProjects();
        } else {
            showToast(data.msg);
        }
    });
}

function editReminder(id) {
    fetch(`/api/reminders/${id}`)
        .then(r => r.json())
        .then(data => {
            if (data.code === 0) {
                const r = data.data;
                document.getElementById('reminderId').value = r.id;
                document.getElementById('title').value = r.title;
                document.getElementById('targetDate').value = r.target_date;
                document.getElementById('note').value = r.note;
                document.getElementById('mentionList').value = r.mention_list;
                document.getElementById('isActive').checked = r.is_active;
                document.getElementById('projectId').value = r.project_id || '';

                document.querySelectorAll('.reminder-day').forEach(el => { el.checked = r.reminder_days.split(',').includes(el.value); });
                document.querySelectorAll('.reminder-time').forEach(el => { el.checked = r.reminder_times.split(',').includes(el.value); });

                document.getElementById('reminderModalTitle').innerHTML = '<i class="bi bi-pencil"></i> 编辑提醒';
                new bootstrap.Modal(document.getElementById('reminderModal')).show();
            }
        });
}

function deleteReminder(id) {
    if (!confirm('确定删除这条提醒吗？')) return;
    fetch(`/api/reminders/${id}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(data => {
            if (data.code === 0) {
                showToast('删除成功', 'success');
                loadReminders();
                loadStats();
            }
        });
}

function resetForm() {
    document.getElementById('reminderId').value = '';
    document.getElementById('title').value = '';
    document.getElementById('targetDate').value = '';
    document.getElementById('note').value = '';
    document.getElementById('mentionList').value = '';
    document.getElementById('isActive').checked = true;
    document.getElementById('projectId').value = '';
    document.querySelectorAll('.reminder-day, .reminder-time').forEach(el => { el.checked = false; });
    document.getElementById('reminderModalTitle').innerHTML = '<i class="bi bi-plus-circle"></i> 新建提醒';
}

// ==================== 日志 ====================

function viewLogs(reminderId) {
    fetch(`/api/reminders/${reminderId}/logs`)
        .then(r => r.json())
        .then(data => {
            if (data.code === 0) {
                const container = document.getElementById('logsList');
                if (data.data.length === 0) {
                    container.innerHTML = '<div class="empty-state"><p>暂无发送记录</p></div>';
                } else {
                    container.innerHTML = data.data.map(log => `
                        <div class="log-item">
                            <div class="log-time">${log.send_date} ${log.send_time}</div>
                            <span class="log-status ${log.status}">${log.status === 'success' ? '成功' : '失败'}</span>
                            <div class="log-message">${escapeHtml(log.message || '')}</div>
                        </div>
                    `).join('');
                }
                new bootstrap.Modal(document.getElementById('logsModal')).show();
            }
        });
}

// ==================== 配置 ====================

function sendNow(reminderId) {
    if (!confirm('确定立即发送这条提醒吗？')) return;
    fetch(`/api/reminders/${reminderId}/send-now`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            showToast(data.msg, data.code === 0 ? 'success' : 'error');
            if (data.code === 0) loadStats();
        });
}

function openConfigModal() {
    fetch('/api/config')
        .then(r => r.json())
        .then(data => {
            if (data.code === 0) {
                document.getElementById('webhookUrl').value = data.data.wechat_webhook_url || '';
                new bootstrap.Modal(document.getElementById('configModal')).show();
            }
        });
}

function saveConfig() {
    const webhookUrl = document.getElementById('webhookUrl').value.trim();
    if (!webhookUrl) return showToast('请输入 Webhook 地址');

    fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ wechat_webhook_url: webhookUrl })
    })
    .then(r => r.json())
    .then(data => {
        if (data.code === 0) {
            showToast('配置保存成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('configModal')).hide();
        } else {
            showToast(data.msg);
        }
    });
}

function testWechat() {
    fetch('/api/test-wechat', { method: 'POST' })
        .then(r => r.json())
        .then(data => showToast(data.msg, data.code === 0 ? 'success' : 'error'))
        .catch(() => showToast('测试失败'));
}

// ==================== 工具函数 ====================

function getDaysLeft(dateStr) {
    const target = new Date(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    target.setHours(0, 0, 0, 0);
    return Math.ceil((target - today) / (1000 * 60 * 60 * 24));
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastBody = document.getElementById('toastBody');
    toastBody.textContent = message;
    toast.className = 'toast';
    toast.classList.add(type === 'success' ? 'text-bg-success' : type === 'error' ? 'text-bg-danger' : 'text-bg-primary');
    new bootstrap.Toast(toast).show();
}
