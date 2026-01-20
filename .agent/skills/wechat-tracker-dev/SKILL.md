---
name: WeChat Tracker Development
description: 开发微信记账小助手的指南，包含项目架构、指令解析、数据库操作和测试
---

# 💸 微信记账小助手 - 开发指南

## 项目概述

这是一个基于微信公众号的记账工具，通过发送微信消息即可完成记账操作。

### 核心理念
**焦虑驱动型记账** - 让用户每天感受到"负债压力"，激发搬砖动力。

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | Flask |
| 数据库 | SQLite |
| 消息处理 | WeChat Official Account API |
| 定时任务 | APScheduler |

## 项目结构

```
wechat-tracker/
├── app.py              # Flask 应用入口，处理微信消息验证
├── wechat_handler.py   # 消息解析和响应生成
├── database.py         # 数据库 CRUD 操作
├── scheduler.py        # 定时推送任务
├── config.py           # 配置文件（微信密钥等）
├── test_logic.py       # 单元测试
└── data/               # SQLite 数据库存储
```

## 用户指令参考

### 记账指令
| 指令格式 | 示例 | 说明 |
|----------|------|------|
| `支出 金额 分类 备注` | `支出 50 餐饮 午餐` | 记录日常支出 |
| `收入 金额 备注` | `收入 1000 工资` | 记录收入 |
| `贷款 名称 总额 月数` | `贷款 房贷 1000000 360` | 添加贷款 |
| `负债 名称 总额 期数` | `负债 信用卡分期 12000 12` | 添加分期负债 |
| `固定 名称 月额` | `固定 物业 200` | 添加固定月开支 |
| `删除 ID` | `删除 1` | 删除固定开支 |

### 查询指令
| 指令 | 说明 |
|------|------|
| `今日` | 查看今日收支统计 |
| `本月` | 查看本月统计 |
| `欠款` | 查看所有贷款/负债明细 |

### 家庭组指令
| 指令 | 说明 |
|------|------|
| `创建家庭 名称` | 创建家庭组，获取邀请码 |
| `加入家庭 邀请码` | 加入已有家庭 |
| `家庭成员` | 查看成员列表 |
| `家庭欠款` | 查看全家欠款排行 |
| `退出家庭` | 退出当前家庭 |

## 数据库模型

```sql
-- 用户表
users (
    openid TEXT PRIMARY KEY,
    nickname TEXT,
    created_at TIMESTAMP
)

-- 记账记录
expenses (
    id INTEGER PRIMARY KEY,
    openid TEXT,
    type TEXT,          -- 'income' | 'expense'
    amount REAL,
    category TEXT,
    description TEXT,
    created_at TIMESTAMP
)

-- 固定开支/贷款
recurring_expenses (
    id INTEGER PRIMARY KEY,
    openid TEXT,
    type TEXT,          -- 'loan' | 'debt' | 'fixed'
    name TEXT,
    total_amount REAL,
    total_months INTEGER,
    monthly_amount REAL,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN
)

-- 家庭组
families (
    id INTEGER PRIMARY KEY,
    name TEXT,
    invite_code TEXT UNIQUE,
    creator_openid TEXT,
    created_at TIMESTAMP
)

-- 家庭成员
family_members (
    id INTEGER PRIMARY KEY,
    family_id INTEGER,
    openid TEXT,
    nickname TEXT,
    role TEXT,          -- 'creator' | 'member'
    joined_at TIMESTAMP
)
```

## 开发指南

### 添加新指令

1. 在 `wechat_handler.py` 的 `parse_message()` 函数中添加正则匹配
2. 在 `database.py` 中添加相应的数据库操作函数
3. 在 `test_logic.py` 中添加测试

### 正则匹配示例

```python
# 匹配 "支出 50 餐饮 午餐"
expense_match = re.match(r'^支出\s+(\d+(?:\.\d+)?)\s+(\S+)(?:\s+(.*))?$', content)
if expense_match:
    amount = float(expense_match.group(1))
    category = expense_match.group(2)
    description = expense_match.group(3)
```

## 测试

```bash
# 运行所有测试
python -m pytest test_logic.py -v

# 运行特定测试
python -m pytest test_logic.py::test_parse_expense -v
```

## 本地调试

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py

# 服务将在 http://localhost:5000 运行
```
