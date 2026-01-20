"""
微信消息处理模块

解析用户发送的消息并执行相应操作
"""

import re
from database import (
    add_user, add_expense, get_today_summary, get_month_summary,
    add_recurring_expense, get_recurring_expenses, delete_recurring_expense,
    get_daily_debt, create_family, join_family, get_user_family, get_family_members, leave_family,
    get_family_members_detail, get_family_debt_ranking,
    get_family_recurring_expenses, get_family_daily_debt, update_nickname,
    get_expense_history, get_category_stats, set_budget, get_budget, is_family_creator
)


def parse_message(openid: str, content: str, notify_callback=None) -> str:
    """
    解析用户消息并返回响应
    
    Args:
        openid: 用户 OpenID
        content: 消息内容
        notify_callback: 用于发送通知的回调函数 (openid, message)
    
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
        
        response = f'✅ 已记录支出 {amount} 元\n分类：{category}' + (f'\n备注：{description}' if description else '')
        
        # 家庭组通知逻辑
        family = get_user_family(openid)
        if family and notify_callback:
            members = get_family_members(family['id'])
            month_summary = get_month_summary(openid)
            debt = get_daily_debt(openid)
            
            notify_msg = f'''📢 家庭支出提醒

成员：{"另一半" if family["role"] == "member" else "创建者"}
物品：{category}
金额：{amount:.2f} 元'''
            if description:
                notify_msg += f'\n备注：{description}'
            
            notify_msg += f'''

📊 本月累计支出：{month_summary["expense"]:.2f} 元
🏠 每日固定欠款：{debt["daily_total"]:.2f} 元'''
            
            for member_openid in members:
                if member_openid != openid:
                    notify_callback(member_openid, notify_msg)
        
        return response
    
    # 收入指令: 收入 金额 [分类] [备注]
    match = re.match(r'^收入\s+(\d+(?:\.\d+)?)\s*(\S*)\s*(.*)$', content)
    if match:
        amount = float(match.group(1))
        category = match.group(2) or '其他'
        description = match.group(3) or None
        add_expense(openid, 'income', amount, category, description)
        return f'✅ 已记录收入 {amount} 元\n分类：{category}' + (f'\n备注：{description}' if description else '')
    
    # 添加贷款: 支持两种格式
    # 格式1: 贷款 名称 总金额 月数 (如: 贷款 房贷 1000000 360)
    # 格式2: 贷款 名称 月供金额 (如: 贷款 房贷 5000)
    match = re.match(r'^(?:添加)?贷款\s+(\S+)\s+(\d+(?:\.\d+)?)\s+(\d+)$', content)
    if match:
        name = match.group(1)
        total_amount = float(match.group(2))
        total_months = int(match.group(3))
        monthly = round(total_amount / total_months, 2)
        daily = round(monthly / 30, 2)
        add_recurring_expense(openid, 'loan', name, 
                              total_amount=total_amount, total_months=total_months)
        return f'''✅ 已添加贷款：{name}

💰 总金额：{total_amount:,.0f} 元
📅 还款期：{total_months} 个月
📆 每月还：{monthly:,.2f} 元
📌 每日均：{daily:.2f} 元'''
    
    # 贷款简化格式: 贷款 名称 月供
    match = re.match(r'^(?:添加)?贷款\s+(\S+)\s+(\d+(?:\.\d+)?)$', content)
    if match:
        name = match.group(1)
        monthly = float(match.group(2))
        daily = round(monthly / 30, 2)
        add_recurring_expense(openid, 'loan', name, monthly_amount=monthly)
        return f'''✅ 已添加贷款：{name}

📆 每月还：{monthly:,.2f} 元
📌 每日均：{daily:.2f} 元'''
    
    # 添加固定开支: 支持两种格式
    # 格式1: 固定 名称 年费 12 (如: 固定 保险 3600 12)
    # 格式2: 固定 名称 月费 (如: 固定 物业 200)
    match = re.match(r'^(?:添加)?固定\s+(\S+)\s+(\d+(?:\.\d+)?)\s+(\d+)$', content)
    if match:
        name = match.group(1)
        total_amount = float(match.group(2))
        total_months = int(match.group(3))
        monthly = round(total_amount / total_months, 2)
        daily = round(monthly / 30, 2)
        add_recurring_expense(openid, 'fixed', name,
                              total_amount=total_amount, total_months=total_months)
        return f'''✅ 已添加固定开支：{name}

💰 总金额：{total_amount:,.0f} 元
📅 周期：{total_months} 个月
📆 每月均：{monthly:,.2f} 元
📌 每日均：{daily:.2f} 元'''
    
    # 固定开支简化格式: 固定 名称 月费
    match = re.match(r'^(?:添加)?固定\s+(\S+)\s+(\d+(?:\.\d+)?)$', content)
    if match:
        name = match.group(1)
        monthly = float(match.group(2))
        daily = round(monthly / 30, 2)
        add_recurring_expense(openid, 'fixed', name, monthly_amount=monthly)
        return f'''✅ 已添加固定开支：{name}

📆 每月：{monthly:,.2f} 元
📌 每日均：{daily:.2f} 元'''
    
    # 添加负债/分期: 负债 名称 总金额 月数 (如: 负债 信用卡分期 12000 12)
    match = re.match(r'^(?:添加)?负债\s+(\S+)\s+(\d+(?:\.\d+)?)\s+(\d+)$', content)
    if match:
        name = match.group(1)
        total_amount = float(match.group(2))
        total_months = int(match.group(3))
        monthly = round(total_amount / total_months, 2)
        daily = round(monthly / 30, 2)
        add_recurring_expense(openid, 'debt', name,
                              total_amount=total_amount, total_months=total_months)
        return f'''✅ 已添加负债：{name}

💰 总金额：{total_amount:,.0f} 元
📅 分期数：{total_months} 个月
📆 每月还：{monthly:,.2f} 元
📌 每日均：{daily:.2f} 元'''
    
    # 删除固定开支/贷款: 删除 ID（仅家庭创建人可操作）
    match = re.match(r'^删除\s+(\d+)$', content)
    if match:
        expense_id = int(match.group(1))
        family = get_user_family(openid)
        
        # 如果在家庭中，只有创建人可以删除
        if family and not is_family_creator(openid):
            return '❌ 只有家庭创建人才能删除记录'
        
        if delete_recurring_expense(openid, expense_id):
            return f'✅ 已删除固定开支/贷款 (ID: {expense_id})'
        else:
            return '❌ 未找到该记录或无权删除'
    
    # 家庭组功能
    if content.startswith('创建家庭'):
        name = content[4:].strip() or "我的家庭"
        code = create_family(openid, name)
        return f'👨‍👩‍👧‍👦 家庭「{name}」创建成功！\n\n邀请码：{code}\n\n发送「加入家庭 {code}」让另一半加入吧！'
    
    if content.startswith('加入家庭'):
        code = content[4:].strip().upper()
        if join_family(openid, code):
            family = get_user_family(openid)
            return f'✅ 成功加入家庭「{family["name"]}」！\n\n现在你们可以共享账本了。'
        else:
            return '❌ 邀请码无效，请检查后重试。'
    
    if content == '退出家庭':
        if leave_family(openid):
            return '👋 已成功退出家庭组。'
        else:
            return '❌ 您当前不在任何家庭组中。'
    
    # 修改昵称: 昵称 名字
    match = re.match(r'^(?:昵称|改名|我叫)\s+(\S+)$', content)
    if match:
        nickname = match.group(1)
        update_nickname(openid, nickname)
        return f'✅ 昵称已更新为：{nickname}'

    if content == '家庭':
        family = get_user_family(openid)
        if family:
            members = get_family_members_detail(family['id'])
            
            msg = f'''👨‍👩‍👧‍👦 {family["name"]}
┌─────────────────────
│ 邀请码：{family["invite_code"]}
└─────────────────────

👥 成员列表'''
            
            for m in members:
                role_icon = '👑' if m['role'] == 'creator' else '👤'
                nickname = m['nickname'] or f"用户{m['openid'][-4:]}"
                is_me = " (我)" if m['openid'] == openid else ""
                msg += f'\n{role_icon} {nickname}{is_me}'
            
            msg += '\n\n💡 发送「家庭欠款」查看排行'
            return msg
        else:
            return '📋 您当前不在任何家庭组中。\n\n发送「创建家庭 名称」来创建一个吧！'
    
    if content == '家庭成员':
        family = get_user_family(openid)
        if not family:
            return '❌ 您当前不在任何家庭组中。'
        
        members = get_family_members_detail(family['id'])
        msg = f'👨‍👩‍👧‍👦 {family["name"]} 成员列表\n'
        msg += '━━━━━━━━━━━━━━━━━\n'
        
        for i, m in enumerate(members):
            role_icon = '👑' if m['role'] == 'creator' else '👤'
            nickname = m['nickname'] or m['openid'][:8]
            msg += f'{role_icon} {nickname}'
            if m['role'] == 'creator':
                msg += ' (创建者)'
            msg += '\n'
        
        msg += f'\n邀请码：{family["invite_code"]}'
        return msg
    
    if content == '家庭欠款':
        family = get_user_family(openid)
        if not family:
            return '❌ 您当前不在任何家庭组中。'
        
        ranking = get_family_debt_ranking(family['id'])
        
        if ranking['total_daily'] == 0:
            return '📋 家庭成员暂无欠款记录。\n\n发送「初始化」开始设置贷款和固定开支。'
        
        msg = f'''👨‍👩‍👧‍👦 {family["name"]} 欠款排行

💸 每日合计：{ranking["total_daily"]:.2f} 元
📅 每月合计：{ranking["total_monthly"]:,.2f} 元

━━━━━━━━━━━━━━━━━'''
        
        medals = ['🥇', '🥈', '🥉']
        for i, r in enumerate(ranking['ranking']):
            medal = medals[i] if i < 3 else f'{i+1}.'
            nickname = r['nickname'] or r['openid'][:8]
            msg += f'\n{medal} {nickname}：-{r["daily"]:.2f}元/日'
            
            # 显示详情
            if r['details']:
                detail_names = [d['name'] for d in r['details'][:3]]
                msg += f'\n   ({", ".join(detail_names)})'
        
        msg += '\n\n💪 大家一起努力搬砖！'
        return msg
    
    # 历史记录: 历史 [天数]
    match = re.match(r'^历史(?:\s+(\d+))?$', content)
    if match:
        days = int(match.group(1)) if match.group(1) else 7
        records = get_expense_history(openid, days)
        
        if not records:
            return f'📋 最近{days}天暂无记账记录'
        
        msg = f'📋 最近{days}天记录\n'
        msg += '─────────────────────'
        
        current_date = None
        for r in records:
            if r['date'] != current_date:
                current_date = r['date']
                msg += f'\n\n📅 {current_date}'
            
            icon = '💵' if r['type'] == 'income' else '💸'
            category = r['category'] or '其他'
            msg += f'\n{icon} {category} {r["amount"]:.0f}元'
            if r['description']:
                msg += f' ({r["description"]})'
        
        return msg
    
    # 分类统计: 统计 [分类] [天数]
    match = re.match(r'^统计(?:\s+(\S+))?(?:\s+(\d+))?$', content)
    if match:
        category_filter = match.group(1)
        days = int(match.group(2)) if match.group(2) else 30
        
        stats = get_category_stats(openid, days)
        
        if stats['total'] == 0:
            return f'📊 最近{days}天暂无支出记录'
        
        msg = f'''📊 支出统计（{days}天）
┌─────────────────────
│ 💸 总支出：{stats["total"]:,.0f} 元
└─────────────────────
'''
        
        for c in stats['categories']:
            cat_name = c['category'] or '其他'
            percent = c['total'] / stats['total'] * 100
            bar_len = int(percent / 10)
            bar = '█' * bar_len + '░' * (10 - bar_len)
            msg += f'\n{cat_name}：{c["total"]:,.0f}元'
            msg += f'\n{bar} {percent:.0f}%'
        
        return msg
    
    # 预算设置: 预算 金额
    match = re.match(r'^预算\s+(\d+(?:\.\d+)?)$', content)
    if match:
        amount = float(match.group(1))
        set_budget(openid, amount)
        return f'✅ 月预算已设置为：{amount:,.0f} 元'
    
    # 预算查看: 预算
    if content == '预算':
        budget_info = get_budget(openid)
        
        if not budget_info['budget']:
            return '📋 您还未设置预算\n\n发送「预算 5000」设置月预算'
        
        budget = budget_info['budget']
        spent = budget_info['spent']
        remaining = budget_info['remaining']
        percent = budget_info['percent']
        
        # 进度条
        bar_len = min(int(percent / 10), 10)
        bar = '█' * bar_len + '░' * (10 - bar_len)
        
        # 状态提示
        if percent >= 100:
            status = '🚨 已超支！'
        elif percent >= 80:
            status = '⚠️ 即将超支'
        else:
            status = '✅ 正常'
        
        return f'''💰 本月预算
┌─────────────────────
│ 预算：{budget:,.0f} 元
│ 已用：{spent:,.0f} 元
│ 剩余：{remaining:,.0f} 元
└─────────────────────

{bar} {percent:.0f}%
{status}'''
    
    # 初始化引导
    if content in ['初始化', '设置', '开始', 'start', 'init']:
        return get_init_guide()
    
    # 未识别的指令
    return '❓ 无法识别的指令，发送"帮助"查看使用说明'


def get_init_guide() -> str:
    """返回初始化录入引导"""
    return '''🚀 欢迎使用记账小助手！

让我们来设置您的固定开支，这样每天都能提醒您"眼睛一睁欠了多少钱"💸

━━━━━━━━━━━━━━━━━
📍 第一步：添加贷款
━━━━━━━━━━━━━━━━━
格式：贷款 名称 总金额 月数

🏠 房贷：贷款 房贷 1000000 360
🚗 车贷：贷款 车贷 150000 60

━━━━━━━━━━━━━━━━━
📍 第二步：添加分期/负债
━━━━━━━━━━━━━━━━━
格式：负债 名称 总金额 月数

💳 信用卡：负债 信用卡分期 12000 12
📱 手机：负债 iPhone分期 8000 24

━━━━━━━━━━━━━━━━━
📍 第三步：添加固定开支
━━━━━━━━━━━━━━━━━
格式：固定 名称 月费

🏢 物业：固定 物业 200
🅿️ 停车：固定 停车 300
📱 话费：固定 话费 100

━━━━━━━━━━━━━━━━━
📍 第四步：查看汇总
━━━━━━━━━━━━━━━━━
发送「欠款」查看每日欠款明细

💡 提示：每条单独发送一条消息'''


def get_help_message() -> str:
    """返回帮助信息"""
    return '''📖 记账小助手使用指南

💰 【日常记账】
• 支出 50 餐饮 午餐
• 收入 1000 工资

🏠 【贷款】
• 贷款 房贷 1000000 360

💳 【负债/分期】
• 负债 信用卡分期 12000 12

📌 【固定开支】
• 固定 物业 200

📊 【查询统计】
• 今日/本月/欠款
• 历史 [天数]
• 统计 [天数]
• 预算 [金额]

👨‍👩‍👧‍👦 【家庭组】
• 创建家庭/加入家庭
• 家庭/家庭欠款
• 昵称 名字

💡 发送「初始化」开始设置'''


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
    """生成固定开支/贷款报告（家庭共享）"""
    family = get_user_family(openid)
    
    # 如果在家庭中，显示家庭共享账单
    if family:
        expenses = get_family_recurring_expenses(family['id'])
        debt = get_family_daily_debt(family['id'])
        title = f"👨‍👩‍👧‍👦 {family['name']} 共享账单"
    else:
        expenses = get_recurring_expenses(openid)
        debt = get_daily_debt(openid)
        title = "💰 欠款总览"
    
    if not expenses:
        return '📋 暂无固定开支/贷款记录\n\n发送「初始化」开始设置贷款和固定开支'
    
    # 按类型分组
    type_groups = {'loan': [], 'debt': [], 'fixed': []}
    for e in expenses:
        exp_type = e.get('type', 'fixed')
        if exp_type in type_groups:
            type_groups[exp_type].append(e)
        else:
            type_groups['fixed'].append(e)
    
    msg = f'''{title}
┌─────────────────────
│ 📌 每日：{debt["daily_total"]:,.2f} 元
│ 📅 每月：{debt["monthly_total"]:,.2f} 元
└─────────────────────'''
    
    type_config = {
        'loan': ('🏠', '贷款'),
        'debt': ('💳', '负债'),
        'fixed': ('📝', '固定开支')
    }
    
    for type_key, (icon, type_name) in type_config.items():
        items = type_groups.get(type_key, [])
        if not items:
            continue
            
        msg += f"\n\n{icon} {type_name}"
        msg += "\n" + "─" * 18
        
        for e in items:
            daily = e['monthly_amount'] / 30
            name = e['name']
            
            # 家庭模式显示归属人
            owner_tag = ""
            if family and e.get('nickname'):
                owner_tag = f" [{e['nickname'] or '?'}]"
            elif family and e.get('openid'):
                owner_tag = f" [用户{e['openid'][-4:]}]"
            
            if e.get('total_amount') and e.get('total_months'):
                msg += f"\n[{e['id']}] {name}{owner_tag}"
                msg += f"\n    {e['total_amount']:,.0f} ÷ {e['total_months']}期"
                msg += f"\n    → {e['monthly_amount']:,.0f}/月 | {daily:.0f}/日"
            else:
                msg += f"\n[{e['id']}] {name}{owner_tag}"
                msg += f"\n    → {e['monthly_amount']:,.0f}/月 | {daily:.0f}/日"
    
    msg += '\n\n─────────────────────'
    msg += '\n💡 删除命令：删除 ID'
    
    return msg


def get_daily_push_message(openid: str) -> str:
    """生成每日推送消息"""
    debt = get_daily_debt(openid)
    today_summary = get_today_summary(openid)
    family = get_user_family(openid)
    
    # 计算今日净收入（考虑固定开支）
    daily_debt = debt['daily_total']
    today_income = today_summary['income']
    today_expense = today_summary['expense']
    net_income = today_income - today_expense - daily_debt
    
    # 生成推送消息
    if daily_debt > 0 or (family and get_family_debt_ranking(family['id'])['total_daily'] > 0):
        msg = f'''☀️ 早安！眼睛一睁

💸 你今日的收入是：{net_income:,.2f} 元

📊 每日欠款明细：'''
        
        type_icons = {'loan': '🏠', 'debt': '💳', 'fixed': '📝'}
        for d in debt['details']:
            icon = type_icons.get(d['type'], '📌')
            msg += f'\n{icon} {d["name"]}：-{d["daily"]:.2f}元'
        
        msg += f'''

━━━━━━━━━━━━━━━━━
📌 每日欠款：{daily_debt:.2f} 元
📅 每月欠款：{debt["monthly_total"]:,.2f} 元'''

        # 如果在家庭组中，添加家庭排行
        if family:
            ranking = get_family_debt_ranking(family['id'])
            if ranking['total_daily'] > 0:
                msg += f'''

👨‍👩‍👧‍👦 家庭欠款排行：'''
                medals = ['🥇', '🥈', '🥉']
                for i, r in enumerate(ranking['ranking']):
                    if r['daily'] > 0:
                        medal = medals[i] if i < 3 else f'{i+1}.'
                        nickname = r['nickname'] or r['openid'][:8]
                        msg += f'\n{medal} {nickname}：-{r["daily"]:.2f}元/日'
                
                msg += f'''

💰 全家每日：{ranking["total_daily"]:.2f} 元
📅 全家每月：{ranking["total_monthly"]:,.2f} 元'''
        
        msg += '\n\n💪 努力搬砖，今天也要加油！'
    else:
        msg = f'''☀️ 早安！

昨日结余：{today_summary["balance"]:.2f} 元

还没有设置固定开支哦~
发送「初始化」开始设置贷款和固定开支'''
    
    return msg
