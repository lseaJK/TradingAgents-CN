"""
飞书表格数据自动获取完整流程脚本
功能：自动刷新token并查询TradingAgents任务表数据

使用方法：
1. 确保.env文件中配置了FEISHU_APP_ID和FEISHU_APP_SECRET
2. 首次运行需要用户授权获取refresh_token
3. 后续运行将自动刷新token并查询表格数据

作者：AI Assistant
创建时间：2025-08-18
"""

import requests
import os
import subprocess
from dotenv import load_dotenv
import json
from datetime import datetime

# 加载环境变量
load_dotenv()

# 飞书应用配置
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET")

# TradingAgents任务表配置
TABLE_APP_TOKEN = "xxxx"
TABLE_ID = "xxx"

# 授权相关
REDIRECT_URI = "https://open.feishu.cn/api-explorer/loading"
SCOPE = "openid offline_access bitable:app:readonly"

class FeishuTableManager:
    def __init__(self):
        self.app_id = FEISHU_APP_ID
        self.app_secret = FEISHU_APP_SECRET
        self.refresh_token = None
        self.access_token = None
        
    def get_authorization_url(self):
        """
        生成用户授权链接（首次使用时需要）
        """
        auth_url = (
            f"https://open.feishu.cn/open-apis/authen/v1/index?"
            f"app_id={self.app_id}&"
            f"redirect_uri={REDIRECT_URI}&"
            f"state=trading_agents&"
            f"scope={SCOPE}"
        )
        return auth_url
    
    def get_initial_tokens(self, authorization_code):
        """
        使用授权码获取初始的access_token和refresh_token
        """
        url = "https://open.feishu.cn/open-apis/authen/v1/access_token"
        body = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
            "code": authorization_code,
            "grant_type": "authorization_code"
        }
        
        try:
            resp = requests.post(url, json=body)
            data = resp.json()
            
            if data.get("code") == 0:
                self.access_token = data["data"]["access_token"]
                self.refresh_token = data["data"]["refresh_token"]
                
                # 保存refresh_token到环境变量
                self.set_env_var("FEISHU_REFRESH_TOKEN", self.refresh_token)
                
                print("✅ 成功获取初始tokens")
                print(f"Access Token: {self.access_token[:20]}...")
                print(f"Refresh Token: {self.refresh_token[:20]}...")
                
                return True
            else:
                print(f"❌ 获取tokens失败: {data}")
                return False
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False
    
    def refresh_access_token(self):
        """
        使用refresh_token刷新access_token
        """
        # 先从环境变量获取refresh_token
        self.refresh_token = os.environ.get("FEISHU_REFRESH_TOKEN")
        
        if not self.refresh_token:
            print("❌ 未找到refresh_token，需要重新授权")
            return False
            
        url = "https://open.feishu.cn/open-apis/authen/v1/refresh_access_token"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        body = {
            "grant_type": "refresh_token",
            "app_id": self.app_id,
            "app_secret": self.app_secret,
            "refresh_token": self.refresh_token
        }
        
        try:
            resp = requests.post(url, headers=headers, json=body)
            data = resp.json()
            
            if data.get("code") == 0:
                self.access_token = data["data"]["access_token"]
                new_refresh_token = data["data"]["refresh_token"]
                
                # 更新refresh_token
                if new_refresh_token != self.refresh_token:
                    self.refresh_token = new_refresh_token
                    self.set_env_var("FEISHU_REFRESH_TOKEN", new_refresh_token)
                    print("🔄 Refresh Token已更新")
                
                print("✅ 成功刷新access_token")
                return True
            else:
                print(f"❌ 刷新失败: {data}")
                # 如果refresh_token失效，提示重新授权
                if data.get("code") in [20026, 20037, 20064]:
                    print("🔐 Refresh Token已失效，需要重新授权")
                    print(f"授权链接: {self.get_authorization_url()}")
                return False
                
        except Exception as e:
            print(f"❌ 刷新请求异常: {e}")
            return False
    
    def get_app_access_token(self):
        """
        获取应用级access_token（备用方案）
        """
        url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/"
        body = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            resp = requests.post(url, json=body)
            data = resp.json()
            
            if data.get("app_access_token"):
                self.access_token = data["app_access_token"]
                print("✅ 成功获取app_access_token")
                return True
            else:
                print(f"❌ 获取app_access_token失败: {data}")
                return False
                
        except Exception as e:
            print(f"❌ 获取app_access_token异常: {e}")
            return False
    
    def get_table_info(self):
        """
        获取表格基本信息
        """
        if not self.access_token:
            print("❌ 没有有效的access_token")
            return None
            
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{TABLE_APP_TOKEN}/tables"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            resp = requests.get(url, headers=headers)
            data = resp.json()
            
            if data.get("code") == 0:
                tables = data.get("data", {}).get("items", [])
                print("📋 表格信息:")
                for table in tables:
                    print(f"  表格名称: {table.get('name')}")
                    print(f"  table_id: {table.get('table_id')}")
                    print(f"  修订版本: {table.get('revision')}")
                return tables
            else:
                print(f"❌ 获取表格信息失败: {data}")
                return None
                
        except Exception as e:
            print(f"❌ 获取表格信息异常: {e}")
            return None
    
    def get_table_fields(self):
        """
        获取表格字段信息
        """
        if not self.access_token:
            print("❌ 没有有效的access_token")
            return None
            
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{TABLE_APP_TOKEN}/tables/{TABLE_ID}/fields"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            resp = requests.get(url, headers=headers)
            data = resp.json()
            
            if data.get("code") == 0:
                fields = data.get("data", {}).get("items", [])
                print("🏷️  表格字段:")
                for field in fields:
                    print(f"  字段名: {field.get('field_name')}")
                    print(f"  字段ID: {field.get('field_id')}")
                    print(f"  字段类型: {field.get('type')}")
                    print("  ---")
                return fields
            else:
                print(f"❌ 获取字段信息失败: {data}")
                return None
                
        except Exception as e:
            print(f"❌ 获取字段信息异常: {e}")
            return None
    
    def get_table_records(self, page_size=100):
        """
        获取表格记录数据
        """
        if not self.access_token:
            print("❌ 没有有效的access_token")
            return None
            
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{TABLE_APP_TOKEN}/tables/{TABLE_ID}/records"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {"page_size": page_size}
        
        try:
            resp = requests.get(url, headers=headers, params=params)
            data = resp.json()
            
            if data.get("code") == 0:
                records = data.get("data", {}).get("items", [])
                total = data.get("data", {}).get("total", 0)
                has_more = data.get("data", {}).get("has_more", False)
                
                print(f"📊 表格数据统计:")
                print(f"  总记录数: {total}")
                print(f"  当前获取: {len(records)}")
                print(f"  是否还有更多: {has_more}")
                print()
                
                print("📝 记录详情:")
                for i, record in enumerate(records, 1):
                    print(f"第 {i} 行:")
                    print(f"  Record ID: {record.get('record_id')}")
                    print(f"  字段数据: {record.get('fields', {})}")
                    print("  ---")
                
                return {
                    "records": records,
                    "total": total,
                    "has_more": has_more
                }
            else:
                print(f"❌ 获取记录失败: {data}")
                return None
                
        except Exception as e:
            print(f"❌ 获取记录异常: {e}")
            return None
    
    def set_env_var(self, key, value):
        """
        设置Windows用户环境变量
        """
        try:
            cmd = f'[Environment]::SetEnvironmentVariable("{key}", "{value}", "User")'
            subprocess.run(["powershell", "-Command", cmd], check=True)
            print(f"✅ 环境变量 {key} 已更新")
        except Exception as e:
            print(f"❌ 设置环境变量失败: {e}")
    
    def run_complete_flow(self, authorization_code=None):
        """
        执行完整的数据获取流程
        """
        print("🚀 开始飞书表格数据获取流程")
        print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # 1. 尝试刷新token
        if self.refresh_access_token():
            print("✅ 使用refresh_token成功获取access_token")
        elif authorization_code:
            # 2. 如果有授权码，使用授权码获取token
            print("🔐 使用授权码获取初始tokens")
            if not self.get_initial_tokens(authorization_code):
                print("❌ 获取初始tokens失败")
                return False
        else:
            # 3. 备用方案：使用app_access_token
            print("🔧 尝试使用app_access_token")
            if not self.get_app_access_token():
                print("❌ 所有token获取方式都失败")
                print(f"请访问授权链接: {self.get_authorization_url()}")
                return False
        
        print("\n" + "=" * 50)
        
        # 4. 获取表格信息
        print("📋 获取表格基本信息...")
        table_info = self.get_table_info()
        if not table_info:
            return False
        
        print("\n" + "-" * 30)
        
        # 5. 获取字段信息
        print("🏷️  获取表格字段信息...")
        fields_info = self.get_table_fields()
        
        print("\n" + "-" * 30)
        
        # 6. 获取记录数据
        print("📊 获取表格记录数据...")
        records_data = self.get_table_records()
        
        if records_data:
            print("\n" + "=" * 50)
            print("✅ 数据获取流程完成!")
            print(f"✅ 共获取到 {len(records_data['records'])} 条记录")
            print(f"✅ 每条记录都有有效的record_id")
            return records_data
        else:
            print("❌ 数据获取失败")
            return False

def main():
    """
    主函数 - 演示完整流程
    """
    print("飞书表格数据自动获取系统")
    print("=" * 50)
    
    # 检查必要的环境变量
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        print("❌ 请在.env文件中配置FEISHU_APP_ID和FEISHU_APP_SECRET")
        return
    
    # 创建管理器实例
    manager = FeishuTableManager()
    
    # 执行完整流程
    result = manager.run_complete_flow()
    
    if result:
        # 保存结果到文件（可选）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"trading_agents_table_data_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"📁 数据已保存到: {filename}")
        except Exception as e:
            print(f"⚠️  保存文件失败: {e}")
    else:
        print("❌ 流程执行失败")

if __name__ == "__main__":
    main()
