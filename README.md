# 💸 微信记账小助手

> **核心理念：躺着都在收费，站着更得拼命！**

基于微信公众号的焦虑驱动型记账工具，让你每天睁眼就感受到"负债压力"，从而激发搬砖动力。

## ✨ 特性

- 📱 **零成本使用** - 微信原生交互，无需下载APP
- 💬 **极简操作** - 一句话完成记账
- 👨‍👩‍👧‍👦 **家庭共享** - 共享账本，互相"鞭策"
- 📊 **可视化** - 预算进度、分类统计一目了然
- ⏰ **每日推送** - 早8点提醒"眼睛一睁，欠款xxx元"

---

## 📖 指令大全

### 💰 日常记账
```
支出 50 餐饮 午餐
收入 1000 工资
```

### 🏠 贷款/负债/固定开支
```
贷款 房贷 1000000 360    # 总额 + 期数
负债 信用卡分期 12000 12
固定 物业 200             # 月费
删除 1                    # 仅家庭创建人
```

### 📊 查询统计
```
今日          # 今日收支
本月          # 本月统计
欠款          # 固定开支明细（家庭共享）
历史          # 最近7天记录
历史 30       # 最近30天记录
统计          # 分类统计（30天）
统计 7        # 分类统计（7天）
```

### 💰 预算管理
```
预算 5000     # 设置月预算
预算          # 查看预算使用情况
```

### 👨‍👩‍👧‍👦 家庭组
```
创建家庭 我的家
加入家庭 ABC123
家庭            # 查看成员
家庭欠款        # 欠款排行
退出家庭
昵称 老公       # 修改显示名称
```

---

## 🏗️ 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Flask + Gunicorn |
| 数据库 | SQLite |
| 定时任务 | APScheduler |
| 消息接口 | WeChat Official Account API |

---

## 📁 项目结构

```
wechat-tracker/
├── app.py              # Flask 应用入口
├── wechat_handler.py   # 消息解析和响应
├── database.py         # 数据库操作
├── scheduler.py        # 定时推送
├── config.py           # 配置文件
├── deploy.sh           # 部署脚本
├── data/               # SQLite 数据库
└── requirements.txt
```

---

## 🚀 快速部署

### 1. 配置微信凭证

编辑 `config.py`：
```python
WECHAT_APP_ID = 'wxxxxxxxxxxx'
WECHAT_APP_SECRET = 'xxxxxxxxxxxxxxxxx'
WECHAT_TOKEN = 'your_custom_token'
```

### 2. 运行部署脚本

```bash
cd /usr/local/wechat-tracker
bash deploy.sh
```

选择选项 1（全新部署）或选项 2（更新代码）

### 3. 配置微信测试号

访问 https://mp.weixin.qq.com/debug/cgi-bin/sandbox

填写接口配置：
- **URL**: `http://YOUR_SERVER_IP:5000/wechat`
- **Token**: 与 config.py 中相同

---

## 📋 常用命令

| 操作 | 命令 |
|------|------|
| 查看状态 | `systemctl status wechat-tracker` |
| 重启服务 | `systemctl restart wechat-tracker` |
| 查看日志 | `journalctl -u wechat-tracker -f` |
| 备份数据 | `bash deploy.sh` → 选项 7 |

---

## ⚠️ 注意事项

- **删除权限**：只有家庭创建人可删除固定开支/贷款
- **数据修改**：记录只能删除，不支持修改
- **数据导出**：暂不支持

---

## 📄 License

MIT
