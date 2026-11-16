"""
企业微信 + 飞书 机器人通知模块
"""
import json
import requests
from datetime import datetime


# ============ 企业微信 ============

def send_wechat_message(webhook_url, content, mention_list=None):
    if not webhook_url:
        return {'errcode': -1, 'errmsg': 'Webhook 未配置'}

    headers = {'Content-Type': 'application/json'}
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content}
    }

    if mention_list:
        mentioned_list = []
        mentioned_mobile_list = []
        for person in mention_list:
            person = person.strip()
            if not person:
                continue
            if person.isdigit() and len(person) == 11:
                mentioned_mobile_list.append(person)
            else:
                mentioned_list.append(person)
        if mentioned_list or mentioned_mobile_list:
            payload["mentioned_list"] = mentioned_list
            payload["mentioned_mobile_list"] = mentioned_mobile_list

    try:
        resp = requests.post(webhook_url, headers=headers, data=json.dumps(payload), timeout=10)
        return resp.json()
    except Exception as e:
        return {'errcode': -1, 'errmsg': str(e)}


def send_wechat_text(webhook_url, content, mention_list=None):
    if not webhook_url:
        return {'errcode': -1, 'errmsg': 'Webhook 未配置'}

    headers = {'Content-Type': 'application/json'}
    payload = {
        "msgtype": "text",
        "text": {
            "content": content,
            "mentioned_list": mention_list or []
        }
    }

    try:
        resp = requests.post(webhook_url, headers=headers, data=json.dumps(payload), timeout=10)
        return resp.json()
    except Exception as e:
        return {'errcode': -1, 'errmsg': str(e)}


# ============ 飞书 ============

def send_feishu_message(webhook_url, content, mention_list=None):
    """飞书机器人发送富文本消息"""
    if not webhook_url:
        return {'code': -1, 'msg': 'Webhook 未配置'}

    headers = {'Content-Type': 'application/json'}

    # 飞书自定义机器人使用 interactive 消息类型
    elements = []

    # 解析 markdown 简单转换为飞书元素
    # 飞书支持 markdown 格式的 content
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "日期提醒"},
                "template": "blue"
            },
            "elements": [
                {"tag": "markdown", "content": content}
            ]
        }
    }

    if mention_list:
        at_list = []
        for person in mention_list:
            person = person.strip()
            if person:
                at_list.append({"tag": "at", "user_id": person})
        if at_list:
            payload["card"]["elements"].extend(at_list)

    try:
        resp = requests.post(webhook_url, headers=headers, data=json.dumps(payload), timeout=10)
        return resp.json()
    except Exception as e:
        return {'code': -1, 'msg': str(e)}


def send_feishu_text(webhook_url, content, mention_list=None):
    """飞书发送纯文本消息"""
    if not webhook_url:
        return {'code': -1, 'msg': 'Webhook 未配置'}

    headers = {'Content-Type': 'application/json'}
    payload = {
        "msg_type": "text",
        "content": {"text": content}
    }

    try:
        resp = requests.post(webhook_url, headers=headers, data=json.dumps(payload), timeout=10)
        return resp.json()
    except Exception as e:
        return {'code': -1, 'msg': str(e)}


# ============ 统一发送 ============

def get_countdown_emoji(days):
    if days <= 0:
        return '🔴'
    elif days <= 3:
        return '🟠'
    elif days <= 7:
        return '🟡'
    elif days <= 15:
        return '🔵'
    elif days <= 30:
        return '🟢'
    else:
        return '⚪'


def format_reminder_content(reminder, days_before, target_date):
    today = datetime.now().date()
    remaining_days = (target_date - today).days
    emoji = get_countdown_emoji(remaining_days)

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


def send_notification(webhook_url, channel, reminder, days_before, target_date):
    """
    统一发送通知

    Args:
        webhook_url: webhook 地址
        channel: wechat / feishu
        reminder: 提醒对象
        days_before: 提前天数
        target_date: 目标日期
    """
    content = format_reminder_content(reminder, days_before, target_date)

    mention_list = None
    if reminder.mention_list:
        mention_list = [m.strip() for m in reminder.mention_list.split(',') if m.strip()]

    if channel == 'feishu':
        result = send_feishu_message(webhook_url, content, mention_list)
        return result, 'feishu'
    else:
        result = send_wechat_message(webhook_url, content, mention_list)
        return result, 'wechat'
