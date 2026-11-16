# 日期提醒系统

简洁美观的日期提醒系统，支持企业微信/飞书双渠道通知。

## 功能

- 自定义提醒日期，提前 1/3/7/15/30 天提醒
- 每天可配置多个提醒时间段
- 企业微信 + 飞书双渠道通知
- 每个提醒可单独配置 webhook，也可使用全局配置
- 支持 @指定人员
- Markdown 备注 + 脚本/文档管理
- 项目分组管理

## 快速开始

### Docker 部署

```bash
# 配置环境变量
cp .env.example .env
vim .env  # 填入企业微信/飞书 Webhook

# 启动
docker-compose up -d --build

# 访问
http://127.0.0.1:8000
```

### 本地运行

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

mysql -u root -p -e "CREATE DATABASE date_reminder CHARACTER SET utf8mb4;"
python init_db.py
python app.py
```

## 配置

编辑 `.env` 文件：

```bash
MYSQL_ROOT_PASSWORD=你的密码
WECHAT_WEBHOOK_URL=企业微信webhook地址
FEISHU_WEBHOOK_URL=飞书webhook地址
```

或在系统界面点击右上角「配置」按钮设置。

## 目录结构

```
├── app.py          # 主应用
├── config.py       # 配置
├── models.py       # 数据模型
├── wechat.py       # 企业微信+飞书通知
├── scheduler.py    # 定时任务
├── templates/      # 前端页面
└── static/         # 静态资源
```

## License

MIT
