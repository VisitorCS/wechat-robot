#!/bin/bash
# 微信记账小助手 - 阿里云部署脚本
# 使用方法: bash deploy.sh

set -e

echo "=========================================="
echo "微信记账小助手 - 阿里云部署"
echo "=========================================="

# 检查 Python 版本
echo "[1/6] 检查 Python 环境..."
python3 --version

# 安装系统依赖
echo "[2/6] 安装系统依赖..."
sudo yum install -y python3-devel gcc || sudo apt-get install -y python3-dev build-essential

# 创建虚拟环境
echo "[3/6] 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 安装 Python 依赖
echo "[4/6] 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 初始化数据库
echo "[5/6] 初始化数据库..."
python3 -c "from database import init_db; init_db()"

# 创建 systemd 服务
echo "[6/6] 配置 systemd 服务..."
sudo tee /etc/systemd/system/wechat-tracker.service > /dev/null << EOF
[Unit]
Description=WeChat Expense Tracker
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 重载并启动服务
sudo systemctl daemon-reload
sudo systemctl enable wechat-tracker
sudo systemctl restart wechat-tracker

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "服务状态:"
sudo systemctl status wechat-tracker --no-pager
echo ""
echo "常用命令:"
echo "  查看日志: sudo journalctl -u wechat-tracker -f"
echo "  重启服务: sudo systemctl restart wechat-tracker"
echo "  停止服务: sudo systemctl stop wechat-tracker"
echo ""
echo "微信接口地址: http://YOUR_SERVER_IP:5000/wechat"
echo ""
