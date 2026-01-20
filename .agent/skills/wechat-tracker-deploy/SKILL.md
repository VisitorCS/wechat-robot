---
name: WeChat Tracker Deployment
description: 部署微信记账小助手到阿里云服务器的完整指南
---

# 🚀 微信记账小助手 - 部署指南

## 部署概述

本应用部署到阿里云 Linux 服务器，使用 systemd 管理服务，通过微信公众号测试接口接收消息。

## 前置条件

- 阿里云 ECS 服务器 (CentOS/Ubuntu)
- Python 3.8+
- 微信公众号测试账号

## 快速部署

### 1. 上传代码

```bash
# 方式一：scp
scp -r ./* root@YOUR_SERVER_IP:/opt/wechat-tracker/

# 方式二：git clone
cd /opt
git clone YOUR_REPO_URL wechat-tracker
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
cd /opt/wechat-tracker
chmod +x deploy.sh
bash deploy.sh
```

### 4. 开放防火墙端口

```bash
# firewalld
sudo firewall-cmd --zone=public --add-port=5000/tcp --permanent
sudo firewall-cmd --reload

# 或 iptables
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

### 5. 配置微信测试号

1. 访问 https://mp.weixin.qq.com/debug/cgi-bin/sandbox
2. 填写接口配置：
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
| 开机自启 | `systemctl enable wechat-tracker` |

## Nginx 反向代理（可选）

如需使用 80 端口或 HTTPS：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /wechat {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 故障排查

### 服务无法启动

```bash
# 检查 Python 环境
which python3
python3 --version

# 检查依赖
pip3 install -r requirements.txt

# 手动测试启动
cd /opt/wechat-tracker
python3 app.py
```

### 微信消息无响应

1. 检查服务是否运行：`systemctl status wechat-tracker`
2. 检查端口是否开放：`curl http://localhost:5000/wechat`
3. 检查微信 Token 是否匹配
4. 查看错误日志：`journalctl -u wechat-tracker -n 50`

### 推送消息失败

1. 检查 APP_ID 和 APP_SECRET 是否正确
2. 确认用户已关注公众号
3. 检查 access_token 是否过期

## 数据备份

```bash
# 备份数据库
cp /opt/wechat-tracker/data/tracker.db /backup/tracker_$(date +%Y%m%d).db

# 定时备份 (crontab)
0 2 * * * cp /opt/wechat-tracker/data/tracker.db /backup/tracker_$(date +\%Y\%m\%d).db
```
