"""
日期提醒系统配置文件
"""
import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config_data.json')


def load_wechat_webhook():
    """从文件加载 Webhook 配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data.get('wechat_webhook_url', '')
        except:
            pass
    return os.getenv('WECHAT_WEBHOOK_URL', '')


def save_wechat_webhook(url):
    """保存 Webhook 配置到文件"""
    data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
        except:
            pass
    data['wechat_webhook_url'] = url
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Config:
    # MySQL 数据库配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'date_reminder')
    MYSQL_CHARSET = os.getenv('MYSQL_CHARSET', 'utf8mb4')

    # SQLAlchemy 配置
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset={MYSQL_CHARSET}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 企业微信机器人 Webhook 地址（全局配置，优先从文件读取）
    WECHAT_WEBHOOK_URL = load_wechat_webhook()

    # 提醒时间（默认每小时检查一次）
    CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', 60))

    # 提前提醒天数选项
    REMINDER_DAYS_OPTIONS = [1, 3, 7, 15, 30]

    # 默认提醒时间段
    DEFAULT_REMINDER_TIMES = ['09:00', '14:00', '18:00']

    # 每页显示数量
    PAGE_SIZE = 20
