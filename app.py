"""
微信公众号记账应用 - Flask 主应用

功能：
- 接收微信服务器验证请求
- 处理用户消息
- 启动定时推送任务
"""

import hashlib
from flask import Flask, request, abort
from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException

from config import WECHAT_TOKEN, FLASK_HOST, FLASK_PORT, FLASK_DEBUG
from database import init_db
from wechat_handler import parse_message as handle_message
from scheduler import init_scheduler, shutdown_scheduler


app = Flask(__name__)


@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    """微信接口入口"""
    
    # 获取请求参数
    signature = request.args.get('signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    
    # GET 请求：服务器验证
    if request.method == 'GET':
        echostr = request.args.get('echostr', '')
        try:
            check_signature(WECHAT_TOKEN, signature, timestamp, nonce)
            print(f"[微信] 服务器验证成功")
            return echostr
        except InvalidSignatureException:
            print(f"[微信] 服务器验证失败")
            abort(403)
    
    # POST 请求：处理用户消息
    try:
        check_signature(WECHAT_TOKEN, signature, timestamp, nonce)
    except InvalidSignatureException:
        print(f"[微信] 消息签名验证失败")
        abort(403)
    
    # 解析消息
    msg = parse_message(request.data)
    print(f"[微信] 收到消息: {msg.type} from {msg.source[:8]}...")
    
    # 处理文本消息
    if msg.type == 'text':
        response_text = handle_message(msg.source, msg.content)
        reply = create_reply(response_text, msg)
        return reply.render()
    
    # 处理关注事件
    elif msg.type == 'event' and msg.event == 'subscribe':
        welcome = '''👋 欢迎使用记账小助手！

发送"帮助"查看使用说明

💡 快速开始：
• 发送"支出 20 餐饮"记录支出
• 发送"贷款 房贷 5000"添加贷款
• 发送"今日"查看今日统计'''
        reply = create_reply(welcome, msg)
        return reply.render()
    
    # 其他消息类型返回提示
    else:
        reply = create_reply('暂不支持此类型消息，请发送文字', msg)
        return reply.render()


@app.route('/')
def index():
    """首页"""
    return '''
    <html>
    <head>
        <meta charset="utf-8">
        <title>记账小助手</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                   max-width: 600px; margin: 50px auto; padding: 20px; }
            h1 { color: #07c160; }
            .status { background: #f0f0f0; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>📒 微信记账小助手</h1>
        <div class="status">
            <p>✅ 服务运行中</p>
            <p>微信接口地址: <code>/wechat</code></p>
        </div>
        <h2>功能介绍</h2>
        <ul>
            <li>📝 日常记账（收入/支出）</li>
            <li>🏠 贷款管理（房贷/车贷）</li>
            <li>📌 固定开支（物业/停车）</li>
            <li>📊 统计报表（今日/本月）</li>
            <li>⏰ 每日推送欠款提醒</li>
        </ul>
    </body>
    </html>
    '''


@app.route('/health')
def health():
    """健康检查"""
    return {'status': 'ok'}


def main():
    """启动应用"""
    print("=" * 50)
    print("微信记账小助手启动中...")
    print("=" * 50)
    
    # 初始化数据库
    init_db()
    
    # 初始化定时任务
    init_scheduler()
    
    try:
        # 启动 Flask 应用
        print(f"\n服务地址: http://{FLASK_HOST}:{FLASK_PORT}")
        print(f"微信接口: http://{FLASK_HOST}:{FLASK_PORT}/wechat")
        print("\n请使用 ngrok 或类似工具暴露到公网")
        print("=" * 50)
        
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, use_reloader=False)
    finally:
        shutdown_scheduler()


if __name__ == '__main__':
    main()
