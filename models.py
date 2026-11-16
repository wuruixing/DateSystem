"""
数据库模型
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20), default='#6366f1')
    sort_order = db.Column(db.Integer, default=0)
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
    __tablename__ = 'reminders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    reminder_days = db.Column(db.String(50), default='1,3,7')
    reminder_times = db.Column(db.String(100), default='09:00')
    note = db.Column(db.Text)
    note_format = db.Column(db.String(10), default='markdown')
    mention_list = db.Column(db.Text)
    # webhook 单独配置
    webhook_type = db.Column(db.String(20))  # wechat / feishu / ''
    webhook_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    project = db.relationship('Project', backref=db.backref('reminders', lazy='dynamic'))
    scripts = db.relationship('ReminderScript', backref='reminder', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('ReminderDocument', backref='reminder', lazy='dynamic', cascade='all, delete-orphan')

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
            'note_format': self.note_format,
            'mention_list': self.mention_list or '',
            'webhook_type': self.webhook_type or '',
            'webhook_url': self.webhook_url or '',
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'scripts': [s.to_dict() for s in self.scripts.all()],
            'documents': [d.to_dict() for d in self.documents.all()]
        }


class ReminderScript(db.Model):
    """提醒关联的脚本"""
    __tablename__ = 'reminder_scripts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminders.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(20), default='bash')
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'language': self.language,
            'content': self.content or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class ReminderDocument(db.Model):
    """提醒关联的文档"""
    __tablename__ = 'reminder_documents'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminders.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class ReminderLog(db.Model):
    __tablename__ = 'reminder_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminders.id'), nullable=False)
    send_date = db.Column(db.Date, nullable=False)
    send_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='success')
    message = db.Column(db.Text)
    response = db.Column(db.Text)
    channel = db.Column(db.String(20), default='wechat')
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
            'channel': self.channel,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
