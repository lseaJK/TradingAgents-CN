#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mainB.py - 飞书表格集成测试脚本
简化版本，用于测试飞书表格的读取、文档创建和回填功能
"""

import os
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 加载.env配置
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# 飞书表格相关配置
FEISHU_APP_ID = os.getenv('FEISHU_APP_ID')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET')
FEISHU_USER_ACCESS_TOKEN = os.getenv('FEISHU_USER_ACCESS_TOKEN')
FEISHU_ACCESS_TOKEN = os.getenv('FEISHU_ACCESS_TOKEN')  # 新增：从.env读取现有token
FEISHU_REFRESH_TOKEN = os.getenv('FEISHU_REFRESH_TOKEN')
# 从.env获取TradingAgents任务表配置
FEISHU_APP_TOKEN = os.getenv('TABLE_APP_TOKEN', "SCrXbf2WJaPLV5sqBTOcxzzknWb")  # 飞书表格 app_token
FEISHU_TABLE_ID = os.getenv('TABLE_ID', "tblmJhLZBJAaAAPf")  # 飞书表格 table_id

# 表格字段配置（根据实际字段信息更新）
FEISHU_TABLE_FIELDS = {
    'stock_code': {'name': '股票代码', 'id': 'fld2C6SJHN', 'type': 1},
    'stock_name': {'name': '股票名称', 'id': 'fldY9bygVX', 'type': 1}, 
    'request_date': {'name': '请求日期', 'id': 'fldYbistOj', 'type': 5},
    'status': {'name': '当前状态', 'id': 'fldaesRzlV', 'type': 1},
    'reply_link': {'name': '回复链接', 'id': 'fldZ346X93', 'type': 15}
}

def get_feishu_access_token():
    """
    获取飞书AccessToken（应用令牌）
    """
    print("🔄 获取应用访问令牌...")
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/"
    resp = requests.post(url, json={
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    })
    data = resp.json()
    token = data.get('app_access_token')
    if not token:
        print(f"❌ 飞书 app_access_token 获取失败: {data}")
        return None
    
    print(f"✅ 获取应用访问令牌成功: {token[:10]}...")
    return token

def get_feishu_access_token_for_table():
    """
    专门为表格操作获取访问令牌（优先级顺序测试）
    """
    # 尝试多种令牌类型，按优先级排序
    token_options = [
        ("现有FEISHU_ACCESS_TOKEN", FEISHU_ACCESS_TOKEN),
        ("用户访问令牌", FEISHU_USER_ACCESS_TOKEN),
        ("应用访问令牌", None)  # 最后获取应用令牌
    ]
    
    for token_type, token in token_options:
        if token:
            print(f"✅ 使用{token_type}进行表格操作: {token[:10]}...")
            return token
    
    # 如果都没有，获取应用访问令牌
    print("🔄 获取应用访问令牌进行表格操作...")
    return get_feishu_access_token()

def fetch_pending_tasks():
    """
    获取飞书表格中待处理的任务（股票代码存在但状态为空）
    """
    print("\n📋 获取飞书表格数据...")
    access_token = get_feishu_access_token()
    if not access_token:
        print("❌ 无法获取飞书访问令牌")
        return []
        
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    
    try:
        resp = requests.get(url, headers=headers)
        data = resp.json()
        
        print(f"📊 API响应状态: {resp.status_code}")
        print(f"📊 API响应数据: {data}")
        
        if data.get('code') != 0:
            print(f"❌ 获取飞书表格数据失败: {data}")
            return []
            
        tasks = []
        items = data.get('data', {}).get('items', [])
        print(f"📊 表格总行数: {len(items)}")
        
        for i, item in enumerate(items, 1):
            fields = item.get('fields', {})
            record_id = item.get('record_id')
            
            print(f"\n📝 行 {i}: record_id={record_id}")
            print(f"   字段数据: {fields}")
            
            # 使用字段名获取数据
            stock_code = fields.get(FEISHU_TABLE_FIELDS['stock_code']['name'])
            stock_name = fields.get(FEISHU_TABLE_FIELDS['stock_name']['name'])
            status = fields.get(FEISHU_TABLE_FIELDS['status']['name'])
            
            print(f"   股票代码: {stock_code}")
            print(f"   股票名称: {stock_name}")
            print(f"   当前状态: {status}")
            
            # 筛选：有股票代码且状态为空的行
            if stock_code and not status:
                task = {
                    'record_id': record_id, 
                    'stock_code': stock_code,
                    'stock_name': stock_name or ''
                }
                tasks.append(task)
                print(f"   ✅ 发现待处理任务: {stock_code} ({stock_name})")
            else:
                print(f"   ⏭️ 跳过（无股票代码或已有状态）")
                
        print(f"\n📋 共发现 {len(tasks)} 个待处理任务")
        return tasks
        
    except Exception as e:
        print(f"❌ 获取飞书表格数据异常: {e}")
        return []

def create_test_feishu_doc(title, content):
    """
    创建测试飞书文档
    """
    print(f"\n📄 创建飞书文档: {title}")
    access_token = get_feishu_access_token()
    if not access_token:
        print("❌ 无法获取飞书访问令牌，无法创建文档")
        return None
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        # 创建文档
        create_url = "https://open.feishu.cn/open-apis/docx/v1/documents"
        resp = requests.post(create_url, headers=headers, json={
            "title": title
        })
        doc_data = resp.json()
        
        print(f"📄 文档创建响应: {doc_data}")
        
        if doc_data.get('code') != 0:
            print(f"❌ 飞书文档创建失败: {doc_data}")
            return None
            
        doc_id = doc_data.get('data', {}).get('document', {}).get('document_id')
        if not doc_id:
            print(f"❌ 飞书文档创建失败，未获取到document_id: {doc_data}")
            return None
            
        print(f"✅ 文档创建成功，ID: {doc_id}")
        
        # 暂时跳过内容写入，先验证核心流程
        print("📝 跳过内容写入，直接返回文档ID...")
        print(f"✅ 飞书文档创建成功: {title} (ID: {doc_id})")
        return doc_id
            
    except Exception as e:
        print(f"❌ 创建飞书文档异常: {e}")
        return None

def diagnose_feishu_permissions():
    """
    诊断飞书表格权限问题
    """
    print("\n🔍 开始权限诊断...")
    access_token = get_feishu_access_token_for_table()
    if not access_token:
        print("❌ 无法获取任何访问令牌")
        return
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # 1. 测试表格信息获取
    print("🔍 步骤1: 测试表格信息获取权限...")
    table_info_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}"
    try:
        resp = requests.get(table_info_url, headers=headers)
        result = resp.json()
        print(f"   表格信息获取: HTTP {resp.status_code}, {result.get('code', 'N/A')}")
        if result.get('code') == 0:
            print("   ✅ 有表格读取权限")
        else:
            print(f"   ❌ 表格读取失败: {result}")
    except Exception as e:
        print(f"   ❌ 表格信息获取异常: {e}")
    
    # 2. 测试记录列表获取
    print("🔍 步骤2: 测试记录列表获取权限...")
    records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    try:
        resp = requests.get(records_url, headers=headers)
        result = resp.json()
        print(f"   记录列表获取: HTTP {resp.status_code}, {result.get('code', 'N/A')}")
        if result.get('code') == 0:
            print("   ✅ 有记录读取权限")
        else:
            print(f"   ❌ 记录读取失败: {result}")
    except Exception as e:
        print(f"   ❌ 记录列表获取异常: {e}")
    
    # 3. 测试字段信息获取
    print("🔍 步骤3: 测试字段信息获取权限...")
    fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/fields"
    try:
        resp = requests.get(fields_url, headers=headers)
        result = resp.json()
        print(f"   字段信息获取: HTTP {resp.status_code}, {result.get('code', 'N/A')}")
        if result.get('code') == 0:
            print("   ✅ 有字段读取权限")
            fields = result.get('data', {}).get('items', [])
            print(f"   📋 发现 {len(fields)} 个字段")
            for field in fields[:5]:  # 只显示前5个字段
                print(f"      - {field.get('field_name')}: {field.get('type')}")
        else:
            print(f"   ❌ 字段读取失败: {result}")
    except Exception as e:
        print(f"   ❌ 字段信息获取异常: {e}")
    
    # 4. 测试应用信息获取
    print("🔍 步骤4: 测试应用信息获取权限...")
    app_info_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}"
    try:
        resp = requests.get(app_info_url, headers=headers)
        result = resp.json()
        print(f"   应用信息获取: HTTP {resp.status_code}, {result.get('code', 'N/A')}")
        if result.get('code') == 0:
            print("   ✅ 有应用读取权限")
            app_info = result.get('data', {}).get('app', {})
            print(f"   📋 应用名称: {app_info.get('name', 'N/A')}")
        else:
            print(f"   ❌ 应用读取失败: {result}")
    except Exception as e:
        print(f"   ❌ 应用信息获取异常: {e}")
    
    print("🔍 权限诊断完成")
    """
    测试表格写入权限 - 尝试创建一条新记录
    """
    print("\n🧪 测试表格写入权限...")
    access_token = get_feishu_access_token_for_table()
    if not access_token:
        print("❌ 无法获取访问令牌")
        return False
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    
    # 尝试创建一条测试记录
    test_data = {
        "fields": {
            FEISHU_TABLE_FIELDS['stock_code']['name']: "TEST001",
            FEISHU_TABLE_FIELDS['status']['name']: "权限测试"
        }
    }
    
    try:
        resp = requests.post(url, headers=headers, json=test_data)
        result = resp.json()
        
        print(f"🧪 写入测试响应: {result}")
        
        if result.get('code') == 0:
            print("✅ 表格写入权限正常")
            # 删除测试记录
            test_record_id = result.get('data', {}).get('record', {}).get('record_id')
            if test_record_id:
                delete_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/{test_record_id}"
                requests.delete(delete_url, headers=headers)
                print("🧹 已清理测试记录")
            return True
        else:
            print(f"❌ 表格写入权限异常: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 测试表格写入权限异常: {e}")
        return False

def update_feishu_table(record_id, request_date, status, reply_link):
    """
    更新飞书表格记录（严格按照官方API文档）
    """
    print(f"\n🔄 更新飞书表格: record_id={record_id}")
    access_token = get_feishu_access_token_for_table()
    if not access_token:
        print("❌ 无法获取飞书访问令牌，无法更新表格")
        return None
        
    # 严格按照官方文档的请求头格式
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # 官方文档标准URL格式
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/{record_id}"
    
    # 构建更新数据 - 严格按照官方文档格式
    update_data = {
        "fields": {
            FEISHU_TABLE_FIELDS['request_date']['name']: request_date,
            FEISHU_TABLE_FIELDS['status']['name']: status,
            FEISHU_TABLE_FIELDS['reply_link']['name']: reply_link
        }
    }
    
    print(f"🔄 请求URL: {url}")
    print(f"🔄 请求头: {headers}")
    print(f"🔄 更新数据: {update_data}")
    
    try:
        # 使用PUT方法 - 官方文档指定的方法
        resp = requests.put(url, headers=headers, json=update_data)
        result = resp.json()
        
        print(f"📊 HTTP状态码: {resp.status_code}")
        print(f"� API响应: {result}")
        
        if result.get('code') == 0:
            print(f"✅ 飞书表格更新成功: record_id={record_id}, status={status}")
            return result
        else:
            error_code = result.get('code')
            error_msg = result.get('msg', '未知错误')
            print(f"❌ 飞书表格更新失败")
            print(f"   错误代码: {error_code}")
            print(f"   错误信息: {error_msg}")
            
            # 检查是否是权限问题
            if error_code == 1254302:
                print("💡 权限提示: 表格开启了高级权限，需要在高级权限设置中添加包含应用的群组并给予读写权限")
            elif str(error_code).startswith('91'):
                print("💡 权限提示: 这是飞书权限相关错误，请检查应用权限配置")
            
            return None
            
    except Exception as e:
        print(f"❌ 更新飞书表格异常: {e}")
        return None

def generate_test_markdown(stock_code, stock_name=""):
    """
    生成测试用的Markdown报告
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    title = f"{stock_code} 测试分析报告"
    if stock_name:
        title = f"{stock_code} ({stock_name}) 测试分析报告"
    
    md = f"""# {title}

**生成时间**: {timestamp}

## 🧪 测试信息

这是一个测试文档，用于验证飞书表格集成功能。

- **股票代码**: {stock_code}
- **股票名称**: {stock_name or '未提供'}
- **测试时间**: {timestamp}

## 📊 模拟分析结果

### 技术分析
- 当前价格: ¥XX.XX
- 建议操作: 测试用途
- 风险等级: 低

### 基本面分析
这是一个测试分析，用于验证文档创建和回填功能。

## ⚠️ 测试声明

**这仅是技术测试文档，不构成任何投资建议。**

---
*由TradingAgents测试脚本生成*
"""
    return md

def main():
    """
    主测试流程
    """
    print("🚀 开始飞书表格集成测试")
    print("=" * 60)
    
    # 检查环境变量
    print("\n🔍 检查环境变量配置:")
    env_vars = ['FEISHU_APP_ID', 'FEISHU_APP_SECRET', 'FEISHU_USER_ACCESS_TOKEN', 'FEISHU_REFRESH_TOKEN']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 10}...{value[-4:] if len(value) > 4 else '****'}")
        else:
            print(f"❌ {var}: 未设置")
    
    print(f"\n📋 飞书表格信息:")
    print(f"   APP Token: {FEISHU_APP_TOKEN}")
    print(f"   Table ID: {FEISHU_TABLE_ID}")
    print(f"   表格链接: https://tcnab3awhbc1.feishu.cn/base/{FEISHU_APP_TOKEN}")
    
    # 运行权限诊断
    diagnose_feishu_permissions()
    
    # 1. 获取待处理任务
    tasks = fetch_pending_tasks()
    if not tasks:
        print("\n⚠️ 没有发现待处理的任务，测试结束")
        return
    
    print(f"\n🎯 开始处理 {len(tasks)} 个测试任务")
    
    # 2. 处理每个任务
    for i, task in enumerate(tasks, 1):
        record_id = task['record_id']
        stock_code = task['stock_code']
        stock_name = task['stock_name']
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n{'=' * 40}")
        print(f"🔄 处理任务 {i}/{len(tasks)}: {stock_code} ({stock_name})")
        print(f"{'=' * 40}")
        
        try:
            # 2.1 更新状态为"测试中"
            print("📝 更新状态为'测试中'...")
            update_feishu_table(record_id, today_str, "测试中", "")
            
            # 2.2 生成测试报告
            print("📄 生成测试报告...")
            md_content = generate_test_markdown(stock_code, stock_name)
            
            # 2.3 创建飞书文档
            feishu_title = f"[测试]{stock_code}_{stock_name}_{today_str}" if stock_name else f"[测试]{stock_code}_{today_str}"
            doc_id = create_test_feishu_doc(feishu_title, md_content)
            
            # 2.4 回填结果
            if doc_id:
                doc_url = f"https://feishu.cn/docx/{doc_id}"
                print("✅ 更新状态为'测试完成'...")
                update_feishu_table(record_id, today_str, "测试完成", doc_url)
                print(f"🎉 {stock_code} 测试完成!")
                print(f"📄 文档链接: {doc_url}")
            else:
                print("❌ 更新状态为'测试失败'...")
                update_feishu_table(record_id, today_str, "测试失败", "文档创建失败")
                print(f"💥 {stock_code} 测试失败")
                
        except Exception as e:
            print(f"💥 任务处理异常: {e}")
            update_feishu_table(record_id, today_str, "测试异常", str(e))
    
    print(f"\n{'=' * 60}")
    print("🏁 飞书表格集成测试完成!")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
