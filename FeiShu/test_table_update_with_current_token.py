#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_table_update_with_current_token.py - 使用当前令牌测试表格更新
"""

import requests
import os
from dotenv import load_dotenv
from pathlib import Path

# 加载FeiShu文件夹中的.env文件
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# 同时加载主目录的.env文件
main_env_path = Path(__file__).parent.parent / 'TradingAgents-CN-main' / '.env'
load_dotenv(main_env_path)

# 获取配置
FEISHU_ACCESS_TOKEN = os.getenv('FEISHU_ACCESS_TOKEN')
FEISHU_APP_TOKEN = os.getenv('TABLE_APP_TOKEN', "xxxxxxxxxxxxx")
FEISHU_TABLE_ID = os.getenv('TABLE_ID', "xxxxxxxxxxxx")

print("🔍 当前令牌测试")
print("=" * 50)
print(f"访问令牌: {FEISHU_ACCESS_TOKEN}")
print(f"表格APP Token: {FEISHU_APP_TOKEN}")
print(f"表格ID: {FEISHU_TABLE_ID}")

def test_table_read():
    """测试表格读取"""
    print("\n📖 测试表格读取...")
    
    if not FEISHU_ACCESS_TOKEN:
        print("❌ 没有访问令牌")
        return None
        
    headers = {"Authorization": f"Bearer {FEISHU_ACCESS_TOKEN}"}
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    
    try:
        resp = requests.get(url, headers=headers)
        data = resp.json()
        
        print(f"HTTP状态码: {resp.status_code}")
        print(f"API响应: {data}")
        
        if data.get('code') == 0:
            items = data.get('data', {}).get('items', [])
            print(f"✅ 表格读取成功，共 {len(items)} 条记录")
            
            # 找到一个有股票代码的记录用于测试
            for item in items:
                fields = item.get('fields', {})
                if fields.get('股票代码'):
                    return item
            
            print("❌ 没有找到包含股票代码的记录")
            return None
        else:
            print(f"❌ 表格读取失败: {data}")
            return None
            
    except Exception as e:
        print(f"❌ 表格读取异常: {e}")
        return None

def test_table_update(record):
    """测试表格更新"""
    print(f"\n📝 测试表格更新...")
    
    if not record:
        print("❌ 没有可用的记录进行测试")
        return False
        
    record_id = record['record_id']
    print(f"测试记录ID: {record_id}")
    
    headers = {
        "Authorization": f"Bearer {FEISHU_ACCESS_TOKEN}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/{record_id}"
    
    # 测试更新数据
    update_data = {
        "fields": {
            "当前状态": "令牌测试中"
        }
    }
    
    print(f"更新数据: {update_data}")
    
    try:
        resp = requests.put(url, headers=headers, json=update_data)
        result = resp.json()
        
        print(f"HTTP状态码: {resp.status_code}")
        print(f"API响应: {result}")
        
        if result.get('code') == 0:
            print("✅ 表格更新成功！")
            
            # 立即再次更新状态
            update_data2 = {
                "fields": {
                    "当前状态": "令牌测试完成"
                }
            }
            
            resp2 = requests.put(url, headers=headers, json=update_data2)
            result2 = resp2.json()
            
            if result2.get('code') == 0:
                print("✅ 二次更新也成功！当前令牌有表格写入权限！")
                return True
            else:
                print(f"⚠️  二次更新失败: {result2}")
                return True  # 第一次成功就说明有权限
        else:
            error_code = result.get('code')
            error_msg = result.get('msg', '未知错误')
            print(f"❌ 表格更新失败")
            print(f"   错误代码: {error_code}")
            print(f"   错误信息: {error_msg}")
            return False
            
    except Exception as e:
        print(f"❌ 表格更新异常: {e}")
        return False

def main():
    print("🧪 飞书表格权限测试")
    print("使用当前FeiShu/.env中的访问令牌")
    print("=" * 50)
    
    # 1. 测试表格读取
    test_record = test_table_read()
    
    # 2. 测试表格更新
    if test_record:
        success = test_table_update(test_record)
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 测试结果：当前令牌有表格写入权限！")
            print("💡 这意味着我们可以直接使用现有的令牌进行表格操作")
            print("🔄 建议：运行完整的业务脚本测试")
        else:
            print("❌ 测试结果：当前令牌没有表格写入权限")
            print("💡 这确认了需要用户授权才能获得写入权限")
    else:
        print("\n❌ 无法进行更新测试，表格读取失败")

if __name__ == "__main__":
    main()
