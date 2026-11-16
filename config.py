"""
日期提醒系统配置文件
"""
import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config_data.json')


def load_config():
    """从文件加载全局配置"""
    config = {
        'wechat_webhook_url': '',
        'feishu_webhook_url': ''
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                config.update(data)
        except:
            pass
    # 环境变量优先
    if os.getenv('WECHAT_WEBHOOK_URL'):
        config['wechat_webhook_url'] = os.getenv('WECHAT_WEBHOOK_URL')
    if os.getenv('FEISHU_WEBHOOK_URL'):
        config['feishu_webhook_url'] = os.getenv('FEISHU_WEBHOOK_URL')
    return config


def save_config(wechat_url, feishu_url):
    """保存全局配置到文件"""
    data = {
        'wechat_webhook_url': wechat_url,
        'feishu_webhook_url': feishu_url
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


_config = load_config()


class Config:
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'date_reminder')
    MYSQL_CHARSET = os.getenv('MYSQL_CHARSET', 'utf8mb4')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset={MYSQL_CHARSET}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WECHAT_WEBHOOK_URL = _config['wechat_webhook_url']
    FEISHU_WEBHOOK_URL = _config['feishu_webhook_url']

    CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', 60))
    REMINDER_DAYS_OPTIONS = [1, 3, 7, 15, 30]
    DEFAULT_REMINDER_TIMES = ['09:00', '14:00', '18:00']
    PAGE_SIZE = 20
