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
        
        # 创建固定开支/贷款表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recurring_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                openid TEXT NOT NULL,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                monthly_amount REAL NOT NULL,
                start_date DATE,
                end_date DATE,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
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
                          monthly_amount: float, end_date: str = None) -> int:
    """
    添加固定开支/贷款
    
    Args:
        openid: 用户 OpenID
        expense_type: 类型 ('loan' 贷款 或 'fixed' 固定开支)
        name: 名称（如 房贷、车贷、物业费）
        monthly_amount: 每月金额
        end_date: 结束日期（可选，格式 YYYY-MM-DD）
    
    Returns:
        记录 ID
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO recurring_expenses (openid, type, name, monthly_amount, start_date, end_date)
            VALUES (?, ?, ?, ?, date('now'), ?)
        ''', (openid, expense_type, name, monthly_amount, end_date))
        conn.commit()
        return cursor.lastrowid


def get_recurring_expenses(openid: str) -> list:
    """获取用户的所有固定开支/贷款"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, type, name, monthly_amount, start_date, end_date
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


if __name__ == '__main__':
    # 测试代码
    init_db()
    print("数据库测试完成")
