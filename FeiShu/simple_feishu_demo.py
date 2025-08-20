#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simple_feishu_demo.py - 简单的飞书表格自动化演示

功能：
1. 从飞书表格获取待处理的股票代码
2. 模拟分析过程（生成简单的分析报告）
3. 更新飞书表格状态和结果

作者：AI Assistant  
创建时间：2025-08-19
"""

import requests
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import time
import json

# 加载环境变量
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# 同时加载主目录的.env文件
main_env_path = Path(__file__).parent.parent / 'TradingAgents-CN-main' / '.env'
load_dotenv(main_env_path)

# 飞书配置
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET")
TABLE_APP_TOKEN = os.environ.get("TABLE_APP_TOKEN", "xxxxxxxxxxxx")
TABLE_ID = os.environ.get("TABLE_ID", "xxxxxxxxxx")

class SimpleFeishuDemo:
    def __init__(self):
        """初始化飞书表格管理器"""
        self.access_token = None
        self.get_feishu_access_token()
        
    def get_feishu_access_token(self):
        """获取飞书访问令牌"""
        try:
            print("🔐 获取飞书访问令牌...")
            
            url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/"
            body = {
                "app_id": FEISHU_APP_ID,
                "app_secret": FEISHU_APP_SECRET
            }
            
            resp = requests.post(url, json=body)
            data = resp.json()
            
            if data.get("app_access_token"):
                self.access_token = data["app_access_token"]
                print("✅ 飞书访问令牌获取成功")
            else:
                raise Exception(f"获取令牌失败: {data}")
                
        except Exception as e:
            print(f"❌ 获取飞书访问令牌失败: {e}")
            raise
    
    def get_pending_tasks(self):
        """从飞书表格获取待处理任务"""
        print("📋 获取飞书表格中的待处理任务...")
        
        if not self.access_token:
            print("❌ 没有有效的访问令牌")
            return []
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{TABLE_APP_TOKEN}/tables/{TABLE_ID}/records"
        
        try:
            resp = requests.get(url, headers=headers)
            data = resp.json()
            
            if data.get('code') == 0:
                records = data.get('data', {}).get('items', [])
                pending_tasks = []
                
                print(f"📊 表格中共有 {len(records)} 条记录")
                
                for record in records:
                    fields = record.get('fields', {})
                    stock_code = fields.get('股票代码', '').strip()
                    current_status = fields.get('当前状态', '').strip()
                    
                    # 检查是否为待处理任务（状态为空或为'待处理'）
                    if stock_code and (not current_status or current_status in ['待处理', '令牌测试完成']):
                        pending_tasks.append({
                            'record_id': record['record_id'],
                            'stock_code': stock_code,
                            'stock_name': fields.get('股票名称', ''),
                            'current_status': current_status
                        })
                        print(f"  ✅ 发现待处理任务: {stock_code} - {fields.get('股票名称', '未知名称')}")
                
                print(f"🎯 共发现 {len(pending_tasks)} 个待处理任务")
                return pending_tasks
            else:
                print(f"❌ 获取表格数据失败: {data}")
                return []
                
        except Exception as e:
            print(f"❌ 获取表格数据异常: {e}")
            return []
    
    def update_task_status(self, record_id, status, reply_link=None):
        """更新飞书表格中任务的状态"""
        print(f"📝 更新任务状态: {record_id} -> {status}")
        
        if not self.access_token:
            print("❌ 没有有效的访问令牌")
            return False
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{TABLE_APP_TOKEN}/tables/{TABLE_ID}/records/{record_id}"
        
        # 构建更新数据
        update_fields = {"当前状态": status}
        if reply_link:
            update_fields["回复链接"] = reply_link
            
        update_data = {"fields": update_fields}
        
        try:
            resp = requests.put(url, headers=headers, json=update_data)
            result = resp.json()
            
            if result.get('code') == 0:
                print(f"✅ 状态更新成功: {status}")
                return True
            else:
                print(f"❌ 状态更新失败: {result}")
                return False
                
        except Exception as e:
            print(f"❌ 状态更新异常: {e}")
            return False
    
    def simulate_stock_analysis(self, stock_code, stock_name=""):
        """模拟股票分析（替代TradingAgents）"""
        print(f"🤖 开始模拟分析股票: {stock_code} ({stock_name})")
        
        # 模拟分析过程（3秒延迟）
        print("📊 正在进行技术面分析...")
        time.sleep(1)
        print("📈 正在进行基本面分析...")
        time.sleep(1)
        print("⚖️ 正在进行风险评估...")
        time.sleep(1)
        
        # 生成模拟分析报告
        analysis_report = f"""
股票代码：{stock_code}
股票名称：{stock_name}
分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== 技术面分析 ===
• 当前价格水平：处于中期上升趋势中
• 技术指标：RSI指标显示不过热，MACD呈现多头排列
• 成交量分析：近期成交量有所放大，资金活跃度提升
• 支撑阻力：关键支撑位在XX元，阻力位在XX元

=== 基本面分析 ===
• 财务状况：公司财务结构稳健，盈利能力持续
• 行业地位：在细分领域具有一定竞争优势
• 成长性：业务拓展稳步推进，未来增长可期
• 估值水平：当前估值处于合理区间

=== 风险评估 ===
• 市场风险：受整体市场波动影响
• 行业风险：关注行业政策变化和竞争加剧
• 公司风险：经营风险相对可控
• 流动性风险：股票流动性良好

=== 投资建议 ===
综合考虑技术面和基本面因素，该股票具有一定的投资价值。
建议投资者根据自身风险承受能力进行配置。

风险提示：股市有风险，投资需谨慎。以上分析仅供参考，不构成投资建议。
        """
        
        print("✅ 模拟分析完成")
        
        # 保存分析结果到文件
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"analysis_{stock_code}_{timestamp}.txt"
            
            # 创建保存目录
            save_dir = Path(__file__).parent.parent / 'results' / stock_code / datetime.now().strftime('%Y-%m-%d')
            save_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = save_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(analysis_report)
            
            print(f"📁 分析结果已保存: {file_path}")
            
            return {
                "success": True,
                "report": analysis_report,
                "file_path": str(file_path)
            }
            
        except Exception as e:
            print(f"⚠️ 保存文件失败: {e}")
            return {
                "success": True,
                "report": analysis_report,
                "file_path": None
            }
    
    def process_single_task(self, task):
        """处理单个任务"""
        print(f"\\n🔄 处理任务: {task['stock_code']} - {task['stock_name']}")
        print("=" * 60)
        
        record_id = task['record_id']
        stock_code = task['stock_code']
        stock_name = task['stock_name']
        
        # 1. 更新状态为"分析中"
        self.update_task_status(record_id, "分析中")
        
        try:
            # 2. 运行模拟分析
            analysis_result = self.simulate_stock_analysis(stock_code, stock_name)
            
            if analysis_result["success"]:
                # 3. 分析成功，更新状态为"已完成"并添加文件链接
                file_path = analysis_result.get("file_path")
                reply_link = f"file://{file_path}" if file_path else None
                
                self.update_task_status(record_id, "已完成", reply_link)
                
                print(f"✅ 任务完成: {stock_code}")
                return True
            else:
                # 4. 分析失败，更新状态为"分析失败"
                self.update_task_status(record_id, "分析失败")
                
                print(f"❌ 任务失败: {stock_code}")
                return False
                
        except Exception as e:
            # 5. 异常处理
            print(f"❌ 处理任务异常: {e}")
            self.update_task_status(record_id, f"处理异常: {str(e)}")
            return False
    
    def run_demo(self):
        """运行演示"""
        print("🚀 开始飞书表格自动化演示")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # 1. 获取待处理任务
        pending_tasks = self.get_pending_tasks()
        
        if not pending_tasks:
            print("💡 没有待处理的任务")
            
            # 演示：添加一个测试任务
            print("\\n🧪 演示：创建一个测试任务...")
            self.create_demo_task()
            
            # 重新获取任务
            pending_tasks = self.get_pending_tasks()
        
        if not pending_tasks:
            print("❌ 仍然没有待处理任务")
            return
        
        # 2. 处理每个任务
        success_count = 0
        failed_count = 0
        
        for i, task in enumerate(pending_tasks, 1):
            print(f"\\n📈 处理进度: {i}/{len(pending_tasks)}")
            
            if self.process_single_task(task):
                success_count += 1
            else:
                failed_count += 1
            
            # 任务间延迟
            if i < len(pending_tasks):
                print("⏱️ 等待 2 秒后继续下一个任务...")
                time.sleep(2)
        
        # 3. 处理完成总结
        print("\\n" + "=" * 70)
        print("🎉 演示处理完成!")
        print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✅ 成功处理: {success_count} 个任务")
        print(f"❌ 失败任务: {failed_count} 个任务")
        print(f"📊 总计处理: {len(pending_tasks)} 个任务")
    
    def create_demo_task(self):
        """创建一个演示任务"""
        print("🧪 创建演示任务...")
        
        if not self.access_token:
            print("❌ 没有有效的访问令牌")
            return False
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{TABLE_APP_TOKEN}/tables/{TABLE_ID}/records"
        
        # 创建演示任务数据
        demo_data = {
            "fields": {
                "股票代码": "600089",
                "股票名称": "特变电工",
                "请求日期": int(datetime.now().timestamp() * 1000),  # 时间戳（毫秒）
                "当前状态": "待处理"
            }
        }
        
        try:
            resp = requests.post(url, headers=headers, json=demo_data)
            result = resp.json()
            
            if result.get('code') == 0:
                print("✅ 演示任务创建成功")
                return True
            else:
                print(f"❌ 演示任务创建失败: {result}")
                return False
                
        except Exception as e:
            print(f"❌ 创建演示任务异常: {e}")
            return False

def main():
    """主函数"""
    try:
        print("飞书表格自动化演示系统")
        print("=" * 70)
        
        # 检查环境变量
        required_vars = ["FEISHU_APP_ID", "FEISHU_APP_SECRET"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            print(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
            print("请在.env文件中配置这些变量")
            return
        
        print(f"🔧 FEISHU_APP_ID: {FEISHU_APP_ID}")
        print(f"🔧 TABLE_APP_TOKEN: {TABLE_APP_TOKEN}")
        print(f"🔧 TABLE_ID: {TABLE_ID}")
        
        # 创建演示处理器
        demo = SimpleFeishuDemo()
        
        # 运行演示
        demo.run_demo()
        
    except KeyboardInterrupt:
        print("\\n⏹️ 用户中断处理")
    except Exception as e:
        print(f"\\n❌ 系统异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
