#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_feishu_table.py - 检查飞书表格字段信息的脚本
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv
import json

# 加载.env配置
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

FEISHU_APP_ID = os.getenv('FEISHU_APP_ID')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET')
# 从.env获取TradingAgents任务表配置
FEISHU_APP_TOKEN = os.getenv('TABLE_APP_TOKEN', "SCrXbf2WJaPLV5sqBTOcxzzknWb")
FEISHU_TABLE_ID = os.getenv('TABLE_ID', "tblmJhLZBJAaAAPf")

def get_feishu_access_token():
    """获取飞书访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/"
    resp = requests.post(url, json={
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    })
    data = resp.json()
    return data.get('app_access_token')

def check_table_fields():
    """检查表格字段信息"""
    print("🔍 检查飞书表格字段信息...")
    access_token = get_feishu_access_token()
    if not access_token:
        print("❌ 无法获取访问令牌")
        return
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 获取字段信息
    fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/fields"
    resp = requests.get(fields_url, headers=headers)
    fields_data = resp.json()
    
    print("📊 字段信息:")
    print(json.dumps(fields_data, indent=2, ensure_ascii=False))
    
    return fields_data

def check_table_records():
    """检查表格记录（使用字段ID）"""
    print("\n🔍 检查飞书表格记录...")
    access_token = get_feishu_access_token()
    if not access_token:
        print("❌ 无法获取访问令牌")
        return
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 获取记录信息
    records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    resp = requests.get(records_url, headers=headers)
    records_data = resp.json()
    
    print("📊 记录信息:")
    print(json.dumps(records_data, indent=2, ensure_ascii=False))
    
    return records_data

def main():
    print("🚀 检查飞书表格配置")
    print("=" * 50)
    
    # 检查字段
    fields_data = check_table_fields()
    
    # 检查记录
    records_data = check_table_records()
    
    # 分析字段映射
    if fields_data and fields_data.get('code') == 0:
        print("\n📋 字段映射分析:")
        fields = fields_data.get('data', {}).get('items', [])
        for field in fields:
            field_name = field.get('field_name', '')
            field_id = field.get('field_id', '')
            field_type = field.get('type', '')
            print(f"   {field_name} -> ID: {field_id}, Type: {field_type}")

if __name__ == "__main__":
    main()
