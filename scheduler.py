"""
定时任务调度器
"""
from datetime import datetime, date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from wechat import send_reminder_notification
from config import Config
from models import db, Reminder, ReminderLog

scheduler = BackgroundScheduler()


def check_and_send_reminders(app):
    """
    检查并发送提醒
    每分钟执行一次，检查当前时间是否匹配提醒时间
    """
    with app.app_context():
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_date = now.date()

        webhook_url = Config.WECHAT_WEBHOOK_URL

        if not webhook_url or 'YOUR_KEY' in webhook_url:
            print(f"[{now}] 企业微信 Webhook 未配置")
            return

        # 查询所有启用的提醒
        reminders = Reminder.query.filter_by(is_active=True).all()

        for reminder in reminders:
            # 解析提醒天数
            reminder_days = [int(d.strip()) for d in reminder.reminder_days.split(',') if d.strip().isdigit()]

            # 解析提醒时间
            reminder_times = [t.strip() for t in reminder.reminder_times.split(',') if t.strip()]

            # 检查当前时间是否在提醒时间列表中
            if current_time not in reminder_times:
                continue

            target_date = reminder.target_date

            # 检查每个提前天数是否匹配
            for days in reminder_days:
                # 计算应该发送提醒的日期
                reminder_date = target_date - timedelta(days=days)

                # 如果今天是需要发送提醒的日期
                if current_date == reminder_date:
                    # 检查是否已经发送过
                    existing_log = ReminderLog.query.filter_by(
                        reminder_id=reminder.id,
                        send_date=current_date,
                        send_time=datetime.strptime(current_time, '%H:%M').time()
                    ).first()

                    if existing_log:
                        continue

                    # 发送提醒
                    result = send_reminder_notification(webhook_url, reminder, days, target_date)

                    # 记录日志
                    log = ReminderLog(
                        reminder_id=reminder.id,
                        send_date=current_date,
                        send_time=datetime.strptime(current_time, '%H:%M').time(),
                        status='success' if result.get('errcode') == 0 else 'failed',
                        message=reminder.title,
                        response=str(result)
                    )
                    db.session.add(log)
                    db.session.commit()

                    print(f"[{now}] 发送提醒: {reminder.title}, 提前{days}天, 状态: {log.status}")


def init_scheduler(app):
    """
    初始化调度器
    """
    # 每分钟的第0秒执行检查
    scheduler.add_job(
        func=check_and_send_reminders,
        trigger=CronTrigger(minute='*'),
        args=[app],
        id='check_reminders',
        replace_existing=True
    )
    scheduler.start()
    print("定时任务调度器已启动")


def shutdown_scheduler():
    """
    关闭调度器
    """
    if scheduler.running:
        scheduler.shutdown()
        print("定时任务调度器已关闭")
