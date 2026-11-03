// 监控面板 JavaScript
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

function loadDashboard() {
    fetch('/api/dashboard')
        .then(r => r.json())
        .then(data => {
            if (data.code === 0) renderDashboard(data.data);
        });
}

function renderDashboard(d) {
    // 概览数字
    document.getElementById('todayDue').textContent = d.today_due;
    document.getElementById('weekDue').textContent = d.week_due;
    document.getElementById('monthDue').textContent = d.month_due;
    document.getElementById('overdue').textContent = d.overdue;

    // 项目统计
    const ps = document.getElementById('projectStats');
    if (d.project_stats.length === 0) {
        ps.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:2rem">暂无项目</p>';
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

    // 即将到期
    const ul = document.getElementById('upcomingList');
    if (d.upcoming.length === 0) {
        ul.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:2rem">暂无即将到期的提醒</p>';
    } else {
        ul.innerHTML = d.upcoming.map(r => {
            const days = getDaysLeft(r.target_date);
            const cc = days === 0 ? 'countdown-today' : days <= 3 ? 'countdown-soon' : 'countdown-normal';
            const ct = days === 0 ? '今天' : days === 1 ? '明天' : `${days}天后`;
            return `
                <div class="upcoming-item">
                    <div class="upcoming-date">${r.target_date}</div>
                    <div class="upcoming-title">${escapeHtml(r.title)}</div>
                    <span class="upcoming-countdown ${cc}">${ct}</span>
                </div>
            `;
        }).join('');
    }

    // 最近日志
    const rl = document.getElementById('recentLogs');
    if (d.recent_logs.length === 0) {
        rl.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:2rem">暂无发送记录</p>';
    } else {
        rl.innerHTML = d.recent_logs.map(log => `
            <div class="recent-log-item">
                <div class="recent-log-time">${log.send_date} ${log.send_time}</div>
                <span class="recent-log-status ${log.status}">${log.status === 'success' ? '成功' : '失败'}</span>
                <div class="recent-log-msg">${escapeHtml(log.message || '')}</div>
            </div>
        `).join('');
    }
}

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

// 配置相关
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

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastBody = document.getElementById('toastBody');
    toastBody.textContent = message;
    toast.className = 'toast';
    toast.classList.add(type === 'success' ? 'text-bg-success' : type === 'error' ? 'text-bg-danger' : 'text-bg-primary');
    new bootstrap.Toast(toast).show();
}
