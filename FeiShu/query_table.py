import requests

# 使用之前获取的有效 user_access_token
access_token = "xxx"
APP_TOKEN = "xxx"

def get_table_id(app_token, access_token):
    """
    获取表格 table_id
    """
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    print("获取表格列表响应:", data)
    
    if 'data' in data and 'items' in data['data']:
        for table in data['data']['items']:
            print(f"表格名称: {table.get('name')}")
            print(f"table_id: {table.get('table_id')}")
        # 默认取第一个表
        table_id = data['data']['items'][0]['table_id']
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
    print("获取记录响应:", data)
    
    if 'data' in data and 'items' in data['data']:
        records = data['data']['items']
        print(f"\n=== TradingAgents任务表 共有 {len(records)} 行数据 ===")
        for i, record in enumerate(records, 1):
            print(f"第 {i} 行:")
            print(f"  Record ID: {record['record_id']}")
            print(f"  Fields: {record['fields']}")
            print("---")
        return records
    else:
        print("获取表格内容失败:", data)
        return None

if __name__ == "__main__":
    print("开始查询 TradingAgents任务表...")
    table_id = get_table_id(APP_TOKEN, access_token)
    if table_id:
        print(f"成功获取 table_id: {table_id}")
        records = get_table_records(APP_TOKEN, table_id, access_token)
        if records:
            print(f"\n✅ 成功查询到 {len(records)} 行数据，每行都有有效的 record_id")
        else:
            print("❌ 查询失败")
    else:
        print("❌ 获取 table_id 失败")
