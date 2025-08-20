#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mainB_with_user_token.py - 使用用户令牌的飞书表格集成测试脚本
结合FeiShu文件夹中的用户授权功能，解决表格写入权限问题
"""

import os
import sys
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 添加FeiShu文件夹到路径，以便导入相关模块
sys.path.append(str(Path(__file__).parent.parent / 'FeiShu'))

try:
    from refresh_feishu_token import refresh_user_access_token, get_app_access_token
except ImportError:
    print("❌ 无法导入FeiShu模块，请检查FeiShu文件夹")
    sys.exit(1)

# 加载.env配置
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# 飞书表格相关配置
FEISHU_APP_ID = os.getenv('FEISHU_APP_ID')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET')
FEISHU_USER_ACCESS_TOKEN = os.getenv('FEISHU_USER_ACCESS_TOKEN')
FEISHU_ACCESS_TOKEN = os.getenv('FEISHU_ACCESS_TOKEN')
FEISHU_REFRESH_TOKEN = os.getenv('FEISHU_REFRESH_TOKEN')
# 从.env获取TradingAgents任务表配置
FEISHU_APP_TOKEN = os.getenv('TABLE_APP_TOKEN', "SCrXbf2WJaPLV5sqBTOcxzzknWb")
FEISHU_TABLE_ID = os.getenv('TABLE_ID', "tblmJhLZBJAaAAPf")

# 表格字段配置
FEISHU_TABLE_FIELDS = {
    'stock_code': {'name': '股票代码', 'id': 'fld2C6SJHN', 'type': 1},
    'stock_name': {'name': '股票名称', 'id': 'fldY9bygVX', 'type': 1}, 
    'request_date': {'name': '请求日期', 'id': 'fldYbistOj', 'type': 5},
    'status': {'name': '当前状态', 'id': 'fldaesRzlV', 'type': 1},
    'reply_link': {'name': '回复链接', 'id': 'fldZ346X93', 'type': 15}
}

def get_best_access_token():
    """
    获取最佳的访问令牌 - 优先使用用户令牌来绕过应用权限限制
    """
    print("🔍 寻找最佳访问令牌...")
    
    # 1. 尝试刷新用户访问令牌
    if FEISHU_REFRESH_TOKEN:
        print("🔄 尝试刷新用户访问令牌...")
        try:
            user_token, new_refresh_token = refresh_user_access_token(
                FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_REFRESH_TOKEN
            )
            if user_token:
                print(f"✅ 成功获取用户访问令牌: {user_token[:10]}...")
                return user_token, "user_access_token"
        except Exception as e:
            print(f"⚠️  刷新用户令牌失败: {e}")
    
    # 2. 检查现有的用户访问令牌
    if FEISHU_USER_ACCESS_TOKEN:
        print(f"🔍 检查现有用户访问令牌: {FEISHU_USER_ACCESS_TOKEN[:10]}...")
        return FEISHU_USER_ACCESS_TOKEN, "user_access_token"
    
    # 3. 检查.env中的FEISHU_ACCESS_TOKEN
    if FEISHU_ACCESS_TOKEN:
        print(f"🔍 检查现有FEISHU_ACCESS_TOKEN: {FEISHU_ACCESS_TOKEN[:10]}...")
        return FEISHU_ACCESS_TOKEN, "feishu_access_token"
    
    # 4. 最后使用应用访问令牌（可能没有写入权限）
    print("🔧 获取应用访问令牌作为备选...")
    try:
        app_token = get_app_access_token(FEISHU_APP_ID, FEISHU_APP_SECRET)
        if app_token:
            print(f"✅ 获取应用访问令牌: {app_token[:10]}...")
            print("⚠️  注意：应用令牌可能没有表格写入权限")
            return app_token, "app_access_token"
    except Exception as e:
        print(f"❌ 获取应用令牌失败: {e}")
    
    print("❌ 无法获取任何有效的访问令牌")
    return None, None

def fetch_pending_tasks():
    """
    获取飞书表格中待处理的任务（股票代码存在但状态为空）
    """
    print("\n📋 获取飞书表格数据...")
    access_token, token_type = get_best_access_token()
    if not access_token:
        print("❌ 无法获取飞书访问令牌")
        return []
        
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    
    try:
        resp = requests.get(url, headers=headers)
        data = resp.json()
        
        print(f"📊 API响应状态: {resp.status_code}")
        print(f"📊 使用令牌类型: {token_type}")
        
        if data.get('code') != 0:
            print(f"❌ 获取飞书表格数据失败: {data}")
            return []
            
        tasks = []
        items = data.get('data', {}).get('items', [])
        print(f"📊 表格总行数: {len(items)}")
        
        for i, item in enumerate(items, 1):
            fields = item.get('fields', {})
            record_id = item.get('record_id')
            
            stock_code = fields.get(FEISHU_TABLE_FIELDS['stock_code']['name'])
            stock_name = fields.get(FEISHU_TABLE_FIELDS['stock_name']['name'])
            status = fields.get(FEISHU_TABLE_FIELDS['status']['name'])
            
            print(f"\n📝 行 {i}: record_id={record_id}")
            print(f"   股票代码: {stock_code}, 状态: {status}")
            
            # 筛选：有股票代码且状态为空的行
            if stock_code and not status:
                task = {
                    'record_id': record_id, 
                    'stock_code': stock_code,
                    'stock_name': stock_name or ''
                }
                tasks.append(task)
                print(f"   ✅ 发现待处理任务")
                
        print(f"\n📋 共发现 {len(tasks)} 个待处理任务")
        return tasks
        
    except Exception as e:
        print(f"❌ 获取飞书表格数据异常: {e}")
        return []

def update_feishu_table(record_id, request_date, status, reply_link):
    """
    更新飞书表格记录 - 使用用户令牌来绕过权限限制
    """
    print(f"\n🔄 更新飞书表格: record_id={record_id}")
    access_token, token_type = get_best_access_token()
    if not access_token:
        print("❌ 无法获取飞书访问令牌，无法更新表格")
        return None
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/{record_id}"
    
    update_data = {
        "fields": {
            FEISHU_TABLE_FIELDS['request_date']['name']: request_date,
            FEISHU_TABLE_FIELDS['status']['name']: status,
            FEISHU_TABLE_FIELDS['reply_link']['name']: reply_link
        }
    }
    
    print(f"🔄 使用令牌类型: {token_type}")
    print(f"🔄 更新数据: {update_data}")
    
    try:
        resp = requests.put(url, headers=headers, json=update_data)
        result = resp.json()
        
        print(f"📊 HTTP状态码: {resp.status_code}")
        print(f"📊 API响应: {result}")
        
        if result.get('code') == 0:
            print(f"✅ 飞书表格更新成功!")
            return result
        else:
            error_code = result.get('code')
            error_msg = result.get('msg', '未知错误')
            print(f"❌ 飞书表格更新失败")
            print(f"   错误代码: {error_code}")
            print(f"   错误信息: {error_msg}")
            
            # 根据错误代码提供具体建议
            if error_code == 91403:
                print("💡 建议: 需要用户授权，请运行 python FeiShu/get_user_authorization.py 获取授权链接")
            elif error_code == 99991663:
                print("💡 建议: 访问令牌无效，需要重新获取用户授权")
            
            return None
            
    except Exception as e:
        print(f"❌ 更新飞书表格异常: {e}")
        return None

def create_test_feishu_doc(title, content):
    """
    创建测试飞书文档
    """
    print(f"\n📄 创建飞书文档: {title}")
    access_token, token_type = get_best_access_token()
    if not access_token:
        print("❌ 无法获取飞书访问令牌，无法创建文档")
        return None
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        create_url = "https://open.feishu.cn/open-apis/docx/v1/documents"
        resp = requests.post(create_url, headers=headers, json={
            "title": title
        })
        doc_data = resp.json()
        
        print(f"📄 使用令牌类型: {token_type}")
        print(f"📄 文档创建响应: {doc_data}")
        
        if doc_data.get('code') != 0:
            print(f"❌ 飞书文档创建失败: {doc_data}")
            return None
            
        doc_id = doc_data.get('data', {}).get('document', {}).get('document_id')
        if not doc_id:
            print(f"❌ 飞书文档创建失败，未获取到document_id")
            return None
            
        print(f"✅ 文档创建成功，ID: {doc_id}")
        return doc_id
            
    except Exception as e:
        print(f"❌ 创建飞书文档异常: {e}")
        return None

def generate_test_markdown(stock_code, stock_name=""):
    """
    生成测试用的Markdown报告
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    title = f"{stock_code} 用户令牌测试报告"
    if stock_name:
        title = f"{stock_code} ({stock_name}) 用户令牌测试报告"
    
    md = f"""# {title}

**生成时间**: {timestamp}

## 🧪 测试信息

这是使用用户访问令牌进行的表格写入测试。

- **股票代码**: {stock_code}
- **股票名称**: {stock_name or '未提供'}
- **测试时间**: {timestamp}
- **权限类型**: 用户访问令牌

## 📊 权限测试结果

### 表格读取权限 ✅
- 成功读取表格数据
- 正确识别待处理任务

### 表格写入权限 🧪
- 正在测试表格记录更新功能
- 使用用户令牌绕过应用权限限制

### 文档创建权限 ✅
- 成功创建飞书文档

## ⚠️ 测试声明

**这是权限测试文档，验证用户令牌的表格写入功能。**

---
*由TradingAgents用户令牌测试脚本生成*
"""
    return md

def main():
    """
    主测试流程 - 使用用户令牌版本
    """
    print("🚀 飞书表格集成测试 (用户令牌版本)")
    print("=" * 70)
    
    # 检查环境变量
    print("\n🔍 检查环境变量配置:")
    env_vars = [
        ('FEISHU_APP_ID', FEISHU_APP_ID),
        ('FEISHU_APP_SECRET', FEISHU_APP_SECRET), 
        ('FEISHU_REFRESH_TOKEN', FEISHU_REFRESH_TOKEN),
        ('FEISHU_USER_ACCESS_TOKEN', FEISHU_USER_ACCESS_TOKEN),
        ('FEISHU_ACCESS_TOKEN', FEISHU_ACCESS_TOKEN)
    ]
    
    for var_name, var_value in env_vars:
        if var_value:
            print(f"✅ {var_name}: {'*' * 10}...{var_value[-4:] if len(var_value) > 4 else '****'}")
        else:
            print(f"❌ {var_name}: 未设置")
    
    print(f"\n📋 飞书表格信息:")
    print(f"   APP Token: {FEISHU_APP_TOKEN}")
    print(f"   Table ID: {FEISHU_TABLE_ID}")
    
    # 检查是否有用户令牌
    if not any([FEISHU_REFRESH_TOKEN, FEISHU_USER_ACCESS_TOKEN, FEISHU_ACCESS_TOKEN]):
        print("\n⚠️  警告：没有检测到用户访问令牌相关配置")
        print("💡 建议：运行以下命令获取用户授权")
        print("   python FeiShu/get_user_authorization.py")
        print("   然后按照指引完成用户授权流程")
        print()
    
    # 1. 获取待处理任务
    tasks = fetch_pending_tasks()
    if not tasks:
        print("\n⚠️ 没有发现待处理的任务")
        return
    
    print(f"\n🎯 开始处理 {len(tasks)} 个测试任务")
    
    # 2. 处理每个任务
    for i, task in enumerate(tasks, 1):
        record_id = task['record_id']
        stock_code = task['stock_code']
        stock_name = task['stock_name']
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n{'=' * 50}")
        print(f"🔄 处理任务 {i}/{len(tasks)}: {stock_code}")
        print(f"{'=' * 50}")
        
        try:
            # 2.1 更新状态为"用户令牌测试中"
            print("📝 更新状态为'用户令牌测试中'...")
            update_result = update_feishu_table(record_id, today_str, "用户令牌测试中", "")
            
            if not update_result:
                print("❌ 表格更新失败，跳过后续步骤")
                continue
            
            # 2.2 生成测试报告
            print("📄 生成测试报告...")
            md_content = generate_test_markdown(stock_code, stock_name)
            
            # 2.3 创建飞书文档
            feishu_title = f"[用户令牌测试]{stock_code}_{today_str}"
            doc_id = create_test_feishu_doc(feishu_title, md_content)
            
            # 2.4 回填结果
            if doc_id:
                doc_url = f"https://feishu.cn/docx/{doc_id}"
                print("✅ 更新状态为'用户令牌测试完成'...")
                update_feishu_table(record_id, today_str, "用户令牌测试完成", doc_url)
                print(f"🎉 {stock_code} 用户令牌测试完成!")
                print(f"📄 文档链接: {doc_url}")
            else:
                print("❌ 更新状态为'文档创建失败'...")
                update_feishu_table(record_id, today_str, "文档创建失败", "")
                
        except Exception as e:
            print(f"💥 任务处理异常: {e}")
            update_feishu_table(record_id, today_str, "测试异常", str(e))
    
    print(f"\n{'=' * 70}")
    print("🏁 飞书表格集成测试 (用户令牌版本) 完成!")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
