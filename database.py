"""
SQLite 数据库操作模块

提供用户和记账记录的 CRUD 操作
"""

import sqlite3
import os
from datetime import datetime, date
from contextlib import contextmanager
from config import DATABASE_PATH


def get_db_path():
    """获取数据库路径，确保目录存在"""
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    return DATABASE_PATH


@contextmanager
def get_connection():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """初始化数据库表"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                openid TEXT PRIMARY KEY,
                nickname TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建记账记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                openid TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (openid) REFERENCES users(openid)
            )
        ''')
        
        # 创建固定开支/贷款表（支持总额+月数计算）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recurring_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                openid TEXT NOT NULL,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                total_amount REAL,
                total_months INTEGER,
                monthly_amount REAL NOT NULL,
                start_date DATE,
                end_date DATE,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (openid) REFERENCES users(openid)
            )
        ''')

        # 创建家庭组表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS families (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                invite_code TEXT UNIQUE NOT NULL,
                creator_openid TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_openid) REFERENCES users(openid)
            )
        ''')

        # 创建家庭成员表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id INTEGER NOT NULL,
                openid TEXT NOT NULL,
                role TEXT DEFAULT 'member', -- 'creator' or 'member'
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(family_id, openid),
                FOREIGN KEY (family_id) REFERENCES families(id),
                FOREIGN KEY (openid) REFERENCES users(openid)
            )
        ''')
        
        conn.commit()
        print("数据库初始化完成")


def add_user(openid: str, nickname: str = None):
    """添加或更新用户"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (openid, nickname, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (openid, nickname))
        conn.commit()


def add_expense(openid: str, expense_type: str, amount: float, 
                category: str = None, description: str = None) -> int:
    """
    添加记账记录
    
    Args:
        openid: 用户 OpenID
        expense_type: 类型 ('income' 或 'expense')
        amount: 金额
        category: 分类
        description: 备注
    
    Returns:
        记录 ID
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO expenses (openid, type, amount, category, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (openid, expense_type, amount, category, description))
        conn.commit()
        return cursor.lastrowid


def get_today_summary(openid: str) -> dict:
    """
    获取用户今日收支统计
    
    Returns:
        {
            'income': 总收入,
            'expense': 总支出,
            'balance': 结余,
            'records': 记录列表
        }
    """
    today = date.today().isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 获取今日收入总额
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE openid = ? AND type = 'income'
            AND date(created_at) = ?
        ''', (openid, today))
        income = cursor.fetchone()['total']
        
        # 获取今日支出总额
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE openid = ? AND type = 'expense'
            AND date(created_at) = ?
        ''', (openid, today))
        expense = cursor.fetchone()['total']
        
        # 获取今日记录详情
        cursor.execute('''
            SELECT type, amount, category, description, created_at
            FROM expenses
            WHERE openid = ? AND date(created_at) = ?
            ORDER BY created_at DESC
        ''', (openid, today))
        records = [dict(row) for row in cursor.fetchall()]
        
        return {
            'income': income,
            'expense': expense,
            'balance': income - expense,
            'records': records
        }


def get_month_summary(openid: str) -> dict:
    """
    获取用户本月收支统计
    
    Returns:
        {
            'income': 总收入,
            'expense': 总支出,
            'balance': 结余,
            'days': 记账天数
        }
    """
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 获取本月收入总额
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE openid = ? AND type = 'income'
            AND date(created_at) >= ?
        ''', (openid, month_start))
        income = cursor.fetchone()['total']
        
        # 获取本月支出总额
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE openid = ? AND type = 'expense'
            AND date(created_at) >= ?
        ''', (openid, month_start))
        expense = cursor.fetchone()['total']
        
        # 获取记账天数
        cursor.execute('''
            SELECT COUNT(DISTINCT date(created_at)) as days
            FROM expenses
            WHERE openid = ? AND date(created_at) >= ?
        ''', (openid, month_start))
        days = cursor.fetchone()['days']
        
        return {
            'income': income,
            'expense': expense,
            'balance': income - expense,
            'days': days
        }


def get_all_users() -> list:
    """获取所有用户的 OpenID 列表（用于每日推送）"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT openid FROM users')
        return [row['openid'] for row in cursor.fetchall()]


def add_recurring_expense(openid: str, expense_type: str, name: str, 
                          total_amount: float = None, total_months: int = None,
                          monthly_amount: float = None) -> int:
    """
    添加固定开支/贷款
    
    支持两种输入方式：
    1. 总金额 + 月数 → 自动计算每月金额
    2. 直接输入每月金额
    
    Args:
        openid: 用户 OpenID
        expense_type: 类型 ('loan' 贷款 或 'fixed' 固定开支)
        name: 名称（如 房贷、车贷、物业费）
        total_amount: 总金额（可选）
        total_months: 还款月数（可选）
        monthly_amount: 每月金额（如果提供 total_amount 和 total_months 则自动计算）
    
    Returns:
        记录 ID
    """
    # 如果提供了总金额和月数，自动计算每月金额
    if total_amount is not None and total_months is not None:
        monthly_amount = round(total_amount / total_months, 2)
    
    if monthly_amount is None:
        raise ValueError("必须提供 monthly_amount 或 (total_amount + total_months)")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO recurring_expenses 
            (openid, type, name, total_amount, total_months, monthly_amount, start_date)
            VALUES (?, ?, ?, ?, ?, ?, date('now'))
        ''', (openid, expense_type, name, total_amount, total_months, monthly_amount))
        conn.commit()
        return cursor.lastrowid


def get_recurring_expenses(openid: str) -> list:
    """获取用户的所有固定开支/贷款"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, type, name, total_amount, total_months, monthly_amount, start_date, end_date
            FROM recurring_expenses
            WHERE openid = ? AND is_active = 1
            ORDER BY type, monthly_amount DESC
        ''', (openid,))
        return [dict(row) for row in cursor.fetchall()]


def delete_recurring_expense(openid: str, expense_id: int) -> bool:
    """删除（停用）固定开支/贷款"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE recurring_expenses 
            SET is_active = 0 
            WHERE id = ? AND openid = ?
        ''', (expense_id, openid))
        conn.commit()
        return cursor.rowcount > 0


def get_daily_debt(openid: str) -> dict:
    """
    计算每日欠款（所有固定开支和贷款的日均值总和）
    
    Returns:
        {
            'daily_total': 每日欠款总额,
            'monthly_total': 每月欠款总额,
            'details': [
                {'name': '房贷', 'monthly': 5000, 'daily': 166.67},
                ...
            ]
        }
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT type, name, monthly_amount
            FROM recurring_expenses
            WHERE openid = ? AND is_active = 1
            AND (end_date IS NULL OR end_date >= date('now'))
        ''', (openid,))
        
        rows = cursor.fetchall()
        
        details = []
        monthly_total = 0
        
        for row in rows:
            monthly = row['monthly_amount']
            daily = round(monthly / 30, 2)  # 按30天计算日均
            monthly_total += monthly
            details.append({
                'type': row['type'],
                'name': row['name'],
                'monthly': monthly,
                'daily': daily
            })
        
        return {
            'daily_total': round(monthly_total / 30, 2),
            'monthly_total': monthly_total,
            'details': details
        }


def create_family(openid: str, name: str) -> str:
    """创建家庭组，返回邀请码"""
    import random
    import string
    invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO families (name, invite_code, creator_openid)
                VALUES (?, ?, ?)
            ''', (name, invite_code, openid))
            family_id = cursor.lastrowid
            
            cursor.execute('''
                INSERT INTO family_members (family_id, openid, role)
                VALUES (?, ?, 'creator')
            ''', (family_id, openid))
            
            conn.commit()
            return invite_code
        except sqlite3.IntegrityError:
            # 邀请码重复则重试一次
            return create_family(openid, name)


def join_family(openid: str, invite_code: str) -> bool:
    """加入家庭组"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM families WHERE invite_code = ?', (invite_code,))
        row = cursor.fetchone()
        if not row:
            return False
        
        family_id = row['id']
        try:
            cursor.execute('''
                INSERT INTO family_members (family_id, openid, role)
                VALUES (?, ?, 'member')
            ''', (family_id, openid))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return True # 已经在家庭中了


def get_user_family(openid: str) -> dict:
    """获取用户所属的家庭信息"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.id, f.name, f.invite_code, fm.role
            FROM families f
            JOIN family_members fm ON f.id = fm.family_id
            WHERE fm.openid = ?
        ''', (openid,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_family_members(family_id: int) -> list:
    """获取家庭所有成员的 openid"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT openid FROM family_members WHERE family_id = ?', (family_id,))
        return [row['openid'] for row in cursor.fetchall()]


def leave_family(openid: str) -> bool:
    """退出家庭组"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM family_members WHERE openid = ?', (openid,))
        conn.commit()
        return cursor.rowcount > 0


def get_family_members_detail(family_id: int) -> list:
    """获取家庭所有成员的详细信息"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT fm.openid, fm.role, fm.joined_at, u.nickname
            FROM family_members fm
            LEFT JOIN users u ON fm.openid = u.openid
            WHERE fm.family_id = ?
            ORDER BY fm.role DESC, fm.joined_at
        ''', (family_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_family_debt_ranking(family_id: int) -> dict:
    """获取家庭成员欠款排行"""
    members = get_family_members(family_id)
    ranking = []
    total_daily = 0
    total_monthly = 0
    
    for openid in members:
        debt = get_daily_debt(openid)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nickname FROM users WHERE openid = ?', (openid,))
            row = cursor.fetchone()
            nickname = row['nickname'] if row and row['nickname'] else openid[:8]
        
        ranking.append({
            'openid': openid,
            'nickname': nickname,
            'daily': debt['daily_total'],
            'monthly': debt['monthly_total'],
            'details': debt['details']
        })
        total_daily += debt['daily_total']
        total_monthly += debt['monthly_total']
    
    # 按每日欠款排序（从高到低）
    ranking.sort(key=lambda x: x['daily'], reverse=True)
    
    return {
        'ranking': ranking,
        'total_daily': round(total_daily, 2),
        'total_monthly': round(total_monthly, 2)
    }


if __name__ == '__main__':
    # 测试代码
    init_db()
    print("数据库测试完成")
