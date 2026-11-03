"""
数据库模型
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Project(db.Model):
    """项目分组表"""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='项目名称')
    color = db.Column(db.String(20), default='#6366f1', comment='项目颜色')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'sort_order': self.sort_order,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Reminder(db.Model):
    """提醒主表"""
    __tablename__ = 'reminders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True, comment='所属项目')
    title = db.Column(db.String(200), nullable=False, comment='提醒标题')
    target_date = db.Column(db.Date, nullable=False, comment='目标日期')
    reminder_days = db.Column(db.String(50), default='1,3,7', comment='提前提醒天数，逗号分隔')
    reminder_times = db.Column(db.String(100), default='09:00', comment='提醒时间，逗号分隔')
    note = db.Column(db.Text, comment='备注')
    mention_list = db.Column(db.Text, comment='需要@的人员列表')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    project = db.relationship('Project', backref=db.backref('reminders', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else '未分组',
            'project_color': self.project.color if self.project else '#6366f1',
            'title': self.title,
            'target_date': self.target_date.strftime('%Y-%m-%d'),
            'reminder_days': self.reminder_days,
            'reminder_times': self.reminder_times,
            'note': self.note or '',
            'mention_list': self.mention_list or '',
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class ReminderLog(db.Model):
    """提醒发送日志"""
    __tablename__ = 'reminder_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminders.id'), nullable=False, comment='提醒ID')
    send_date = db.Column(db.Date, nullable=False, comment='发送日期')
    send_time = db.Column(db.Time, nullable=False, comment='发送时间')
    status = db.Column(db.String(20), default='success', comment='发送状态: success/failed')
    message = db.Column(db.Text, comment='发送的消息内容')
    response = db.Column(db.Text, comment='企业微信响应')
    created_at = db.Column(db.DateTime, default=datetime.now)

    reminder = db.relationship('Reminder', backref=db.backref('logs', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'reminder_id': self.reminder_id,
            'send_date': self.send_date.strftime('%Y-%m-%d'),
            'send_time': self.send_time.strftime('%H:%M'),
            'status': self.status,
            'message': self.message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
