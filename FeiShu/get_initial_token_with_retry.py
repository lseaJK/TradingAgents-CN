#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_initial_token_with_retry.py - 带重试机制的用户令牌获取脚本
"""

import requests
import os
import time
from dotenv import load_dotenv
from pathlib import Path

# 加载主目录的 .env 文件
env_path = Path(__file__).parent.parent / 'TradingAgents-CN-main' / '.env'
load_dotenv(env_path)

app_id = os.environ.get("FEISHU_APP_ID")
app_secret = os.environ.get("FEISHU_APP_SECRET")

def get_initial_tokens_with_retry(app_id, app_secret, code, max_retries=3, timeout=30):
    """
    用授权 code 换取初始的 access_token 和 refresh_token (带重试机制)
    """
    url = "https://open.feishu.cn/open-apis/authen/v1/access_token"
    body = {
        "app_id": app_id,
        "app_secret": app_secret,
        "code": code,
        "grant_type": "authorization_code"
    }
    
    print(f"🔄 尝试获取用户访问令牌...")
    print(f"📋 请求信息:")
    print(f"   URL: {url}")
    print(f"   APP ID: {app_id}")
    print(f"   授权码: {code}")
    
    for attempt in range(max_retries):
        try:
            print(f"\n🔄 第 {attempt + 1} 次尝试...")
            
            # 设置较长的超时时间和会话配置
            session = requests.Session()
            session.verify = True  # 启用SSL验证
            
            resp = session.post(
                url, 
                json=body, 
                timeout=timeout,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'TradingAgents/1.0'
                }
            )
            
            print(f"📊 HTTP状态码: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"📊 API响应: {data}")
                
                if data.get("code") == 0:
                    access_token = data["data"]["access_token"]
                    refresh_token = data["data"]["refresh_token"]
                    
                    print("✅ 成功获取令牌!")
                    print(f"🔑 Access Token: {access_token[:20]}...")
                    print(f"🔄 Refresh Token: {refresh_token[:20]}...")
                    
                    # 保存到环境变量和.env文件
                    save_tokens_to_env(access_token, refresh_token)
                    
                    return access_token, refresh_token
                else:
                    print(f"❌ API返回错误: {data}")
                    if data.get("code") == 20003:
                        print("💡 错误原因: 授权码已过期，请重新获取授权")
                        return None, None
                    elif data.get("code") == 10003:
                        print("💡 错误原因: 参数错误，请检查APP_ID和APP_SECRET")
                        return None, None
            else:
                print(f"❌ HTTP错误: {resp.status_code}")
                print(f"响应内容: {resp.text}")
                
        except requests.exceptions.ConnectTimeout:
            print(f"⏰ 第 {attempt + 1} 次尝试连接超时")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"⏳ 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 第 {attempt + 1} 次尝试网络错误: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"⏳ 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        except Exception as e:
            print(f"❌ 第 {attempt + 1} 次尝试未知错误: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"⏳ 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
    
    print("❌ 所有重试都失败了")
    return None, None

def save_tokens_to_env(access_token, refresh_token):
    """
    保存令牌到.env文件
    """
    env_file = Path(__file__).parent.parent / 'TradingAgents-CN-main' / '.env'
    
    if not env_file.exists():
        print("❌ .env文件不存在")
        return
    
    try:
        # 读取现有内容
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 更新或添加token
        updated_user_token = False
        updated_refresh_token = False
        
        for i, line in enumerate(lines):
            if line.startswith('FEISHU_USER_ACCESS_TOKEN='):
                lines[i] = f'FEISHU_USER_ACCESS_TOKEN={access_token}\n'
                updated_user_token = True
                print(f"✅ 更新FEISHU_USER_ACCESS_TOKEN")
            elif line.startswith('FEISHU_REFRESH_TOKEN='):
                lines[i] = f'FEISHU_REFRESH_TOKEN={refresh_token}\n'
                updated_refresh_token = True
                print(f"✅ 更新FEISHU_REFRESH_TOKEN")
        
        # 如果没有找到相应行，添加它们
        if not updated_user_token:
            lines.append(f'\nFEISHU_USER_ACCESS_TOKEN={access_token}\n')
            print(f"✅ 添加FEISHU_USER_ACCESS_TOKEN")
        
        if not updated_refresh_token:
            lines.append(f'FEISHU_REFRESH_TOKEN={refresh_token}\n')
            print(f"✅ 添加FEISHU_REFRESH_TOKEN")
        
        # 写入文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"💾 .env文件已更新")
        
    except Exception as e:
        print(f"❌ 保存到.env文件失败: {e}")

def main():
    print("🚀 飞书用户令牌获取工具 (带重试机制)")
    print("=" * 60)
    
    if not app_id or not app_secret:
        print("❌ 错误：缺少FEISHU_APP_ID或FEISHU_APP_SECRET")
        print("请检查.env文件配置")
        return
    
    if not code:
        print("❌ 错误：缺少授权码")
        print("请先运行 python get_user_authorization.py 获取授权链接")
        return
    
    access_token, refresh_token = get_initial_tokens_with_retry(app_id, app_secret, code)
    
    if access_token and refresh_token:
        print(f"\n{'=' * 60}")
        print("🎉 令牌获取成功!")
        print(f"🔑 用户访问令牌: {access_token}")
        print(f"🔄 刷新令牌: {refresh_token}")
        print(f"💾 已保存到.env文件")
        print(f"{'=' * 60}")
        print()
        print("🔄 下一步操作:")
        print("1. 切换到主目录: cd ../TradingAgents-CN-main")
        print("2. 运行测试脚本: python mainB_with_user_token.py")
        print("3. 验证表格写入功能是否正常")
    else:
        print(f"\n{'=' * 60}")
        print("❌ 令牌获取失败")
        print("💡 可能的原因:")
        print("   1. 授权码已过期 (有效期很短)")
        print("   2. 网络连接问题")
        print("   3. APP_ID或APP_SECRET配置错误")
        print()
        print("🔄 建议操作:")
        print("1. 重新获取授权码: python get_user_authorization.py")
        print("2. 检查网络连接")
        print("3. 验证.env文件中的应用配置")

if __name__ == "__main__":
    main()
