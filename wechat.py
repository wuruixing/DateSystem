"""
企业微信机器人通知模块
"""
import json
import requests
from datetime import datetime


# 倒计时颜色映射 - 使用企业微信支持的明亮颜色
COUNTDOWN_COLORS = {
    0: '#ff0000',    # 今天 - 红色
    1: '#ff6600',    # 明天 - 橙红
    2: '#ff6600',    # 2天 - 橙红
    3: '#ff6600',    # 3天 - 橙红
    7: '#0066ff',    # 7天 - 蓝色
    15: '#9900cc',   # 15天 - 紫色
    30: '#666666',   # 30天 - 灰色
}


def get_countdown_emoji(days):
    """根据天数获取 emoji 和颜色"""
    if days <= 0:
        return '🔴', 'warning'
    elif days <= 3:
        return '🟠', 'warning'
    elif days <= 7:
        return '🟡', 'warning'
    elif days <= 15:
        return '🔵', 'info'
    elif days <= 30:
        return '🟢', 'comment'
    else:
        return '⚪', 'comment'


def send_wechat_message(webhook_url, title, content, mention_list=None):
    """
    发送企业微信机器人消息

    Args:
        webhook_url: 企业微信机器人 Webhook 地址
        title: 消息标题
        content: 消息内容 (Markdown 格式)
        mention_list: 需要@的人员列表 (手机号或userid)
    """
    if not webhook_url:
        return {'errcode': -1, 'errmsg': 'Webhook URL is not configured'}

    headers = {'Content-Type': 'application/json'}

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }

    # 添加@人功能
    if mention_list:
        mentioned_list = []
        mentioned_mobile_list = []
        for person in mention_list:
            person = person.strip()
            if not person:
                continue
            # 如果是手机号（11位数字）
            if person.isdigit() and len(person) == 11:
                mentioned_mobile_list.append(person)
            else:
                mentioned_list.append(person)

        if mentioned_list or mentioned_mobile_list:
            payload["mentioned_list"] = mentioned_list
            payload["mentioned_mobile_list"] = mentioned_mobile_list

    try:
        response = requests.post(
            webhook_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )
        result = response.json()
        return result
    except Exception as e:
        return {'errcode': -1, 'errmsg': str(e)}


def send_text_message(webhook_url, content, mention_list=None):
    """
    发送文本消息

    Args:
        webhook_url: 企业微信机器人 Webhook 地址
        content: 消息内容
        mention_list: 需要@的人员列表
    """
    if not webhook_url:
        return {'errcode': -1, 'errmsg': 'Webhook URL is not configured'}

    headers = {'Content-Type': 'application/json'}

    payload = {
        "msgtype": "text",
        "text": {
            "content": content,
            "mentioned_list": mention_list or []
        }
    }

    try:
        response = requests.post(
            webhook_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )
        result = response.json()
        return result
    except Exception as e:
        return {'errcode': -1, 'errmsg': str(e)}


def format_reminder_message(reminder, days_before, target_date):
    """
    格式化提醒消息 - 简洁样式

    Args:
        reminder: 提醒对象
        days_before: 提前天数
        target_date: 目标日期
    """
    today = datetime.now().date()
    remaining_days = (target_date - today).days
    emoji, _ = get_countdown_emoji(remaining_days)

    if remaining_days < 0:
        time_desc = f'已过期{abs(remaining_days)}天'
    elif remaining_days == 0:
        time_desc = '今天'
    elif remaining_days == 1:
        time_desc = '明天'
    else:
        time_desc = f'{remaining_days}天后'

    title_line = f"{emoji} **{time_desc}** · {reminder.title}"

    if reminder.note:
        content = f"""{title_line}

📅 到期：{target_date.strftime('%Y-%m-%d')}
📝 备注：{reminder.note}"""
    else:
        content = f"""{title_line}

📅 到期：{target_date.strftime('%Y-%m-%d')}"""

    return content


def send_reminder_notification(webhook_url, reminder, days_before, target_date):
    """
    发送提醒通知

    Args:
        webhook_url: 企业微信 Webhook 地址
        reminder: 提醒对象
        days_before: 提前天数
        target_date: 目标日期

    Returns:
        dict: 发送结果
    """
    content = format_reminder_message(reminder, days_before, target_date)

    # 解析@人员列表
    mention_list = None
    if reminder.mention_list:
        mention_list = [m.strip() for m in reminder.mention_list.split(',') if m.strip()]

    return send_wechat_message(webhook_url, reminder.title, content, mention_list)
