"""
日期提醒系统 - Flask 主应用
"""
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from config import Config
from models import db, Project, Reminder, ReminderLog
from scheduler import init_scheduler, shutdown_scheduler
import atexit

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()
    print("数据库表初始化完成")


# ==================== 页面路由 ====================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


# ==================== 项目 API ====================

@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.order_by(Project.sort_order).all()
    return jsonify({'code': 0, 'data': [p.to_dict() for p in projects]})


@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'code': 1, 'msg': '项目名称不能为空'})

    project = Project(
        name=data['name'],
        color=data.get('color', '#6366f1'),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(project)
    db.session.commit()
    return jsonify({'code': 0, 'msg': '创建成功', 'data': project.to_dict()})


@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    if data.get('name'):
        project.name = data['name']
    if 'color' in data:
        project.color = data['color']
    if 'sort_order' in data:
        project.sort_order = data['sort_order']
    db.session.commit()
    return jsonify({'code': 0, 'msg': '更新成功', 'data': project.to_dict()})


@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    # 将该项目下的提醒设为未分组
    Reminder.query.filter_by(project_id=project_id).update({Reminder.project_id: None})
    db.session.delete(project)
    db.session.commit()
    return jsonify({'code': 0, 'msg': '删除成功'})


# ==================== 提醒 API ====================

@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    keyword = request.args.get('keyword', '')
    project_id = request.args.get('project_id', '')

    query = Reminder.query

    if keyword:
        query = query.filter(
            db.or_(
                Reminder.title.contains(keyword),
                Reminder.note.contains(keyword)
            )
        )

    if project_id:
        query = query.filter(Reminder.project_id == project_id)

    pagination = query.order_by(Reminder.target_date.asc(), Reminder.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'code': 0,
        'data': {
            'list': [r.to_dict() for r in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })


@app.route('/api/reminders', methods=['POST'])
def create_reminder():
    data = request.get_json()

    if not data.get('title'):
        return jsonify({'code': 1, 'msg': '标题不能为空'})

    if not data.get('target_date'):
        return jsonify({'code': 1, 'msg': '目标日期不能为空'})

    try:
        target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'code': 1, 'msg': '日期格式错误'})

    reminder = Reminder(
        project_id=data.get('project_id'),
        title=data['title'],
        target_date=target_date,
        reminder_days=data.get('reminder_days', '1,3,7'),
        reminder_times=data.get('reminder_times', '09:00'),
        note=data.get('note', ''),
        mention_list=data.get('mention_list', ''),
        is_active=data.get('is_active', True)
    )

    db.session.add(reminder)
    db.session.commit()

    return jsonify({'code': 0, 'msg': '创建成功', 'data': reminder.to_dict()})


@app.route('/api/reminders/<int:reminder_id>', methods=['GET'])
def get_reminder(reminder_id):
    reminder = Reminder.query.get_or_404(reminder_id)
    return jsonify({'code': 0, 'data': reminder.to_dict()})


@app.route('/api/reminders/<int:reminder_id>', methods=['PUT'])
def update_reminder(reminder_id):
    reminder = Reminder.query.get_or_404(reminder_id)
    data = request.get_json()

    if data.get('title'):
        reminder.title = data['title']
    if data.get('project_id') is not None:
        reminder.project_id = data['project_id']
    if data.get('target_date'):
        try:
            reminder.target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'code': 1, 'msg': '日期格式错误'})
    if 'reminder_days' in data:
        reminder.reminder_days = data['reminder_days']
    if 'reminder_times' in data:
        reminder.reminder_times = data['reminder_times']
    if 'note' in data:
        reminder.note = data['note']
    if 'mention_list' in data:
        reminder.mention_list = data['mention_list']
    if 'is_active' in data:
        reminder.is_active = data['is_active']

    db.session.commit()
    return jsonify({'code': 0, 'msg': '更新成功', 'data': reminder.to_dict()})


@app.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    reminder = Reminder.query.get_or_404(reminder_id)
    ReminderLog.query.filter_by(reminder_id=reminder_id).delete()
    db.session.delete(reminder)
    db.session.commit()
    return jsonify({'code': 0, 'msg': '删除成功'})


# ==================== 日志 API ====================

@app.route('/api/reminders/<int:reminder_id>/logs', methods=['GET'])
def get_reminder_logs(reminder_id):
    logs = ReminderLog.query.filter_by(reminder_id=reminder_id).order_by(
        ReminderLog.send_date.desc(),
        ReminderLog.send_time.desc()
    ).limit(50).all()
    return jsonify({'code': 0, 'data': [log.to_dict() for log in logs]})


# ==================== 配置 API ====================

@app.route('/api/config', methods=['GET'])
def get_config():
    from config import Config
    return jsonify({'code': 0, 'data': {'wechat_webhook_url': Config.WECHAT_WEBHOOK_URL}})


@app.route('/api/config', methods=['POST'])
def update_config():
    from config import save_wechat_webhook, Config
    data = request.get_json()
    webhook_url = data.get('wechat_webhook_url', '')
    save_wechat_webhook(webhook_url)
    Config.WECHAT_WEBHOOK_URL = webhook_url
    return jsonify({'code': 0, 'msg': '配置保存成功'})


@app.route('/api/test-wechat', methods=['POST'])
def test_wechat():
    from wechat import send_text_message
    from config import Config
    result = send_text_message(
        Config.WECHAT_WEBHOOK_URL,
        "日期提醒系统测试消息\n这是一条测试消息，如果您收到此消息，说明配置正确！"
    )
    if result.get('errcode') == 0:
        return jsonify({'code': 0, 'msg': '测试消息发送成功'})
    else:
        return jsonify({'code': 1, 'msg': f"发送失败: {result.get('errmsg', '未知错误')}"})


# ==================== 统计/监控 API ====================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_reminders = Reminder.query.count()
    active_reminders = Reminder.query.filter_by(is_active=True).count()
    total_logs = ReminderLog.query.count()
    success_logs = ReminderLog.query.filter_by(status='success').count()

    return jsonify({
        'code': 0,
        'data': {
            'total_reminders': total_reminders,
            'active_reminders': active_reminders,
            'total_logs': total_logs,
            'success_logs': success_logs
        }
    })


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """获取监控面板数据"""
    from datetime import date, timedelta

    today = date.today()

    # 今日到期
    today_due = Reminder.query.filter(
        Reminder.target_date == today,
        Reminder.is_active == True
    ).count()

    # 本周到期
    week_end = today + timedelta(days=(6 - today.weekday()))
    week_due = Reminder.query.filter(
        Reminder.target_date >= today,
        Reminder.target_date <= week_end,
        Reminder.is_active == True
    ).count()

    # 本月到期
    month_end = today.replace(day=28) + timedelta(days=4)
    month_end = month_end.replace(day=1) - timedelta(days=1)
    month_due = Reminder.query.filter(
        Reminder.target_date >= today,
        Reminder.target_date <= month_end,
        Reminder.is_active == True
    ).count()

    # 已过期
    overdue = Reminder.query.filter(
        Reminder.target_date < today,
        Reminder.is_active == True
    ).count()

    # 项目统计
    projects = Project.query.all()
    project_stats = []
    for p in projects:
        count = Reminder.query.filter_by(project_id=p.id, is_active=True).count()
        project_stats.append({
            'id': p.id,
            'name': p.name,
            'color': p.color,
            'count': count
        })

    # 最近发送日志
    recent_logs = ReminderLog.query.order_by(
        ReminderLog.send_date.desc(),
        ReminderLog.send_time.desc()
    ).limit(20).all()

    # 即将到期的提醒（未来7天）
    upcoming = Reminder.query.filter(
        Reminder.target_date >= today,
        Reminder.target_date <= today + timedelta(days=7),
        Reminder.is_active == True
    ).order_by(Reminder.target_date.asc()).limit(10).all()

    return jsonify({
        'code': 0,
        'data': {
            'today_due': today_due,
            'week_due': week_due,
            'month_due': month_due,
            'overdue': overdue,
            'project_stats': project_stats,
            'recent_logs': [log.to_dict() for log in recent_logs],
            'upcoming': [r.to_dict() for r in upcoming]
        }
    })


@app.route('/api/reminders/<int:reminder_id>/send-now', methods=['POST'])
def send_reminder_now(reminder_id):
    """立即发送提醒（测试用）"""
    from wechat import send_reminder_notification
    from config import Config

    reminder = Reminder.query.get_or_404(reminder_id)

    if not Config.WECHAT_WEBHOOK_URL or 'YOUR_KEY' in Config.WECHAT_WEBHOOK_URL:
        return jsonify({'code': 1, 'msg': '请先配置企业微信 Webhook 地址'})

    result = send_reminder_notification(
        Config.WECHAT_WEBHOOK_URL,
        reminder,
        0,
        reminder.target_date
    )

    # 记录日志
    now = datetime.now()
    log = ReminderLog(
        reminder_id=reminder.id,
        send_date=now.date(),
        send_time=now.time(),
        status='success' if result.get('errcode') == 0 else 'failed',
        message=f'[手动发送] {reminder.title}',
        response=str(result)
    )
    db.session.add(log)
    db.session.commit()

    if result.get('errcode') == 0:
        return jsonify({'code': 0, 'msg': '发送成功'})
    else:
        return jsonify({'code': 1, 'msg': f"发送失败: {result.get('errmsg', '未知错误')}"})


# ==================== 启动和关闭 ====================

@atexit.register
def atexit_handler():
    shutdown_scheduler()


if __name__ == '__main__':
    init_scheduler(app)
    app.run(host='0.0.0.0', port=8000, debug=True)
