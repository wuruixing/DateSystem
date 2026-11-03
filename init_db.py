"""
数据库初始化脚本
"""
from app import app, db


def init_database():
    with app.app_context():
        db.create_all()
        print("数据库表创建成功！")
        print("\n提示：请在系统中配置企业微信 Webhook 地址")


if __name__ == '__main__':
    init_database()
