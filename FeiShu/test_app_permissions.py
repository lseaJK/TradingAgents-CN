#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_app_permissions.py - 测试应用权限配置
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# 加载.env配置
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# 飞书配置
FEISHU_APP_ID = os.getenv('FEISHU_APP_ID')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET')
FEISHU_APP_TOKEN = os.getenv('TABLE_APP_TOKEN', "SCrXbf2WJaPLV5sqBTOcxzzknWb")
FEISHU_TABLE_ID = os.getenv('TABLE_ID', "tblmJhLZBJAaAAPf")

def get_app_access_token():
    """获取应用访问令牌"""
    print("🔄 获取应用访问令牌...")
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/"
    resp = requests.post(url, json={
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    })
    data = resp.json()
    
    if data.get('code') != 0:
        print(f"❌ 获取应用访问令牌失败: {data}")
        return None
        
    token = data.get('app_access_token')
    print(f"✅ 获取应用访问令牌成功: {token[:10]}...")
    return token

def test_minimal_record_update():
    """测试最小化的记录更新，只更新一个字段"""
    print("\n🧪 测试最小化记录更新...")
    
    access_token = get_app_access_token()
    if not access_token:
        return False
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # 先获取一个现有记录
    records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    try:
        resp = requests.get(records_url, headers=headers)
        data = resp.json()
        
        if data.get('code') != 0:
            print(f"❌ 无法获取记录列表: {data}")
            return False
            
        items = data.get('data', {}).get('items', [])
        if not items:
            print("❌ 表格中没有记录")
            return False
            
        # 选择第一个有股票代码的记录
        target_record = None
        for item in items:
            if item.get('fields', {}).get('股票代码'):
                target_record = item
                break
        
        if not target_record:
            print("❌ 没有找到有股票代码的记录")
            return False
            
        record_id = target_record['record_id']
        print(f"🎯 选择记录进行测试: {record_id}")
        
        # 尝试最小化更新 - 只更新一个简单字段
        update_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/{record_id}"
        
        # 使用字段名而不是字段ID
        update_data = {
            "fields": {
                "当前状态": "权限测试"
            }
        }
        
        print(f"🔄 尝试更新记录...")
        print(f"   URL: {update_url}")
        print(f"   数据: {update_data}")
        
        resp = requests.put(update_url, headers=headers, json=update_data)
        result = resp.json()
        
        print(f"📊 更新响应: HTTP {resp.status_code}")
        print(f"📊 响应内容: {result}")
        
        if result.get('code') == 0:
            print("✅ 应用令牌有表格写入权限!")
            return True
        else:
            error_code = result.get('code')
            error_msg = result.get('msg', '未知错误')
            print(f"❌ 更新失败")
            print(f"   错误代码: {error_code}")
            print(f"   错误信息: {error_msg}")
            
            # 分析具体的权限问题
            if error_code == 91403:
                print("💡 分析: 91403 - 应用没有表格写入权限")
                print("   可能原因:")
                print("   1. 应用未被添加到有写入权限的用户组")
                print("   2. 表格开启了高级权限限制")
                print("   3. 应用缺少 'bitable:app:readwrite' 权限")
            elif error_code == 99991663:
                print("💡 分析: 99991663 - 访问令牌无效")
                print("   可能原因:")
                print("   1. 令牌已过期")
                print("   2. 此API不支持应用令牌，需要用户令牌")
            
            return False
            
    except Exception as e:
        print(f"❌ 测试更新异常: {e}")
        return False

def main():
    print("🧪 飞书应用权限测试工具")
    print("=" * 50)
    
    print(f"📋 配置信息:")
    print(f"   APP_ID: {FEISHU_APP_ID}")
    print(f"   APP_TOKEN: {FEISHU_APP_TOKEN}")
    print(f"   TABLE_ID: {FEISHU_TABLE_ID}")
    
    success = test_minimal_record_update()
    
    print(f"\n{'=' * 50}")
    if success:
        print("🎉 权限测试通过! 应用可以更新表格记录")
        print("💡 建议: 可以在mainB.py中使用应用令牌进行表格操作")
    else:
        print("❌ 权限测试失败")
        print("💡 建议:")
        print("   1. 检查飞书开发者控制台中的应用权限配置")
        print("   2. 确保应用有 'bitable:app:readwrite' 权限")
        print("   3. 检查表格是否开启了高级权限限制")
        print("   4. 如需要，获取用户授权使用user_access_token")

if __name__ == "__main__":
    main()
