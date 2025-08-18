import requests

# 使用刚刚获取的 user_access_token
access_token = "u-dB4sRVs81aUrECnzj3KIZF5h3rS50h8hMi001k8w2BBq"

def search_documents(access_token, search_key):
    """
    搜索飞书文档
    """
    url = "https://open.feishu.cn/open-apis/docx_builtin/search"
    headers = {"Authorization": f"Bearer {access_token}"}
    body = {
        "search_key": search_key,
        "count": 10
    }
    resp = requests.post(url, headers=headers, json=body)
    print("Status code:", resp.status_code)
    print("Response text:", resp.text)
    try:
        data = resp.json()
        print("搜索结果:", data)
        return data
    except Exception as e:
        print("JSON 解析错误:", e)
        return None

if __name__ == "__main__":
    # 搜索 TradingAgents任务表
    result = search_documents(access_token, "TradingAgents任务表")
