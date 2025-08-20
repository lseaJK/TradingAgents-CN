from feishu_manager import FeishuManager

def test_tenant_access_token():
    mgr = FeishuManager(env_path=r'e:\my_agent_learning\TradingAgents\TradingAgents-CN-main\.env')
    tenant_token = mgr.get_tenant_access_token()
    print('tenant_access_token:', tenant_token)
    user_token_info = mgr.get_user_access_token(code)
    print('user_access_token:', user_token_info.get('access_token'))
    refreshed = mgr.refresh_user_access_token(refresh_token)
    print('refreshed_access_token:', refreshed.get('access_token'))
if __name__ == '__main__':
    test_tenant_access_token()