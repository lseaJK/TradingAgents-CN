#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mainB_fixed.py - 修复版飞书表格集成测试脚本
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

def get_feishu_access_token():
    """获取飞书应用访问令牌"""
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

def test_table_permissions():
    """测试表格权限"""
    print("\n🧪 测试表格权限...")
    access_token = get_feishu_access_token()
    if not access_token:
        return False
        
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 1. 测试读取权限
    print("📖 测试读取权限...")
    read_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    try:
        resp = requests.get(read_url, headers=headers)
        read_result = resp.json()
        if read_result.get('code') == 0:
            print("✅ 读取权限正常")
        else:
            print(f"❌ 读取权限异常: {read_result}")
            return False
    except Exception as e:
        print(f"❌ 读取权限测试异常: {e}")
        return False
    
    # 2. 测试写入权限 - 创建新记录
    print("✏️ 测试写入权限（创建记录）...")
    create_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    test_data = {
        "fields": {
            FEISHU_TABLE_FIELDS['stock_code']['name']: "TEST001",
            FEISHU_TABLE_FIELDS['status']['name']: "权限测试"
        }
    }
    
    headers["Content-Type"] = "application/json"
    
    try:
        resp = requests.post(create_url, headers=headers, json=test_data)
        create_result = resp.json()
        print(f"✏️ 创建记录响应: {create_result}")
        
        if create_result.get('code') == 0:
            print("✅ 写入权限正常")
            
            # 获取创建的记录ID
            test_record_id = create_result.get('data', {}).get('record', {}).get('record_id')
            
            if test_record_id:
                # 3. 测试更新权限
                print("🔄 测试更新权限...")
                update_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/{test_record_id}"
                update_data = {
                    "fields": {
                        FEISHU_TABLE_FIELDS['status']['name']: "权限测试-已更新"
                    }
                }
                
                resp = requests.put(update_url, headers=headers, json=update_data)
                update_result = resp.json()
                print(f"🔄 更新记录响应: {update_result}")
                
                if update_result.get('code') == 0:
                    print("✅ 更新权限正常")
                else:
                    print(f"❌ 更新权限异常: {update_result}")
                
                # 4. 清理测试记录
                print("🧹 清理测试记录...")
                delete_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/{test_record_id}"
                resp = requests.delete(delete_url, headers=headers)
                delete_result = resp.json()
                
                if delete_result.get('code') == 0:
                    print("✅ 测试记录已清理")
                else:
                    print(f"⚠️ 测试记录清理失败: {delete_result}")
                
                return True
            else:
                print("❌ 未获取到测试记录ID")
                return False
        else:
            print(f"❌ 写入权限异常: {create_result}")
            return False
            
    except Exception as e:
        print(f"❌ 写入权限测试异常: {e}")
        return False

def test_document_creation():
    """测试文档创建"""
    print("\n📄 测试文档创建...")
    access_token = get_feishu_access_token()
    if not access_token:
        return False
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        # 创建测试文档
        create_url = "https://open.feishu.cn/open-apis/docx/v1/documents"
        resp = requests.post(create_url, headers=headers, json={
            "title": f"[权限测试]{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        })
        doc_data = resp.json()
        
        print(f"📄 文档创建响应: {doc_data}")
        
        if doc_data.get('code') == 0:
            doc_id = doc_data.get('data', {}).get('document', {}).get('document_id')
            if doc_id:
                print(f"✅ 文档创建成功: {doc_id}")
                doc_url = f"https://feishu.cn/docx/{doc_id}"
                print(f"📄 文档链接: {doc_url}")
                return doc_id
            else:
                print("❌ 未获取到文档ID")
                return False
        else:
            print(f"❌ 文档创建失败: {doc_data}")
            return False
            
    except Exception as e:
        print(f"❌ 文档创建测试异常: {e}")
        return False

def main():
    """主测试流程"""
    print("🚀 飞书表格集成权限测试")
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
    
    # 测试权限
    table_permission_ok = test_table_permissions()
    doc_permission_ok = test_document_creation()
    
    print(f"\n{'=' * 60}")
    print("🏁 权限测试结果:")
    print(f"   📊 表格权限: {'✅ 正常' if table_permission_ok else '❌ 异常'}")
    print(f"   📄 文档权限: {'✅ 正常' if doc_permission_ok else '❌ 异常'}")
    
    if table_permission_ok and doc_permission_ok:
        print("🎉 所有权限测试通过，可以运行完整流程！")
    else:
        print("⚠️ 权限配置仍有问题，请检查飞书开发者后台设置")
    
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
