"""
定时任务调度模块

实现每日推送功能
"""

from apscheduler.schedulers.background import BackgroundScheduler
from wechatpy import WeChatClient
from config import (
    WECHAT_APP_ID, WECHAT_APP_SECRET,
    DAILY_PUSH_HOUR, DAILY_PUSH_MINUTE
)
from database import get_all_users
from wechat_handler import get_daily_push_message


# 全局调度器实例
scheduler = None


def send_daily_push():
    """发送每日推送"""
    print(f"[定时任务] 开始发送每日推送...")
    
    try:
        # 初始化微信客户端
        client = WeChatClient(WECHAT_APP_ID, WECHAT_APP_SECRET)
        
        # 获取所有用户
        users = get_all_users()
        print(f"[定时任务] 共有 {len(users)} 个用户")
        
        success_count = 0
        for openid in users:
            try:
                # 生成推送消息
                message = get_daily_push_message(openid)
                
                # 发送客服消息
                client.message.send_text(openid, message)
                success_count += 1
                print(f"[定时任务] 成功推送给用户: {openid[:8]}...")
            except Exception as e:
                print(f"[定时任务] 推送失败 {openid[:8]}...: {e}")
        
        print(f"[定时任务] 推送完成，成功 {success_count}/{len(users)}")
        
    except Exception as e:
        print(f"[定时任务] 发送失败: {e}")


def init_scheduler():
    """初始化并启动调度器"""
    global scheduler
    
    if scheduler is not None:
        return scheduler
    
    scheduler = BackgroundScheduler()
    
    # 添加每日推送任务
    scheduler.add_job(
        send_daily_push,
        'cron',
        hour=DAILY_PUSH_HOUR,
        minute=DAILY_PUSH_MINUTE,
        id='daily_push',
        replace_existing=True
    )
    
    scheduler.start()
    print(f"[调度器] 已启动，每日 {DAILY_PUSH_HOUR:02d}:{DAILY_PUSH_MINUTE:02d} 推送")
    
    return scheduler


def shutdown_scheduler():
    """关闭调度器"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        print("[调度器] 已关闭")


if __name__ == '__main__':
    # 测试推送（手动触发）
    print("测试每日推送...")
    send_daily_push()
