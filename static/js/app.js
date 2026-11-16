let currentPage=1, searchKeyword='', currentProject='';
let scripts=[], documents=[];

document.addEventListener('DOMContentLoaded', () => {
    loadStats(); loadDashboard(); loadProjects(); loadReminders();
    document.getElementById('searchInput').addEventListener('input', debounce(function(){ searchKeyword=this.value.trim(); currentPage=1; loadReminders(); }, 300));
    document.getElementById('saveReminder').addEventListener('click', saveReminder);
});

function loadStats() {
    fetch('/api/stats').then(r=>r.json()).then(d=>{ if(d.code===0){ animateNumber('totalReminders',d.data.total_reminders); animateNumber('activeReminders',d.data.active_reminders); animateNumber('totalLogs',d.data.total_logs); animateNumber('successLogs',d.data.success_logs); } });
}
function animateNumber(id, target) {
    const el=document.getElementById(id); if(!el) return;
    const cur=parseInt(el.textContent)||0, diff=target-cur, steps=20; let step=0;
    const t=setInterval(()=>{ step++; if(step>=steps){el.textContent=target;clearInterval(t);} else{el.textContent=Math.round(cur+(diff/steps)*step);} },30);
}

function loadDashboard() {
    fetch('/api/dashboard').then(r=>r.json()).then(d=>{
        if(d.code===0){
            document.getElementById('todayDue').textContent=d.data.today_due;
            document.getElementById('weekDue').textContent=d.data.week_due;
            document.getElementById('monthDue').textContent=d.data.month_due;
            document.getElementById('overdue').textContent=d.data.overdue;
            const ps=document.getElementById('projectStats');
            if(d.data.project_stats.length===0){ ps.innerHTML='<p style="color:var(--text-secondary);text-align:center;padding:1rem;width:100%">暂无项目</p>'; }
            else { ps.innerHTML=d.data.project_stats.map(p=>`<div class="project-stat-card"><div class="project-stat-color" style="background:${p.color}"></div><div class="project-stat-info"><div class="project-stat-name">${esc(p.name)}</div><div class="project-stat-count">${p.count} <small style="font-size:0.8rem;color:var(--text-secondary)">个提醒</small></div></div></div>`).join(''); }
        }
    });
}

function loadProjects() {
    fetch('/api/projects').then(r=>r.json()).then(d=>{
        if(d.code===0){ renderProjectTabs(d.data); renderProjectSelect(d.data); }
    });
}
function renderProjectTabs(projects) {
    document.getElementById('projectTabs').innerHTML = `<button class="project-tab ${currentProject===''?'active':''}" onclick="filterByProject('')">全部</button>` + projects.map(p=>`<button class="project-tab ${currentProject==p.id?'active':''}" onclick="filterByProject(${p.id})" style="border-left:3px solid ${p.color}">${esc(p.name)}</button>`).join('');
}
function renderProjectSelect(projects) {
    document.getElementById('projectId').innerHTML = '<option value="">未分组</option>' + projects.map(p=>`<option value="${p.id}">${esc(p.name)}</option>`).join('');
}
function filterByProject(pid) { currentProject=pid; currentPage=1; loadProjects(); loadReminders(); }

function openProjectModal() { document.getElementById('projectName').value=''; document.querySelector('input[name="projectColor"][value="#6366f1"]').checked=true; new bootstrap.Modal(document.getElementById('projectModal')).show(); }
function saveProject() {
    const name=document.getElementById('projectName').value.trim(); if(!name) return showToast('请输入项目名称');
    const color=document.querySelector('input[name="projectColor"]:checked').value;
    fetch('/api/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,color})}).then(r=>r.json()).then(d=>{ if(d.code===0){ showToast('项目创建成功','success'); bootstrap.Modal.getInstance(document.getElementById('projectModal')).hide(); loadProjects(); loadDashboard(); } else showToast(d.msg); });
}

function loadReminders() {
    fetch(`/api/reminders?page=${currentPage}&per_page=100&keyword=${encodeURIComponent(searchKeyword)}&project_id=${currentProject}`).then(r=>r.json()).then(d=>{ if(d.code===0) renderCards(d.data.list); });
}
function renderCards(reminders) {
    const c=document.getElementById('reminderCards');
    if(reminders.length===0){ c.innerHTML='<div class="empty-state"><i class="bi bi-calendar-x"></i><p>暂无提醒</p></div>'; return; }
    c.innerHTML=reminders.map(r=>{
        const dl=getDaysLeft(r.target_date);
        const cc=dl<0?'countdown-overdue':dl===0?'countdown-today':dl<=3?'countdown-soon':'countdown-normal';
        const ct=dl<0?`已过期${Math.abs(dl)}天`:dl===0?'今天':dl===1?'明天':`还有${dl}天`;
        const wType=r.webhook_type||'wechat';
        const wLabel=r.webhook_url?(wType==='feishu'?'飞书':'企微')+'(单独)':'全局默认';
        const wClass=r.webhook_url?(wType==='feishu'?'feishu':'wechat'):'default';
        return `<div class="reminder-card" style="--card-color:${r.project_color}">
            <div class="card-header-row"><span class="card-project">${esc(r.project_name)}</span><span class="card-status ${r.is_active?'active':'inactive'}">${r.is_active?'启用':'停用'}</span></div>
            <div class="card-title">${esc(r.title)}</div>
            <div class="card-date"><i class="bi bi-calendar"></i><span>${r.target_date}</span><span class="countdown-badge ${cc}">${ct}</span></div>
            <div class="card-meta">
                <span class="card-meta-item"><i class="bi bi-clock"></i> 提前${r.reminder_days.split(',').join('/')}天</span>
                <span class="card-meta-item"><i class="bi bi-bell"></i> ${r.reminder_times}</span>
                ${r.mention_list?`<span class="card-meta-item"><i class="bi bi-person"></i> @${r.mention_list}</span>`:''}
            </div>
            <span class="card-webhook ${wClass}">${wLabel}</span>
            ${r.note?`<div class="card-note"><i class="bi bi-sticky"></i> ${esc(r.note.substring(0,40))}${r.note.length>40?'...':''}</div>`:''}
            ${r.scripts&&r.scripts.length?`<div style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:0.5rem"><i class="bi bi-code-slash"></i> ${r.scripts.length}个脚本</div>`:''}
            ${r.documents&&r.documents.length?`<div style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:0.5rem"><i class="bi bi-file-earmark-text"></i> ${r.documents.length}个文档</div>`:''}
            <div class="card-actions">
                <button class="action-btn" onclick="sendNow(${r.id})" title="立即发送"><i class="bi bi-send-fill"></i></button>
                <button class="action-btn" onclick="viewLogs(${r.id})" title="日志"><i class="bi bi-clock-history"></i></button>
                <button class="action-btn" onclick="editReminder(${r.id})" title="编辑"><i class="bi bi-pencil"></i></button>
                <button class="action-btn delete" onclick="deleteReminder(${r.id})" title="删除"><i class="bi bi-trash"></i></button>
            </div></div>`;
    }).join('');
}

function openReminderModal() { scripts=[]; documents=[]; resetForm(); new bootstrap.Modal(document.getElementById('reminderModal')).show(); }
function saveReminder() {
    const id=document.getElementById('reminderId').value, title=document.getElementById('title').value.trim(), targetDate=document.getElementById('targetDate').value;
    if(!title) return showToast('请输入标题'); if(!targetDate) return showToast('请选择目标日期');
    const days=Array.from(document.querySelectorAll('.reminder-day:checked')).map(e=>e.value).join(',');
    const times=Array.from(document.querySelectorAll('.reminder-time:checked')).map(e=>e.value).join(',');
    if(!days) return showToast('请选择提前天数'); if(!times) return showToast('请选择提醒时间');
    const data={ title, target_date:targetDate, project_id:document.getElementById('projectId').value||null, reminder_days:days, reminder_times:times, note:document.getElementById('note').value.trim(), mention_list:document.getElementById('mentionList').value.trim(), webhook_type:document.getElementById('webhookType').value, webhook_url:document.getElementById('webhookUrl').value.trim(), is_active:document.getElementById('isActive').checked };
    fetch(id?`/api/reminders/${id}`:'/api/reminders',{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).then(r=>r.json()).then(d=>{
        if(d.code===0){ showToast(id?'更新成功':'创建成功','success'); bootstrap.Modal.getInstance(document.getElementById('reminderModal')).hide(); loadReminders(); loadStats(); loadDashboard(); loadProjects(); } else showToast(d.msg);
    });
}
function editReminder(id) {
    fetch(`/api/reminders/${id}`).then(r=>r.json()).then(d=>{
        if(d.code===0){
            const r=d.data;
            document.getElementById('reminderId').value=r.id; document.getElementById('title').value=r.title; document.getElementById('targetDate').value=r.target_date;
            document.getElementById('note').value=r.note; document.getElementById('mentionList').value=r.mention_list; document.getElementById('isActive').checked=r.is_active;
            document.getElementById('projectId').value=r.project_id||''; document.getElementById('webhookType').value=r.webhook_type||''; document.getElementById('webhookUrl').value=r.webhook_url||'';
            document.querySelectorAll('.reminder-day').forEach(e=>{e.checked=r.reminder_days.split(',').includes(e.value);});
            document.querySelectorAll('.reminder-time').forEach(e=>{e.checked=r.reminder_times.split(',').includes(e.value);});
            scripts=r.scripts||[]; documents=r.documents||[];
            renderScripts(); renderDocuments();
            document.getElementById('reminderModalTitle').innerHTML='<i class="bi bi-pencil"></i> 编辑提醒';
            new bootstrap.Modal(document.getElementById('reminderModal')).show();
        }
    });
}
function deleteReminder(id) { if(!confirm('确定删除？')) return; fetch(`/api/reminders/${id}`,{method:'DELETE'}).then(r=>r.json()).then(d=>{ if(d.code===0){ showToast('删除成功','success'); loadReminders(); loadStats(); } }); }
function resetForm() { document.getElementById('reminderId').value=''; document.getElementById('title').value=''; document.getElementById('targetDate').value=''; document.getElementById('note').value=''; document.getElementById('mentionList').value=''; document.getElementById('isActive').checked=true; document.getElementById('projectId').value=''; document.getElementById('webhookType').value=''; document.getElementById('webhookUrl').value=''; document.querySelectorAll('.reminder-day,.reminder-time').forEach(e=>{e.checked=false;}); document.getElementById('reminderModalTitle').innerHTML='<i class="bi bi-plus-circle"></i> 新建提醒'; scripts=[]; documents=[]; renderScripts(); renderDocuments(); }

// Scripts
function renderScripts() { document.getElementById('scriptsList').innerHTML=scripts.map((s,i)=>`<div class="script-item"><div class="script-item-header"><input type="text" value="${esc(s.name)}" onchange="scripts[${i}].name=this.value" style="flex:1;margin-right:0.5rem"><select onchange="scripts[${i}].language=this.value"><option value="bash" ${s.language==='bash'?'selected':''}>Bash</option><option value="python" ${s.language==='python'?'selected':''}>Python</option><option value="shell" ${s.language==='shell'?'selected':''}>Shell</option></select><button class="action-btn delete" onclick="scripts.splice(${i},1);renderScripts()"><i class="bi bi-trash"></i></button></div><textarea onchange="scripts[${i}].content=this.value" placeholder="脚本内容...">${esc(s.content||'')}</textarea></div>`).join(''); }
function addScript() { scripts.push({name:'新脚本',language:'bash',content:''}); renderScripts(); }

// Documents
function renderDocuments() { document.getElementById('documentsList').innerHTML=documents.map((d,i)=>`<div class="doc-item"><div class="doc-item-header"><input type="text" value="${esc(d.title)}" onchange="documents[${i}].title=this.value" style="flex:1;margin-right:0.5rem"><button class="action-btn delete" onclick="documents.splice(${i},1);renderDocuments()"><i class="bi bi-trash"></i></button></div><textarea onchange="documents[${i}].content=this.value" placeholder="文档内容（支持Markdown）..." style="min-height:100px">${esc(d.content||'')}</textarea></div>`).join(''); }
function addDocument() { documents.push({title:'新文档',content:''}); renderDocuments(); }

// Config
function openConfigModal() { fetch('/api/config').then(r=>r.json()).then(d=>{ if(d.code===0){ document.getElementById('wechatWebhook').value=d.data.wechat_webhook_url||''; document.getElementById('feishuWebhook').value=d.data.feishu_webhook_url||''; new bootstrap.Modal(document.getElementById('configModal')).show(); } }); }
function saveConfig() { const w=document.getElementById('wechatWebhook').value.trim(), f=document.getElementById('feishuWebhook').value.trim(); fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({wechat_webhook_url:w,feishu_webhook_url:f})}).then(r=>r.json()).then(d=>{ if(d.code===0){ showToast('配置保存成功','success'); bootstrap.Modal.getInstance(document.getElementById('configModal')).hide(); } else showToast(d.msg); }); }
function testWechat() { fetch('/api/test-wechat',{method:'POST'}).then(r=>r.json()).then(d=>showToast(d.msg,d.code===0?'success':'error')).catch(()=>showToast('测试失败')); }
function testFeishu() { fetch('/api/test-feishu',{method:'POST'}).then(r=>r.json()).then(d=>showToast(d.msg,d.code===0?'success':'error')).catch(()=>showToast('测试失败')); }

// Logs
function viewLogs(id) { fetch(`/api/reminders/${id}/logs`).then(r=>r.json()).then(d=>{ if(d.code===0){ const c=document.getElementById('logsList'); if(d.data.length===0){ c.innerHTML='<div class="empty-state"><p>暂无记录</p></div>'; } else { c.innerHTML=d.data.map(l=>`<div class="log-item"><div class="log-time">${l.send_date} ${l.send_time}</div><span class="log-channel ${l.channel||'wechat'}">${l.channel==='feishu'?'飞书':'企微'}</span><span class="log-status ${l.status}">${l.status==='success'?'成功':'失败'}</span><div class="log-message">${esc(l.message||'')}</div></div>`).join(''); } new bootstrap.Modal(document.getElementById('logsModal')).show(); } }); }

function sendNow(id) { if(!confirm('确定立即发送？')) return; fetch(`/api/reminders/${id}/send-now`,{method:'POST'}).then(r=>r.json()).then(d=>showToast(d.msg,d.code===0?'success':'error')); }

function getDaysLeft(d) { const t=new Date(d),n=new Date(); n.setHours(0,0,0,0); t.setHours(0,0,0,0); return Math.ceil((t-n)/(1000*60*60*24)); }
function esc(s) { if(!s) return ''; const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }
function debounce(fn,w) { let t; return function(...a){ clearTimeout(t); t=setTimeout(()=>fn.apply(this,a),w); }; }
function showToast(msg,type='info') { const t=document.getElementById('toast'); document.getElementById('toastBody').textContent=msg; t.className='toast'; t.classList.add(type==='success'?'text-bg-success':type==='error'?'text-bg-danger':'text-bg-primary'); new bootstrap.Toast(t).show(); }
