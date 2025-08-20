
# -*- coding: utf-8 -*-
"""
refresh_token.py - 刷新飞书用户访问令牌（企业自建应用/服务端模式）
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
FEISHU_REFRESH_TOKEN = os.getenv('FEISHU_REFRESH_TOKEN')

def get_app_access_token():
    """获取应用访问令牌"""
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

def refresh_user_access_token():
    """使用refresh_token刷新用户访问令牌（企业自建应用/服务端模式）"""
    if not FEISHU_REFRESH_TOKEN:
        print("❌ 未设置FEISHU_REFRESH_TOKEN，无法刷新用户令牌")
        return None
    app_token = get_app_access_token()
    if not app_token:
        print("❌ 无法获取应用令牌，无法刷新用户令牌")
        return None
    url = "https://open.feishu.cn/open-apis/auth/v3/user_access_token/refresh"
    headers = {
        "Authorization": f"Bearer {app_token}",
        "Content-Type": "application/json"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": FEISHU_REFRESH_TOKEN
    }
    try:
        resp = requests.post(url, headers=headers, json=data)
        result = resp.json()
        print(f"📊 刷新响应: {result}")
        if result.get('code') != 0:
            print(f"❌ 刷新用户访问令牌失败: {result}")
            return None
        new_access_token = result.get('data', {}).get('access_token')
        new_refresh_token = result.get('data', {}).get('refresh_token')
        expires_in = result.get('data', {}).get('expires_in')
        if new_access_token:
            print(f"✅ 获取新的用户访问令牌成功: {new_access_token[:10]}...")
            print(f"📅 令牌有效期: {expires_in} 秒")
            update_env_file(new_access_token, new_refresh_token)
            return new_access_token
        else:
            print(f"❌ 响应中没有找到access_token: {result}")
            return None
    except Exception as e:
        print(f"❌ 刷新用户访问令牌异常: {e}")
        return None

def update_env_file(new_access_token, new_refresh_token=None):
    """更新.env文件中的token"""
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        print("❌ .env文件不存在")
        return
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('FEISHU_ACCESS_TOKEN='):
            lines[i] = f'FEISHU_ACCESS_TOKEN={new_access_token}\n'
            updated = True
            print(f"✅ 更新FEISHU_ACCESS_TOKEN")
        elif new_refresh_token and line.startswith('FEISHU_REFRESH_TOKEN='):
            lines[i] = f'FEISHU_REFRESH_TOKEN={new_refresh_token}\n'
            print(f"✅ 更新FEISHU_REFRESH_TOKEN")
    if not updated:
        lines.append(f'\nFEISHU_ACCESS_TOKEN={new_access_token}\n')
        print(f"✅ 添加FEISHU_ACCESS_TOKEN")
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"💾 .env文件已更新")

def main():
    print("🚀 飞书用户访问令牌刷新工具（企业自建应用/服务端模式）")
    print("=" * 50)
    print(f"📋 配置检查:")
    print(f"   APP_ID: {FEISHU_APP_ID}")
    print(f"   APP_SECRET: {'已设置' if FEISHU_APP_SECRET else '未设置'}")
    print(f"   REFRESH_TOKEN: {'已设置' if FEISHU_REFRESH_TOKEN else '未设置'}")
    if not all([FEISHU_APP_ID, FEISHU_APP_SECRET]):
        print("❌ 缺少必要的飞书应用配置")
        return
    new_token = refresh_user_access_token()
    if new_token:
        print(f"\n✅ 令牌刷新成功!")
        print(f"🔑 新的用户访问令牌: {new_token}")
        print(f"💡 提示: 请重新运行mainB.py测试表格写入功能")
    else:
        print(f"\n❌ 令牌刷新失败")
        print(f"💡 提示: 请检查FEISHU_REFRESH_TOKEN是否正确，或重新获取用户授权")

if __name__ == "__main__":
    main()
