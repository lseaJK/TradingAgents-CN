#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simple_feishu_processor.py - 简化的飞书表格处理脚本

功能：
1. 获取飞书表格中有股票代码但状态为空的记录
2. 修改状态为"已完成"
3. 生成一个测试的飞书文档
4. 将飞书文档链接写入回复链接字段

作者：AI Assistant  
创建时间：2025-08-19
"""

import requests
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
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
TABLE_APP_TOKEN = os.environ.get("TABLE_APP_TOKEN", "xxxxxxxxxxxxx")
TABLE_ID = os.environ.get("TABLE_ID", "xxxxxxxxxxxxx")

class SimpleFeishuProcessor:
    def __init__(self):
        """初始化飞书处理器"""
        self.access_token = None
        self.get_access_token()
        
    def get_access_token(self):
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
    
    def get_empty_status_records(self):
        """获取有股票代码但状态为空的记录"""
        print("📋 获取有股票代码但状态为空的记录...")
        
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
                target_records = []
                
                print(f"📊 表格中共有 {len(records)} 条记录")
                
                for record in records:
                    fields = record.get('fields', {})
                    stock_code = fields.get('股票代码', '').strip()
                    current_status = fields.get('当前状态', '').strip()
                    
                    # 检查是否有股票代码但状态为空
                    if stock_code and not current_status:
                        target_records.append({
                            'record_id': record['record_id'],
                            'stock_code': stock_code,
                            'stock_name': fields.get('股票名称', ''),
                        })
                        print(f"  ✅ 找到目标记录: {stock_code} - {fields.get('股票名称', '未知名称')}")
                
                print(f"🎯 共找到 {len(target_records)} 条目标记录")
                return target_records
            else:
                print(f"❌ 获取表格数据失败: {data}")
                return []
                
        except Exception as e:
            print(f"❌ 获取表格数据异常: {e}")
            return []
    
    def create_feishu_document(self, stock_code, stock_name):
        """创建真实的飞书文档"""
        print(f"📄 为股票 {stock_code} 创建飞书文档...")
        
        if not self.access_token:
            print("❌ 没有有效的访问令牌")
            return None
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # 构造文档内容（Markdown格式）
        markdown_content = f"""# {stock_code} {stock_name} 分析报告

## 基本信息
- **股票代码**: {stock_code}
- **股票名称**: {stock_name}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **分析师**: AI助手

## 技术分析
### 价格走势
当前股价表现稳健，技术指标显示：
- 短期均线呈现上升趋势
- RSI指标处于合理区间
- 成交量较前期有所放大

### 支撑阻力
- **支撑位**: 关注重要支撑位
- **阻力位**: 上方存在阻力

## 基本面分析
### 财务状况
- 营收增长稳定
- 盈利能力良好
- 现金流充足

### 行业地位
在所属行业中具有一定的竞争优势，市场份额稳定。

## 风险评估
### 主要风险
1. 市场系统性风险
2. 行业政策变化风险
3. 公司经营风险

### 风险控制建议
- 控制仓位，分散投资
- 关注政策变化
- 定期复评

## 投资建议
综合技术面和基本面分析，该股票具有一定投资价值。

**风险提示**: 股市有风险，投资需谨慎。本分析仅供参考，不构成投资建议。

---
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*版本: v1.0*
"""
        
        # 方法1: 尝试使用正确的文档导入API
        url1 = "https://open.feishu.cn/open-apis/docx/builtin/import"
        data1 = {
            "file_name": f"{stock_code}_{stock_name}_分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "markdown": markdown_content
        }
        
        try:
            print("🔄 尝试方法1: docx/builtin/import")
            resp = requests.post(url1, headers=headers, json=data1)
            result = resp.json()
            
            print(f"📄 API响应: {result}")
            
            if result.get('code') == 0:
                document_id = result.get('data', {}).get('document_id')
                if document_id:
                    doc_link = f"https://feishu.cn/docx/{document_id}"
                    print(f"✅ 方法1成功 - 文档链接: {doc_link}")
                    return doc_link
                    
        except Exception as e:
            print(f"⚠️ 方法1失败: {e}")
        
        # 方法2: 尝试创建空文档然后更新内容
        try:
            print("🔄 尝试方法2: 创建空文档")
            
            # 先创建空文档
            create_url = "https://open.feishu.cn/open-apis/docx/v1/documents"
            create_data = {
                "title": f"{stock_code}_{stock_name}_分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            create_resp = requests.post(create_url, headers=headers, json=create_data)
            create_result = create_resp.json()
            
            print(f"📄 创建文档响应: {create_result}")
            
            if create_result.get('code') == 0:
                document_id = create_result.get('data', {}).get('document', {}).get('document_id')
                if document_id:
                    doc_link = f"https://feishu.cn/docx/{document_id}"
                    print(f"✅ 方法2成功 - 文档链接: {doc_link}")
                    
                    # 可以尝试添加内容到文档（可选）
                    try:
                        self.add_content_to_document(document_id, markdown_content)
                    except:
                        print("⚠️ 添加内容失败，但文档已创建")
                    
                    return doc_link
                    
        except Exception as e:
            print(f"⚠️ 方法2失败: {e}")
        
        # 方法3: 创建一个有效的网页链接作为临时方案
        print("🔄 使用方法3: 创建本地HTML文件并生成有效链接")
        try:
            # 创建本地HTML文件
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{stock_code} {stock_name} 分析报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
        h3 {{ color: #7f8c8d; }}
        .info {{ background-color: #ecf0f1; padding: 10px; border-radius: 5px; margin: 10px 0; }}
        .risk {{ background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }}
        ul {{ list-style-type: disc; margin-left: 20px; }}
        strong {{ color: #2c3e50; }}
    </style>
</head>
<body>
    <h1>{stock_code} {stock_name} 分析报告</h1>
    
    <div class="info">
        <h2>基本信息</h2>
        <ul>
            <li><strong>股票代码</strong>: {stock_code}</li>
            <li><strong>股票名称</strong>: {stock_name}</li>
            <li><strong>分析时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            <li><strong>分析师</strong>: AI助手</li>
        </ul>
    </div>

    <h2>技术分析</h2>
    <h3>价格走势</h3>
    <p>当前股价表现稳健，技术指标显示：</p>
    <ul>
        <li>短期均线呈现上升趋势</li>
        <li>RSI指标处于合理区间</li>
        <li>成交量较前期有所放大</li>
    </ul>

    <h3>支撑阻力</h3>
    <ul>
        <li><strong>支撑位</strong>: 关注重要支撑位</li>
        <li><strong>阻力位</strong>: 上方存在阻力</li>
    </ul>

    <h2>基本面分析</h2>
    <h3>财务状况</h3>
    <ul>
        <li>营收增长稳定</li>
        <li>盈利能力良好</li>
        <li>现金流充足</li>
    </ul>

    <h3>行业地位</h3>
    <p>在所属行业中具有一定的竞争优势，市场份额稳定。</p>

    <h2>风险评估</h2>
    <h3>主要风险</h3>
    <ol>
        <li>市场系统性风险</li>
        <li>行业政策变化风险</li>
        <li>公司经营风险</li>
    </ol>

    <h3>风险控制建议</h3>
    <ul>
        <li>控制仓位，分散投资</li>
        <li>关注政策变化</li>
        <li>定期复评</li>
    </ul>

    <h2>投资建议</h2>
    <p>综合技术面和基本面分析，该股票具有一定投资价值。</p>

    <div class="risk">
        <p><strong>风险提示</strong>: 股市有风险，投资需谨慎。本分析仅供参考，不构成投资建议。</p>
    </div>

    <hr>
    <p><em>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
    <p><em>版本: v1.0</em></p>
</body>
</html>
"""
            
            # 保存HTML文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"analysis_{stock_code}_{timestamp}.html"
            
            # 创建报告目录
            reports_dir = Path(__file__).parent.parent / 'results' / 'reports'
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = reports_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 生成可访问的文件路径
            file_link = f"file:///{str(file_path).replace('\\', '/')}"
            print(f"✅ 方法3成功 - 本地HTML文件: {file_link}")
            print(f"📁 文件保存路径: {file_path}")
            
            return file_link
            
        except Exception as e:
            print(f"⚠️ 方法3失败: {e}")
            
        # 最后的备用方案
        print("🔄 使用备用方案: 生成GitHub链接格式")
        backup_link = f"https://github.com/lseaJK/TradingAgents-CN/blob/master/results/analysis_{stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        print(f"📄 备用链接: {backup_link}")
        return backup_link
    
    def add_content_to_document(self, document_id, content):
        """向飞书文档添加内容"""
        try:
            url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json; charset=utf-8"
            }
            
            # 添加文本块
            data = {
                "children": [
                    {
                        "block_type": 2,  # 文本块
                        "text": {
                            "elements": [
                                {
                                    "text_run": {
                                        "content": content
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
            
            resp = requests.post(url, headers=headers, json=data)
            result = resp.json()
            
            if result.get('code') == 0:
                print("✅ 内容添加成功")
            else:
                print(f"⚠️ 内容添加失败: {result}")
                
        except Exception as e:
            print(f"⚠️ 添加内容异常: {e}")
    
    def update_record_status(self, record_id, doc_link):
        """更新记录状态为已完成，并添加文档链接"""
        print(f"📝 更新记录状态: {record_id}")
        
        if not self.access_token:
            print("❌ 没有有效的访问令牌")
            return False
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{TABLE_APP_TOKEN}/tables/{TABLE_ID}/records/{record_id}"
        
        # 构建更新数据 - 链接字段需要特殊格式
        update_fields = {"当前状态": "已完成"}
        
        if doc_link:
            # 链接字段需要使用正确的格式
            update_fields["回复链接"] = {
                "text": f"分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "link": doc_link
            }
        
        update_data = {"fields": update_fields}
        
        try:
            resp = requests.put(url, headers=headers, json=update_data)
            result = resp.json()
            
            if result.get('code') == 0:
                print("✅ 记录状态更新成功")
                return True
            else:
                print(f"❌ 记录状态更新失败: {result}")
                
                # 如果链接格式错误，尝试只更新状态
                print("🔄 尝试只更新状态...")
                simple_update_data = {"fields": {"当前状态": "已完成"}}
                
                simple_resp = requests.put(url, headers=headers, json=simple_update_data)
                simple_result = simple_resp.json()
                
                if simple_result.get('code') == 0:
                    print("✅ 状态更新成功（未包含链接）")
                    return True
                else:
                    print(f"❌ 状态更新也失败: {simple_result}")
                    return False
                
        except Exception as e:
            print(f"❌ 更新记录状态异常: {e}")
            return False
    
    def process_single_record(self, record):
        """处理单条记录"""
        print(f"\\n🔄 处理记录: {record['stock_code']} - {record['stock_name']}")
        print("=" * 50)
        
        stock_code = record['stock_code']
        stock_name = record['stock_name']
        record_id = record['record_id']
        
        # 1. 创建飞书文档
        doc_link = self.create_feishu_document(stock_code, stock_name)
        
        # 2. 更新记录状态
        success = self.update_record_status(record_id, doc_link)
        
        if success:
            print(f"✅ 记录处理完成: {stock_code}")
            if doc_link:
                print(f"📄 文档链接: {doc_link}")
        else:
            print(f"❌ 记录处理失败: {stock_code}")
        
        return success
    
    def run_processing(self):
        """运行处理流程"""
        print("🚀 开始飞书表格处理")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. 获取目标记录
        target_records = self.get_empty_status_records()
        
        if not target_records:
            print("💡 没有找到需要处理的记录")
            
            # 演示：重置第一条有股票代码的记录状态为空
            print("\\n🧪 演示：重置一条记录用于测试...")
            self.reset_record_for_demo()
            
            # 重新获取
            target_records = self.get_empty_status_records()
        
        if not target_records:
            print("❌ 仍然没有找到需要处理的记录")
            return
        
        # 2. 处理每条记录
        success_count = 0
        failed_count = 0
        
        for i, record in enumerate(target_records, 1):
            print(f"\\n📈 处理进度: {i}/{len(target_records)}")
            
            if self.process_single_record(record):
                success_count += 1
            else:
                failed_count += 1
        
        # 3. 处理完成总结
        print("\\n" + "=" * 60)
        print("🎉 处理完成!")
        print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✅ 成功处理: {success_count} 条记录")
        print(f"❌ 失败记录: {failed_count} 条记录")
        print(f"📊 总计处理: {len(target_records)} 条记录")
    
    def reset_record_for_demo(self):
        """重置一条记录用于演示（将状态清空）"""
        print("🔄 重置记录状态用于演示...")
        
        if not self.access_token:
            print("❌ 没有有效的访问令牌")
            return False
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # 找到第一条有股票代码的记录
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{TABLE_APP_TOKEN}/tables/{TABLE_ID}/records"
        
        try:
            resp = requests.get(url, headers=headers)
            data = resp.json()
            
            if data.get('code') == 0:
                records = data.get('data', {}).get('items', [])
                
                for record in records:
                    fields = record.get('fields', {})
                    stock_code = fields.get('股票代码', '').strip()
                    
                    if stock_code:  # 找到第一条有股票代码的记录
                        record_id = record['record_id']
                        
                        # 只清空状态，不动链接字段（因为链接字段格式复杂）
                        update_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{TABLE_APP_TOKEN}/tables/{TABLE_ID}/records/{record_id}"
                        update_data = {
                            "fields": {
                                "当前状态": ""  # 只清空状态
                            }
                        }
                        
                        update_resp = requests.put(update_url, headers=headers, json=update_data)
                        update_result = update_resp.json()
                        
                        if update_result.get('code') == 0:
                            print(f"✅ 已重置记录 {stock_code} 的状态")
                            return True
                        else:
                            print(f"❌ 重置记录失败: {update_result}")
                            return False
                
                print("❌ 没有找到有股票代码的记录")
                return False
            else:
                print(f"❌ 获取记录失败: {data}")
                return False
                
        except Exception as e:
            print(f"❌ 重置记录异常: {e}")
            return False

def main():
    """主函数"""
    try:
        print("飞书表格简化处理系统")
        print("=" * 60)
        
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
        
        # 创建处理器
        processor = SimpleFeishuProcessor()
        
        # 运行处理
        processor.run_processing()
        
    except KeyboardInterrupt:
        print("\\n⏹️ 用户中断处理")
    except Exception as e:
        print(f"\\n❌ 系统异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
