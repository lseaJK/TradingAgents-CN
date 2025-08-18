import requests
import os
from dotenv import load_dotenv

load_dotenv()

app_id = os.environ.get("FEISHU_APP_ID")
app_secret = os.environ.get("FEISHU_APP_SECRET")
code = "bHNiGae8HeKd44EwbdIEFBda5wfyDcHd"

def get_initial_tokens(app_id, app_secret, code):
    """
    用授权 code 换取初始的 access_token 和 refresh_token
    """
    url = "https://open.feishu.cn/open-apis/authen/v1/access_token"
    body = {
        "app_id": app_id,
        "app_secret": app_secret,
        "code": code,
        "grant_type": "authorization_code"
    }
    resp = requests.post(url, json=body)
    data = resp.json()
    print("Response:", data)
    
    if data.get("code") == 0:
        access_token = data["data"]["access_token"]
        refresh_token = data["data"]["refresh_token"]
        print("access_token:", access_token)
        print("refresh_token:", refresh_token)
        return access_token, refresh_token
    else:
        print("获取失败:", data)
        return None, None

if __name__ == "__main__":
    access_token, refresh_token = get_initial_tokens(app_id, app_secret, code)
    if refresh_token:
        # 设置环境变量
        os.system(f'powershell -Command "[Environment]::SetEnvironmentVariable(\'FEISHU_REFRESH_TOKEN\', \'{refresh_token}\', \'User\')"')
        print("已设置 FEISHU_REFRESH_TOKEN 环境变量")
