import requests
import os

# ...existing code...
import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件

app_id = os.environ.get("FEISHU_APP_ID")
app_secret = os.environ.get("FEISHU_APP_SECRET")

def get_app_access_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/"
    resp = requests.post(url, json={
        "app_id": app_id,
        "app_secret": app_secret
    })
    data = resp.json()
    token = data.get('app_access_token')
    if token:
        print("app_access_token:", token)
        return token
    else:
        print("获取失败:", data)
        return None

# 调用函数
if __name__ == "__main__":
    get_app_access_token(app_id, app_secret)