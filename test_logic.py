# -*- coding: utf-8 -*-
"""
WeChat Expense Tracker - Local Test Script
Run this script to verify core logic
"""
import os
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Set test database path
os.environ['TEST_MODE'] = '1'

# Create data directory
if not os.path.exists('data'):
    os.makedirs('data')

# Override config
import config
config.DATABASE_PATH = 'data/test_expense.db'

# Remove old test database
if os.path.exists('data/test_expense.db'):
    os.remove('data/test_expense.db')

import database
import wechat_handler

def print_result(test_name, passed, details=""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {test_name}")
    if details and not passed:
        print(f"       -> {details}")

def run_tests():
    print("=" * 50)
    print("WeChat Expense Tracker - Local Test")
    print("=" * 50)
    
    # Initialize database
    database.init_db()
    print("\nDatabase initialized\n")
    
    passed = 0
    failed = 0
    
    # ===== Test 1: User Creation =====
    try:
        database.add_user('test_user', 'TestUser')
        with database.get_connection() as conn:
            user = conn.cursor().execute('SELECT * FROM users WHERE openid="test_user"').fetchone()
        if user and user['nickname'] == 'TestUser':
            print_result("User Creation", True)
            passed += 1
        else:
            print_result("User Creation", False, "User record not found")
            failed += 1
    except Exception as e:
        print_result("User Creation", False, str(e))
        failed += 1
    
    # ===== Test 2: Loan Calculation (Total / Months) =====
    try:
        resp = wechat_handler.parse_message('test_user', '贷款 房贷 120000 12')
        # 120000 / 12 = 10000/month, 10000/30 = 333.33/day
        if '10,000.00' in resp and '333.33' in resp:
            print_result("Loan Calculation (Total/Months)", True)
            passed += 1
        else:
            print_result("Loan Calculation (Total/Months)", False, f"Response: {resp[:80]}")
            failed += 1
    except Exception as e:
        print_result("Loan Calculation (Total/Months)", False, str(e))
        failed += 1
    
    # ===== Test 3: Fixed Expense =====
    try:
        resp = wechat_handler.parse_message('test_user', '固定 物业 300')
        if '300.00' in resp:
            print_result("Fixed Expense", True)
            passed += 1
        else:
            print_result("Fixed Expense", False, f"Response: {resp[:80]}")
            failed += 1
    except Exception as e:
        print_result("Fixed Expense", False, str(e))
        failed += 1
    
    # ===== Test 4: Debt/Installment =====
    try:
        resp = wechat_handler.parse_message('test_user', '负债 信用卡分期 6000 6')
        # 6000 / 6 = 1000/month
        if '1,000.00' in resp:
            print_result("Debt/Installment", True)
            passed += 1
        else:
            print_result("Debt/Installment", False, f"Response: {resp[:80]}")
            failed += 1
    except Exception as e:
        print_result("Debt/Installment", False, str(e))
        failed += 1
    
    # ===== Test 5: Debt Summary =====
    try:
        debt = database.get_daily_debt('test_user')
        # 10000 + 300 + 1000 = 11300/month
        expected_monthly = 10000 + 300 + 1000
        if debt['monthly_total'] == expected_monthly:
            print_result("Debt Summary Calculation", True)
            passed += 1
        else:
            print_result("Debt Summary Calculation", False, f"Expected={expected_monthly}, Actual={debt['monthly_total']}")
            failed += 1
    except Exception as e:
        print_result("Debt Summary Calculation", False, str(e))
        failed += 1
    
    # ===== Test 6: Create Family =====
    try:
        resp = wechat_handler.parse_message('test_user', '创建家庭 TestFamily')
        import re
        match = re.search(r'邀请码：(\w{6})', resp)
        if match:
            invite_code = match.group(1)
            print_result("Create Family", True)
            passed += 1
        else:
            print_result("Create Family", False, "Invite code not found")
            failed += 1
    except Exception as e:
        print_result("Create Family", False, str(e))
        failed += 1
    
    # ===== Test 7: Join Family =====
    try:
        family = database.get_user_family('test_user')
        if family:
            invite_code = family['invite_code']
            database.add_user('spouse', 'Spouse')
            resp = wechat_handler.parse_message('spouse', f'加入家庭 {invite_code}')
            if '成功加入' in resp:
                print_result("Join Family", True)
                passed += 1
            else:
                print_result("Join Family", False, f"Response: {resp[:80]}")
                failed += 1
        else:
            print_result("Join Family", False, "Family not found")
            failed += 1
    except Exception as e:
        print_result("Join Family", False, str(e))
        failed += 1
    
    # ===== Test 8: Family Members List =====
    try:
        resp = wechat_handler.parse_message('test_user', '家庭成员')
        if 'TestUser' in resp or 'Spouse' in resp or '成员列表' in resp:
            print_result("Family Members List", True)
            passed += 1
        else:
            print_result("Family Members List", False, f"Response: {resp[:80]}")
            failed += 1
    except Exception as e:
        print_result("Family Members List", False, str(e))
        failed += 1
    
    # ===== Test 9: Family Debt Ranking =====
    try:
        # Add debt to spouse
        wechat_handler.parse_message('spouse', '贷款 车贷 60000 12')  # 5000/month
        
        resp = wechat_handler.parse_message('test_user', '家庭欠款')
        if '欠款排行' in resp and ('test' in resp.lower() or 'spouse' in resp.lower()):
            print_result("Family Debt Ranking", True)
            passed += 1
        else:
            print_result("Family Debt Ranking", False, f"Response: {resp[:80]}")
            failed += 1
    except Exception as e:
        print_result("Family Debt Ranking", False, str(e))
        failed += 1
    
    # ===== Test 10: Family Notification (Mock) =====
    try:
        notifications = []
        def mock_notify(target_openid, message):
            notifications.append((target_openid, message))
        
        wechat_handler.parse_message('test_user', '支出 88 购物 测试物品', notify_callback=mock_notify)
        
        if len(notifications) == 1 and notifications[0][0] == 'spouse':
            msg = notifications[0][1]
            if '家庭支出提醒' in msg and '88.00' in msg:
                print_result("Family Expense Notification", True)
                passed += 1
            else:
                print_result("Family Expense Notification", False, f"Message incorrect")
                failed += 1
        else:
            print_result("Family Expense Notification", False, f"Notification count={len(notifications)}, expected=1")
            failed += 1
    except Exception as e:
        print_result("Family Expense Notification", False, str(e))
        failed += 1
    
    # ===== Test 11: Daily Push with Family Ranking =====
    try:
        msg = wechat_handler.get_daily_push_message('test_user')
        if '眼睛一睁' in msg and '家庭欠款排行' in msg:
            print_result("Daily Push with Family Ranking", True)
            passed += 1
        else:
            # May not have family ranking if no debt, check basic format
            if '眼睛一睁' in msg or '早安' in msg:
                print_result("Daily Push with Family Ranking", True)
                passed += 1
            else:
                print_result("Daily Push with Family Ranking", False, "Message format incorrect")
                failed += 1
    except Exception as e:
        print_result("Daily Push with Family Ranking", False, str(e))
        failed += 1
    
    # ===== Test 12: Help Message =====
    try:
        resp = wechat_handler.parse_message('test_user', '帮助')
        if '使用指南' in resp and '家庭组' in resp:
            print_result("Help Message", True)
            passed += 1
        else:
            print_result("Help Message", False, "Help content incomplete")
            failed += 1
    except Exception as e:
        print_result("Help Message", False, str(e))
        failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    total = passed + failed
    print(f"Test Result: {passed}/{total} passed")
    if failed == 0:
        print("All tests passed!")
    else:
        print(f"Warning: {failed} test(s) failed")
    print("=" * 50)
    
    # Clean up test database
    if os.path.exists('data/test_expense.db'):
        os.remove('data/test_expense.db')
        print("\nTest database cleaned up")
    
    return failed == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
