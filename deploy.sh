#!/bin/bash
# 微信记账小助手 - 交互式部署脚本
# 使用方法: bash deploy.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[✓]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }

# 交互式确认
confirm() {
    read -p "$1 [y/N]: " response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

# 显示菜单
show_menu() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}    微信记账小助手 - 部署管理工具${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "请选择操作:"
    echo "  1) 全新部署 (首次安装)"
    echo "  2) 更新代码 (保留数据)"
    echo "  3) 数据库迁移 (修复表结构)"
    echo "  4) 仅重启服务"
    echo "  5) 查看服务状态"
    echo "  6) 查看日志"
    echo "  7) 备份数据库"
    echo "  8) 退出"
    echo ""
    read -p "请输入选项 [1-8]: " choice
}

# 检查 Python 环境
check_python() {
    print_info "检查 Python 环境..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python 版本: $PYTHON_VERSION"
    else
        print_error "Python3 未安装!"
        exit 1
    fi
}

# 安装系统依赖
install_deps() {
    print_info "安装系统依赖..."
    if command -v yum &> /dev/null; then
        sudo yum install -y python3-devel gcc
    elif command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3-dev build-essential
    fi
    print_success "系统依赖安装完成"
}

# 创建/更新虚拟环境
setup_venv() {
    print_info "配置虚拟环境..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "虚拟环境创建完成"
    else
        print_info "虚拟环境已存在"
    fi
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    print_success "Python 依赖安装完成"
}

# 初始化数据库
init_database() {
    print_info "初始化数据库..."
    python3 -c "from database import init_db; init_db()"
    print_success "数据库初始化完成"
}

# 数据库迁移（创建新表）
migrate_database() {
    print_info "执行数据库迁移..."
    source venv/bin/activate 2>/dev/null || true
    # init_db 使用 CREATE TABLE IF NOT EXISTS，会创建新表但不影响已有数据
    python3 -c "from database import init_db; init_db()"
    print_success "数据库迁移完成"
}

# 配置 systemd 服务
setup_service() {
    print_info "配置 systemd 服务..."
    sudo tee /etc/systemd/system/wechat-tracker.service > /dev/null <<EOF
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
    sudo systemctl daemon-reload
    sudo systemctl enable wechat-tracker
    print_success "systemd 服务配置完成"
}

# 重启服务
restart_service() {
    print_info "重启服务..."
    sudo systemctl restart wechat-tracker
    sleep 2
    if systemctl is-active --quiet wechat-tracker; then
        print_success "服务启动成功"
    else
        print_error "服务启动失败!"
        sudo journalctl -u wechat-tracker -n 20 --no-pager
    fi
}

# 查看服务状态
show_status() {
    echo ""
    sudo systemctl status wechat-tracker --no-pager
    echo ""
}

# 查看日志
show_logs() {
    echo ""
    print_info "按 Ctrl+C 退出日志查看"
    sudo journalctl -u wechat-tracker -f
}

# 备份数据库
backup_database() {
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    DB_FILE="$SCRIPT_DIR/data/tracker.db"
    BACKUP_DIR="$SCRIPT_DIR/backups"
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/tracker_$(date +%Y%m%d_%H%M%S).db"
    
    if [ -f "$DB_FILE" ]; then
        cp "$DB_FILE" "$BACKUP_FILE"
        print_success "数据库已备份到: $BACKUP_FILE"
    else
        print_warning "数据库文件不存在: $DB_FILE"
    fi
}

# 全新部署
full_deploy() {
    echo ""
    print_info "开始全新部署..."
    echo ""
    
    check_python
    install_deps
    setup_venv
    init_database
    setup_service
    restart_service
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ 部署完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "微信接口地址: http://YOUR_SERVER_IP:5000/wechat"
    echo ""
    echo "常用命令:"
    echo "  查看日志: sudo journalctl -u wechat-tracker -f"
    echo "  重启服务: sudo systemctl restart wechat-tracker"
    echo ""
}

# 更新部署
update_deploy() {
    echo ""
    print_info "开始更新部署..."
    echo ""
    
    if confirm "是否先备份数据库?"; then
        backup_database
    fi
    
    setup_venv
    migrate_database
    restart_service
    
    print_success "更新完成！"
}

# 主程序
main() {
    # 如果有参数，直接执行对应操作
    case "${1:-}" in
        --full) full_deploy; exit 0 ;;
        --update) update_deploy; exit 0 ;;
        --migrate) migrate_database; exit 0 ;;
        --restart) restart_service; exit 0 ;;
    esac
    
    # 交互式菜单
    while true; do
        show_menu
        case $choice in
            1) full_deploy ;;
            2) update_deploy ;;
            3) migrate_database ;;
            4) restart_service ;;
            5) show_status ;;
            6) show_logs ;;
            7) backup_database ;;
            8) echo "再见!"; exit 0 ;;
            *) print_warning "无效选项，请重新选择" ;;
        esac
        
        echo ""
        read -p "按回车键继续..."
    done
}

main "$@"
