
import os
import requests
from typing import Optional

def get_feishu_auth_url(app_id: str, redirect_uri: str, state: str = "random_state") -> str:
    """
    生成飞书OAuth授权链接，state建议用uuid等随机字符串
    """
    from urllib.parse import quote
    return (
        f"https://open.feishu.cn/open-apis/authen/v1/index?app_id={app_id}"
        f"&redirect_uri={quote(redirect_uri)}&state={state}"
    )

class FeishuManager:
    """
    飞书Token管理类，支持tenant_access_token、user_access_token获取与刷新。
    配置从环境变量或.env文件读取。
    """
    def __init__(self, env_path: Optional[str] = None):
        self.env_path = env_path
        self.env = self._load_env(env_path)
        self.app_id = self.env.get('FEISHU_APP_ID')
        self.app_secret = self.env.get('FEISHU_APP_SECRET')
        self.redirect_uri = self.env.get('REDIRECT_URI')
        self.access_token = self.env.get('FEISHU_ACCESS_TOKEN')
        self.first_refresh_token = self.env.get('FIRST_REFRESH_TOKEN')
        
    def save_refresh_token(self, refresh_token: str):
        """
        保存refresh_token到.env文件（覆盖FIRST_REFRESH_TOKEN）
        """
        if not self.env_path:
            print("未指定.env路径，无法保存refresh_token")
            return
        lines = []
        found = False
        # 读取原文件内容
        if os.path.exists(self.env_path):
            with open(self.env_path, encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('FIRST_REFRESH_TOKEN='):
                        lines.append(f'FIRST_REFRESH_TOKEN={refresh_token}\n')
                        found = True
                    else:
                        lines.append(line)
        # 如果没有则追加
        if not found:
            lines.append(f'FIRST_REFRESH_TOKEN={refresh_token}\n')
        with open(self.env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def _load_env(self, env_path: Optional[str]):
        env = dict(os.environ)
        # 支持.env文件读取
        if env_path and os.path.exists(env_path):
            with open(env_path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'): continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        env[k.strip()] = v.strip().strip('"')
        return env

    def get_tenant_access_token(self) -> str:
        """
        获取tenant_access_token（应用级token）
        """
        url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/'
        payload = {
            'app_id': self.app_id,
            'app_secret': self.app_secret
        }
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        return resp.json().get('tenant_access_token')

    def get_user_access_token(self, code: Optional[str] = None, refresh_token: Optional[str] = None) -> dict:
        """
        优先用refresh_token自动刷新user_access_token，否则用授权code换取。
        """
        # 优先用refresh_token
        refresh_token = self.first_refresh_token
        print("使用FIRST_REFRESH_TOKEN自动刷新user_access_token...")
        token_info = self.refresh_user_access_token(refresh_token)
        # 自动保存新的refresh_token
        if 'refresh_token' in token_info:
            self.save_refresh_token(token_info['refresh_token'])
        return token_info
        
        # url = 'https://open.feishu.cn/open-apis/authen/v1/access_token'
        # payload = {
        #     'app_id': self.app_id,
        #     'app_secret': self.app_secret,
        #     'grant_type': 'authorization_code',
        #     'code': code,
        #     'redirect_uri': self.redirect_uri
        # }
        # resp = requests.post(url, json=payload)
        # resp.raise_for_status()
        # token_info = resp.json()
        # # 自动保存refresh_token
        # if 'refresh_token' in token_info:
        #     self.save_refresh_token(token_info['refresh_token'])
        # return token_info

    def refresh_user_access_token(self, refresh_token: str) -> dict:
        """
        刷新user_access_token
        """
        url = 'https://open.feishu.cn/open-apis/authen/v1/refresh_access_token'
        payload = {
            'app_id': self.app_id,
            'app_secret': self.app_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_env_token(self) -> Optional[str]:
        """
        获取.env文件或环境变量中的FEISHU_ACCESS_TOKEN
        """
        return self.access_token

    def get_config(self) -> dict:
        """
        返回所有飞书相关配置
        """
        return {
            'FEISHU_APP_ID': self.app_id,
            'FEISHU_APP_SECRET': self.app_secret,
            'REDIRECT_URI': self.redirect_uri,
            'FEISHU_ACCESS_TOKEN': self.access_token,
            'AUTH_CODE': self.auth_code
        }

if __name__ == '__main__':
    # 初始化管理器
    mgr = FeishuManager(env_path=r'e:\my_agent_learning\TradingAgents\TradingAgents-CN-main\.env')

    # 1. 生成授权链接
    import uuid
    state = str(uuid.uuid4())
    auth_url = get_feishu_auth_url(mgr.app_id, mgr.redirect_uri, state)
    print("请在浏览器打开以下链接进行授权:")
    print(auth_url)
    print("授权后，将跳转到redirect_uri并携带code参数。请将code填入.env的AUTH_CODE后再运行本脚本。")

    # 2. 获取tenant_access_token
    tenant_token = mgr.get_tenant_access_token()
    print("tenant_access_token:", tenant_token)

    # 3. 优先用FIRST_REFRESH_TOKEN自动获取user_access_token
    user_token_info = mgr.get_user_access_token()
    print("user_access_token info:", user_token_info)

    # 4. 如有refresh_token，可再次刷新
    if 'refresh_token' in user_token_info:
        refreshed = mgr.refresh_user_access_token(user_token_info['refresh_token'])
        mgr.save_refresh_token(refreshed.get('refresh_token', ''))
        print("Refreshed token info:", refreshed)
    else:
        print("No refresh_token found in user_token_info:", user_token_info)


