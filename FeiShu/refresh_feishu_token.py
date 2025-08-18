import requests
import os
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件

app_id = os.environ.get("FEISHU_APP_ID")
app_secret = os.environ.get("FEISHU_APP_SECRET")
refresh_token = os.environ.get("FEISHU_REFRESH_TOKEN")

def refresh_user_access_token(app_id, app_secret, refresh_token):
    """
    用 refresh_token 刷新 user_access_token 和 refresh_token
    """
    url = "https://open.feishu.cn/open-apis/authen/v1/refresh_access_token"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    body = {
        "grant_type": "refresh_token",
        "app_id": app_id,
        "app_secret": app_secret,
        "refresh_token": refresh_token
    }
    resp = requests.post(url, headers=headers, json=body)
    data = resp.json()
    if data.get("code") == 0:
        print("user_access_token:", data["data"]["access_token"])
        print("refresh_token:", data["data"]["refresh_token"])
        # 用 PowerShell 写入用户环境变量
        def set_env_var(key, value):
            """
            用 PowerShell 设置用户环境变量
            """
            cmd = f'[Environment]::SetEnvironmentVariable("{key}", "{value}", "User")'
            subprocess.run(["powershell", "-Command", cmd])
        
        set_env_var("FEISHU_REFRESH_TOKEN", data["data"]["refresh_token"])
        print("已写入用户环境变量 FEISHU_REFRESH_TOKEN")
        # 可写入 .env 文件
        return data["data"]["access_token"], data["data"]["refresh_token"]
    else:
        print("刷新失败:", data)
        # 检查错误码，若为 20037 或 20064，提示需要重新授权
        if data.get("code") in [20037, 20064]:
            print("refresh_token 已过期或被撤销，请重新授权获取新的 refresh_token")
        return None, None

def get_app_access_token(app_id, app_secret):
    """
    实时获取并写入最新的 access_token
    """
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/"
    resp = requests.post(url, json={
        "app_id": app_id,
        "app_secret": app_secret
    })
    data = resp.json()
    token = data.get('app_access_token')
    if token:
        print("app_access_token:", token)
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        # 直接覆盖写入，保证每次都是最新
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        # 移除所有旧的 FEISHU_ACCESS_TOKEN
        lines = [line for line in lines if not line.startswith('FEISHU_ACCESS_TOKEN=')]
        lines.append(f'FEISHU_ACCESS_TOKEN={token}\n')
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("已写入 .env 文件 FEISHU_ACCESS_TOKEN")
        return token
    else:
        print("获取失败:", data)
        return None


# 查询 TradingAgents任务表内容的相关函数
def get_table_id(app_token, access_token):
    """
    获取表格 table_id
    """
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    if 'data' in data and 'tables' in data['data']:
        # 默认取第一个表，如有多个可遍历查找
        table_id = data['data']['tables'][0]['table_id']
        print("table_id:", table_id)
        return table_id
    else:
        print("获取 table_id 失败:", data)
        return None

def get_table_records(app_token, table_id, access_token):
    """
    获取表格所有记录并打印每行 id
    """
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    if 'data' in data and 'items' in data['data']:
        records = data['data']['items']
        for record in records:
            print("Record id:", record['record_id'])
            print("Fields:", record['fields'])
    else:
        print("获取表格内容失败:", data)

if __name__ == "__main__":
    # 优先尝试刷新 user_access_token
    if refresh_token:
        access_token, new_refresh_token = refresh_user_access_token(app_id, app_secret, refresh_token)
        print("获取的 user_access_token:", access_token)
        if access_token:
            # TradingAgents任务表的 app_token
            APP_TOKEN = "SCrXbf2WJaPLV5sqBTOcxzzknWb"
            table_id = get_table_id(APP_TOKEN, access_token)
            if table_id:
                get_table_records(APP_TOKEN, table_id, access_token)
        else:
            print("user_access_token 获取失败，尝试获取 app_access_token")
            token = get_app_access_token(app_id, app_secret)
            print("获取的 app_access_token:", token)
    else:
        print("未检测到 FEISHU_REFRESH_TOKEN，尝试获取 app_access_token")
        token = get_app_access_token(app_id, app_secret)
        print("获取的 app_access_token:", token)