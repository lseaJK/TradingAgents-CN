#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_user_authorization.py - 获取飞书用户授权的完整指南
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# 加载主目录的 .env 文件
env_path = Path(__file__).parent.parent / 'TradingAgents-CN-main' / '.env'
load_dotenv(env_path)

FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID")

def generate_authorization_url():
    """生成飞书用户授权URL"""
    
    # 重定向URI (飞书API Explorer提供的标准重定向地址)
    redirect_uri = "https://open.feishu.cn/api-explorer/loading"
    
    # 权限范围 - 包含表格读写权限
    scope = "bitable:app:readwrite docx:document:write"
    
    # 生成授权URL
    auth_url = (
        f"https://open.feishu.cn/open-apis/authen/v1/index?"
        f"app_id={FEISHU_APP_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"state=trading_agents"
    )
    
    return auth_url

def main():
    print("🔐 飞书用户授权获取指南")
    print("=" * 60)
    
    if not FEISHU_APP_ID:
        print("❌ 错误：未找到FEISHU_APP_ID，请检查.env配置")
        return
    
    print(f"📱 应用ID: {FEISHU_APP_ID}")
    print()
    
    # 生成授权URL
    auth_url = generate_authorization_url()
    
    print("📋 获取用户授权的步骤:")
    print("1️⃣  复制下面的授权链接到浏览器中打开")
    print("2️⃣  使用飞书账号登录并同意授权")
    print("3️⃣  授权成功后，浏览器会跳转到一个包含code参数的页面")
    print("4️⃣  从URL中复制code参数的值")
    print("5️⃣  将code参数值用于获取访问令牌")
    print()
    
    print("🔗 授权链接:")
    print("-" * 60)
    print(auth_url)
    print("-" * 60)
    print()
    
    print("📝 示例:")
    print("授权成功后，浏览器URL可能类似:")
    print("https://open.feishu.cn/api-explorer/loading?code=ABC123DEF456&state=trading_agents")
    print()
    print("请复制 'code=' 后面的值（例如: ABC123DEF456）")
    print()
    
    print("⚠️  注意事项:")
    print("• 授权码有效期很短（通常几分钟），获取后请立即使用")
    print("• 确保使用有表格编辑权限的飞书账号进行授权")
    print("• 授权成功后将获得用户访问令牌，可以绕过应用权限限制")
    print()
    
    print("🔄 获取授权码后的下一步:")
    print("1. 编辑 get_initial_token.py，将获取的code填入")
    print("2. 运行 python get_initial_token.py 获取refresh_token")
    print("3. 运行 python mainB.py 测试表格写入功能")

if __name__ == "__main__":
    main()
