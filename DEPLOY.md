# 微信记账小助手 - 阿里云部署指南

## 部署步骤

### 1. 上传代码到服务器

```bash
# 方式一：使用 scp
scp -r ./* root@YOUR_SERVER_IP:/opt/wechat-tracker/

# 方式二：使用 git
cd /opt
git clone YOUR_REPO_URL wechat-tracker
```

### 2. 配置微信测试号

编辑 `config.py`，填写您的微信测试号信息：
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

### 4. 配置防火墙

```bash
# 开放 5000 端口
sudo firewall-cmd --zone=public --add-port=5000/tcp --permanent
sudo firewall-cmd --reload

# 或者使用 iptables
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

### 5. 配置微信测试号后台

1. 访问 https://mp.weixin.qq.com/debug/cgi-bin/sandbox
2. 在"接口配置信息"填写：
   - URL: `http://YOUR_SERVER_IP:5000/wechat`
   - Token: 与 config.py 中相同

---

## 常用命令

| 操作 | 命令 |
|------|------|
| 查看服务状态 | `systemctl status wechat-tracker` |
| 重启服务 | `systemctl restart wechat-tracker` |
| 停止服务 | `systemctl stop wechat-tracker` |
| 查看日志 | `journalctl -u wechat-tracker -f` |

---

## 可选：使用 Nginx 反向代理

如果您希望使用 80 端口或 HTTPS：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /wechat {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
