"""
定时任务调度器
"""
from datetime import datetime, date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from wechat import send_notification
from config import Config
from models import db, Reminder, ReminderLog

scheduler = BackgroundScheduler()


def check_and_send_reminders(app):
    with app.app_context():
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        current_date = now.date()

        reminders = Reminder.query.filter_by(is_active=True).all()

        for reminder in reminders:
            reminder_days = [int(d.strip()) for d in reminder.reminder_days.split(',') if d.strip().isdigit()]
            reminder_times = [t.strip() for t in reminder.reminder_times.split(',') if t.strip()]

            if current_time not in reminder_times:
                continue

            target_date = reminder.target_date

            for days in reminder_days:
                reminder_date = target_date - timedelta(days=days)

                if current_date != reminder_date:
                    continue

                existing_log = ReminderLog.query.filter_by(
                    reminder_id=reminder.id,
                    send_date=current_date,
                    send_time=datetime.strptime(current_time, '%H:%M').time()
                ).first()

                if existing_log:
                    continue

                # 确定使用哪个 webhook
                channel = reminder.webhook_type or 'wechat'
                webhook_url = reminder.webhook_url

                # 如果没单独配置，用全局配置
                if not webhook_url:
                    if channel == 'feishu':
                        webhook_url = Config.FEISHU_WEBHOOK_URL
                    else:
                        webhook_url = Config.WECHAT_WEBHOOK_URL

                if not webhook_url:
                    print(f"[{now}] 跳过 {reminder.title}: 未配置 webhook")
                    continue

                result, used_channel = send_notification(webhook_url, channel, reminder, days, target_date)

                errcode = result.get('errcode') if used_channel == 'wechat' else result.get('code')
                status = 'success' if (used_channel == 'wechat' and errcode == 0) or (used_channel == 'feishu' and result.get('StatusCode') == 0) else 'failed'

                log = ReminderLog(
                    reminder_id=reminder.id,
                    send_date=current_date,
                    send_time=datetime.strptime(current_time, '%H:%M').time(),
                    status=status,
                    message=reminder.title,
                    response=str(result),
                    channel=used_channel
                )
                db.session.add(log)
                db.session.commit()

                print(f"[{now}] 发送: {reminder.title}, 提前{days}天, 渠道:{used_channel}, 状态:{status}")


def init_scheduler(app):
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
    if scheduler.running:
        scheduler.shutdown()
        print("定时任务调度器已关闭")
