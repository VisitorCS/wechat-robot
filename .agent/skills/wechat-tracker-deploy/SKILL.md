---
name: WeChat Tracker Deployment
description: 部署微信记账小助手到服务器的完整指南
---

# 🚀 微信记账小助手 - 部署指南

## 部署概述

本应用部署到 Linux 服务器，使用 systemd 管理服务，通过微信公众号接口接收消息。

## 前置条件

- Linux 服务器 (CentOS/Ubuntu)
- Python 3.6+
- 微信公众号测试账号

## 快速部署

### 1. 上传代码

```bash
scp -r ./* root@YOUR_SERVER_IP:/usr/local/wechat-tracker/
```

### 2. 配置微信凭证

编辑 `config.py`：
```python
WECHAT_APP_ID = 'wxxxxxxxxxxx'
WECHAT_APP_SECRET = 'xxxxxxxxxxxxxxxxx'
WECHAT_TOKEN = 'your_custom_token'
```

### 3. 运行部署脚本

```bash
cd /usr/local/wechat-tracker
bash deploy.sh
```

交互式菜单选项：
- `1` 全新部署（首次安装）
- `2` 更新代码（保留数据）
- `3` 数据库迁移
- `4` 重启服务
- `5` 查看状态
- `6` 查看日志
- `7` 备份数据库

### 4. 配置微信测试号

访问 https://mp.weixin.qq.com/debug/cgi-bin/sandbox

填写接口配置：
- **URL**: `http://YOUR_SERVER_IP:5000/wechat`
- **Token**: 与 config.py 中相同

## 服务管理

| 操作 | 命令 |
|------|------|
| 查看状态 | `systemctl status wechat-tracker` |
| 启动服务 | `systemctl start wechat-tracker` |
| 停止服务 | `systemctl stop wechat-tracker` |
| 重启服务 | `systemctl restart wechat-tracker` |
| 查看日志 | `journalctl -u wechat-tracker -f` |

## 数据库迁移

部署脚本会自动调用 `init_db()`：
- 使用 `CREATE TABLE IF NOT EXISTS` 创建新表
- 不影响已有数据
- 新增表会自动创建

## 故障排查

### 服务无法启动

```bash
# 手动测试
cd /usr/local/wechat-tracker
source venv/bin/activate
python3 app.py
```

### 微信消息无响应

1. 检查服务状态：`systemctl status wechat-tracker`
2. 检查端口：`curl http://localhost:5000/wechat`
3. 检查日志：`journalctl -u wechat-tracker -n 50`

### 数据库错误

如果出现表结构问题：
```bash
bash deploy.sh
# 选择选项 3（数据库迁移）
```

## 数据备份

```bash
# 手动备份
cp /usr/local/wechat-tracker/data/tracker.db /backup/

# 使用部署脚本
bash deploy.sh
# 选择选项 7（备份数据库）
```
