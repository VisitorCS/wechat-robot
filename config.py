"""
微信公众号记账应用配置文件

请在部署前填写您的微信测试号信息：
- 微信测试号申请地址：https://mp.weixin.qq.com/debug/cgi-bin/sandbox
"""

import os

# =============================================
# 微信公众平台配置 - 请填写您的信息
# =============================================
WECHAT_APP_ID = os.environ.get('WECHAT_APP_ID', 'your_app_id_here')
WECHAT_APP_SECRET = os.environ.get('WECHAT_APP_SECRET', 'your_app_secret_here')
WECHAT_TOKEN = os.environ.get('WECHAT_TOKEN', 'your_token_here')

# =============================================
# 数据库配置
# =============================================
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'expense.db')

# =============================================
# 定时推送配置（每日推送时间）
# =============================================
DAILY_PUSH_HOUR = 8   # 早上 8:00 推送
DAILY_PUSH_MINUTE = 0

# =============================================
# Flask 配置
# =============================================
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = False  # 生产环境关闭 Debug
