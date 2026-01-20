"""
微信消息处理模块

解析用户发送的消息并执行相应操作
"""

import re
from database import (
    add_user, add_expense, get_today_summary, get_month_summary,
    add_recurring_expense, get_recurring_expenses, delete_recurring_expense,
    get_daily_debt
)


def parse_message(openid: str, content: str) -> str:
    """
    解析用户消息并返回响应
    
    Args:
        openid: 用户 OpenID
        content: 消息内容
    
    Returns:
        响应文本
    """
    # 确保用户存在
    add_user(openid)
    
    content = content.strip()
    
    # 帮助指令
    if content in ['帮助', '?', '？', 'help']:
        return get_help_message()
    
    # 今日统计
    if content == '今日':
        return get_today_report(openid)
    
    # 本月统计
    if content == '本月':
        return get_month_report(openid)
    
    # 查看固定开支
    if content in ['固定', '贷款', '欠款']:
        return get_recurring_report(openid)
    
    # 支出指令: 支出 金额 [分类] [备注]
    match = re.match(r'^支出\s+(\d+(?:\.\d+)?)\s*(\S*)\s*(.*)$', content)
    if match:
        amount = float(match.group(1))
        category = match.group(2) or '其他'
        description = match.group(3) or None
        add_expense(openid, 'expense', amount, category, description)
        return f'✅ 已记录支出 {amount} 元\n分类：{category}' + (f'\n备注：{description}' if description else '')
    
    # 收入指令: 收入 金额 [分类] [备注]
    match = re.match(r'^收入\s+(\d+(?:\.\d+)?)\s*(\S*)\s*(.*)$', content)
    if match:
        amount = float(match.group(1))
        category = match.group(2) or '其他'
        description = match.group(3) or None
        add_expense(openid, 'income', amount, category, description)
        return f'✅ 已记录收入 {amount} 元\n分类：{category}' + (f'\n备注：{description}' if description else '')
    
    # 添加贷款: 贷款 名称 月供金额
    match = re.match(r'^(?:添加)?贷款\s+(\S+)\s+(\d+(?:\.\d+)?)$', content)
    if match:
        name = match.group(1)
        amount = float(match.group(2))
        add_recurring_expense(openid, 'loan', name, amount)
        daily = round(amount / 30, 2)
        return f'✅ 已添加贷款：{name}\n每月：{amount} 元\n每日：{daily} 元'
    
    # 添加固定开支: 固定 名称 月金额
    match = re.match(r'^(?:添加)?固定\s+(\S+)\s+(\d+(?:\.\d+)?)$', content)
    if match:
        name = match.group(1)
        amount = float(match.group(2))
        add_recurring_expense(openid, 'fixed', name, amount)
        daily = round(amount / 30, 2)
        return f'✅ 已添加固定开支：{name}\n每月：{amount} 元\n每日：{daily} 元'
    
    # 删除固定开支/贷款: 删除 ID
    match = re.match(r'^删除\s+(\d+)$', content)
    if match:
        expense_id = int(match.group(1))
        if delete_recurring_expense(openid, expense_id):
            return f'✅ 已删除固定开支/贷款 (ID: {expense_id})'
        else:
            return '❌ 未找到该记录'
    
    # 未识别的指令
    return '❓ 无法识别的指令，发送"帮助"查看使用说明'


def get_help_message() -> str:
    """返回帮助信息"""
    return '''📖 记账小助手使用指南

💰 【日常记账】
• 支出 50 餐饮 午餐
• 收入 1000 工资

🏠 【贷款/固定开支】
• 贷款 房贷 5000
• 固定 物业 200
• 固定 停车 300
• 删除 1  (删除ID为1的项)

📊 【查询统计】
• 今日 - 查看今日收支
• 本月 - 查看本月统计
• 欠款 - 查看固定开支明细

💡 提示：每天早上会推送欠款提醒'''


def get_today_report(openid: str) -> str:
    """生成今日报告"""
    summary = get_today_summary(openid)
    debt = get_daily_debt(openid)
    
    msg = f'''📅 今日账单

💵 收入：{summary["income"]:.2f} 元
💸 支出：{summary["expense"]:.2f} 元
📊 结余：{summary["balance"]:.2f} 元'''
    
    if debt['daily_total'] > 0:
        net = summary['balance'] - debt['daily_total']
        msg += f'''

🏠 每日固定支出：{debt["daily_total"]:.2f} 元
💰 实际结余：{net:.2f} 元'''
    
    if summary['records']:
        msg += '\n\n📝 今日明细：'
        for r in summary['records'][:5]:  # 最多显示5条
            type_icon = '💵' if r['type'] == 'income' else '💸'
            msg += f'\n{type_icon} {r["category"]} {r["amount"]}元'
    
    return msg


def get_month_report(openid: str) -> str:
    """生成本月报告"""
    summary = get_month_summary(openid)
    debt = get_daily_debt(openid)
    
    msg = f'''📅 本月统计

💵 总收入：{summary["income"]:.2f} 元
💸 总支出：{summary["expense"]:.2f} 元
📊 结余：{summary["balance"]:.2f} 元
📆 记账天数：{summary["days"]} 天'''
    
    if debt['monthly_total'] > 0:
        net = summary['balance'] - debt['monthly_total']
        msg += f'''

🏠 固定支出：{debt["monthly_total"]:.2f} 元
💰 实际结余：{net:.2f} 元'''
    
    return msg


def get_recurring_report(openid: str) -> str:
    """生成固定开支/贷款报告"""
    expenses = get_recurring_expenses(openid)
    debt = get_daily_debt(openid)
    
    if not expenses:
        return '📋 暂无固定开支/贷款记录\n\n发送"贷款 房贷 5000"添加贷款\n发送"固定 物业 200"添加固定开支'
    
    msg = f'''🏠 固定开支明细

每日合计：{debt["daily_total"]:.2f} 元
每月合计：{debt["monthly_total"]:.2f} 元

📋 详细列表：'''
    
    for e in expenses:
        type_icon = '🏦' if e['type'] == 'loan' else '📝'
        daily = round(e['monthly_amount'] / 30, 2)
        msg += f'\n{type_icon} [{e["id"]}] {e["name"]}：{e["monthly_amount"]}元/月 ({daily}元/日)'
    
    msg += '\n\n💡 发送"删除 ID"可删除对应项'
    
    return msg


def get_daily_push_message(openid: str) -> str:
    """生成每日推送消息"""
    debt = get_daily_debt(openid)
    today_summary = get_today_summary(openid)
    
    # 计算今日净收入（考虑固定开支）
    daily_debt = debt['daily_total']
    today_income = today_summary['income']
    today_expense = today_summary['expense']
    net_income = today_income - today_expense - daily_debt
    
    # 生成推送消息
    if daily_debt > 0:
        msg = f'''☀️ 早安！眼睛一睁

💸 你今日的收入是：{net_income:.2f} 元

📊 欠款明细：'''
        
        for d in debt['details']:
            type_name = '贷款' if d['type'] == 'loan' else '固定'
            msg += f'\n• {d["name"]}({type_name})：-{d["daily"]:.2f}元'
        
        msg += f'''

💰 每日固定支出：{daily_debt:.2f} 元
📅 每月固定支出：{debt["monthly_total"]:.2f} 元

努力搬砖，今天也要加油！💪'''
    else:
        msg = f'''☀️ 早安！

昨日结余：{today_summary["balance"]:.2f} 元

还没有设置固定开支哦~
发送"帮助"查看如何添加贷款和固定开支'''
    
    return msg
