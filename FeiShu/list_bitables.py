import requests

# 使用当前有效的 user_access_token
access_token = "xxx"

def list_bitables(access_token):
    """
    列出所有有权限访问的多维表
    """
    url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"page_size": 50}
    
    resp = requests.get(url, headers=headers, params=params)
    print("Status code:", resp.status_code)
    print("Response:", resp.text)
    
    if resp.status_code == 200:
        try:
            data = resp.json()
            if data.get("code") == 0:
                apps = data.get("data", {}).get("items", [])
                for app in apps:
                    print(f"表格名称: {app.get('name')}")
                    print(f"app_token: {app.get('app_token')}")
                    print(f"URL: {app.get('url')}")
                    print("---")
                return apps
            else:
                print("API 错误:", data)
        except Exception as e:
            print("JSON 解析错误:", e)
    return None

if __name__ == "__main__":
    list_bitables(access_token)
