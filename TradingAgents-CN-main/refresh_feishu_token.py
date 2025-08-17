import requests
import os
import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件

app_id = os.environ.get("FEISHU_APP_ID")
app_secret = os.environ.get("FEISHU_APP_SECRET")

def get_app_access_token(app_id, app_secret):
    """
    实时获取并写入最新的 access_token 到 .env 文件
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

# 调用函数
if __name__ == "__main__":
    token = get_app_access_token(app_id, app_secret)
    if not token:
        print("access_token 获取失败，无法进行表格创建测试")
        exit(1)

    # 用刚刚获取的 token 直接进行表格创建
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
    body = {
        "name": "TradingAgents任务表",
        "time_zone": "Asia/Shanghai"
    }
    resp = requests.post(url, headers=headers, json=body)
    print("表格创建返回:", resp.json())