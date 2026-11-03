# 日期提醒系统

简洁美观的日期提醒系统，支持自定义提醒日期、提前提醒天数，并统一配置企业微信机器人发送通知。

## 功能特点

- 🎯 **自定义日期** - 设置任意目标日期
- ⏰ **灵活提前提醒** - 支持提前 1/3/7/15/30 天（可多选）
- 🕐 **时间段配置** - 可配置每天的提醒时间（09:00/12:00/14:00/18:00/21:00）
- 💬 **统一企业微信通知** - 全局配置 Webhook，自动发送 Markdown 格式消息
- @ **@提醒功能** - 支持在群里@指定人员（手机号或userid）
- 📝 **备注功能** - 每条提醒可添加备注说明
- 📊 **发送日志** - 记录所有发送历史
- 🎨 **现代 UI** - 简洁大气的现代化界面设计

## 技术栈

- **后端**: Python Flask
- **前端**: HTML5 + Bootstrap 5 + JavaScript
- **数据库**: MySQL
- **定时任务**: APScheduler
- **通知**: 企业微信机器人 Webhook

## 快速开始

### 1. 安装依赖

```bash
cd date-reminder-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置企业微信 Webhook

编辑 `config.py` 文件，修改 Webhook 地址：

```python
# 企业微信机器人 Webhook 地址（全局配置）
WECHAT_WEBHOOK_URL = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY'
```

### 3. 配置数据库

确保 MySQL 已启动，创建数据库：

```sql
CREATE DATABASE IF NOT EXISTS date_reminder CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

如需修改数据库密码，编辑 `config.py`：

```python
MYSQL_PASSWORD = 'your_password'  # 默认空密码
```

### 4. 初始化数据库

```bash
python init_db.py
```

### 5. 启动应用

```bash
python app.py
```

访问 **http://127.0.0.1:8000**

## 使用说明

### 创建提醒

1. 点击 **「新建提醒」** 按钮
2. 填写提醒信息：
   - **标题**: 提醒名称（必填）
   - **目标日期**: 选择日期（必填）
   - **提前提醒天数**: 勾选需要提前提醒的天数
   - **每天提醒时间**: 勾选每天发送提醒的时间
   - **备注**: 可选，添加备注说明
   - **@提醒人员**: 可选，输入手机号或企业微信userid
3. 点击 **「保存」**

### 测试通知

点击页面右上角的 **「测试通知」** 按钮，验证企业微信配置是否正确。

### 查看日志

点击提醒项的 **日志图标**，查看该提醒的所有发送记录。

## 项目结构

```
date-reminder-system/
├── app.py              # Flask 主应用
├── config.py           # 配置文件（数据库、Webhook）
├── models.py           # 数据库模型
├── scheduler.py        # 定时任务调度器
├── wechat.py           # 企业微信通知模块
├── init_db.py          # 数据库初始化
├── requirements.txt    # Python 依赖
├── templates/
│   └── index.html      # 前端页面
└── static/
    ├── css/style.css   # 样式文件
    └── js/app.js       # 前端脚本
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/reminders | 获取提醒列表 |
| POST | /api/reminders | 创建提醒 |
| PUT | /api/reminders/:id | 更新提醒 |
| DELETE | /api/reminders/:id | 删除提醒 |
| GET | /api/reminders/:id/logs | 获取提醒日志 |
| POST | /api/test-wechat | 测试企业微信配置 |
| GET | /api/stats | 获取统计信息 |

## 生产部署

### 方式一：Docker 部署（推荐）

**1. 安装 Docker 和 Docker Compose**

确保已安装 Docker 和 Docker Compose。

**2. 配置环境变量**

编辑 `.env` 文件：

```bash
# MySQL 根密码
MYSQL_ROOT_PASSWORD=root123

# 企业微信 Webhook 地址
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
```

**3. 启动服务**

```bash
docker-compose up -d
```

**4. 访问应用**

打开 http://127.0.0.1:8000

**5. 查看日志**

```bash
docker-compose logs -f web    # 查看应用日志
docker-compose logs -f db     # 查看数据库日志
```

**6. 停止服务**

```bash
docker-compose down           # 停止服务（保留数据）
docker-compose down -v        # 停止服务并删除数据
```

### 方式二：Gunicorn 部署

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 注意事项

1. 企业微信 Webhook 在 `config.py` 中全局配置
2. 定时任务每分钟执行一次，检查需要发送的提醒
3. @人员功能支持手机号（11位）或企业微信userid
4. 每条提醒的日志最多保留 50 条

## License

MIT
