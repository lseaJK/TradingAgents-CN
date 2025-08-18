# 飞书表格数据获取完整流程使用指南

## 📋 功能概述

本脚本实现了飞书 TradingAgents任务表 的自动数据获取，包括：
- 自动token刷新机制
- 表格基本信息查询
- 字段结构获取
- 记录数据提取
- 结果保存为JSON文件

## 🚀 快速开始

### 1. 环境配置

确保 `.env` 文件中包含以下配置：
```env
FEISHU_APP_ID=cli_a82994526a3b900b
FEISHU_APP_SECRET=你的app_secret
```

### 2. 权限配置

⚠️ **重要：需要为应用开通以下权限之一**

访问以下链接申请权限：
```
https://open.feishu.cn/app/cli_a82994526a3b900b/auth?q=bitable:app:readonly,bitable:app,base:table:read&op_from=openapi&token_type=tenant
```

需要的权限（任选其一）：
- `bitable:app:readonly` - 多维表只读权限（推荐）
- `bitable:app` - 多维表完整权限
- `base:table:read` - 表格读取权限

### 3. 首次授权（获取用户令牌）

如果需要用户身份访问（推荐），请：

1. 访问授权链接：
```
https://open.feishu.cn/open-apis/authen/v1/index?app_id=cli_a82994526a3b900b&redirect_uri=https://open.feishu.cn/api-explorer/loading&state=trading_agents&scope=openid offline_access bitable:app:readonly
```

2. 完成授权后，从回调URL中提取授权码（code参数）

3. 使用授权码运行脚本：
```python
# 在脚本中
manager = FeishuTableManager()
result = manager.run_complete_flow(authorization_code="你的授权码")
```

## 📊 使用方法

### 方法1：直接运行（自动处理）
```bash
python feishu_table_manager.py
```

### 方法2：编程调用
```python
from feishu_table_manager import FeishuTableManager

# 创建管理器
manager = FeishuTableManager()

# 执行完整流程
result = manager.run_complete_flow()

if result:
    print(f"获取到 {len(result['records'])} 条记录")
    for record in result['records']:
        print(f"ID: {record['record_id']}, 数据: {record['fields']}")
```

### 方法3：分步执行
```python
manager = FeishuTableManager()

# 1. 刷新token
if manager.refresh_access_token():
    # 2. 获取表格信息
    tables = manager.get_table_info()
    
    # 3. 获取字段信息
    fields = manager.get_table_fields()
    
    # 4. 获取记录数据
    records = manager.get_table_records()
```

## 🔧 故障排除

### 问题1：权限不足 (99991672)
**解决方法：**
1. 访问权限申请链接开通必要权限
2. 等待权限生效（通常几分钟）
3. 重新运行脚本

### 问题2：Refresh Token失效 (20026)
**解决方法：**
1. 重新访问授权链接获取新的授权码
2. 运行 `manager.get_initial_tokens(new_code)`
3. 或使用app_access_token模式（需要权限）

### 问题3：网络连接超时
**解决方法：**
1. 检查网络连接
2. 确认可以访问 open.feishu.cn
3. 如有代理，确保Python可以使用

### 问题4：表格不存在 (NOTEXIST)
**解决方法：**
1. 确认表格URL和app_token正确
2. 确认有表格访问权限
3. 检查表格是否被删除或移动

## 📁 输出文件

脚本成功运行后会生成：
```
trading_agents_table_data_20250818_224831.json
```

文件包含：
- 记录总数
- 每条记录的ID和字段数据
- 是否还有更多数据的标识

## 🔄 自动化运行

### Windows 计划任务
1. 创建批处理文件 `run_feishu_table.bat`：
```batch
@echo off
cd /d "E:\my_agent_learning\TradingAgents\TradingAgents-CN-main"
python feishu_table_manager.py
pause
```

2. 在Windows计划任务中设置定时运行

### Python定时任务
```python
import schedule
import time

def job():
    manager = FeishuTableManager()
    manager.run_complete_flow()

# 每天上午9点运行
schedule.every().day.at("09:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## 📞 技术支持

如遇到问题，请检查：
1. 网络连接是否正常
2. 环境变量是否正确配置
3. 应用权限是否已开通
4. Token是否在有效期内

更多帮助请参考飞书开放平台文档：
https://open.feishu.cn/document/

---

**最后更新：2025-08-18**
**版本：v1.0**
