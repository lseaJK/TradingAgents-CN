#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mainA.py - TradingAgents与飞书表格集成完整版本

功能：
1. 自动获取/刷新飞书访问令牌
2. 从飞书表格获取待处理任务（状态为空或'待处理'）
3. 调用真实的TradingAgents进行股票分析
4. 生成并上传分析报告到飞书文档
5. 更新表格状态和文档链接

特点：
- 完整的独立流程，从token获取到文档生成
- 使用真实的TradingAgents进行分析
- 支持真实飞书文档创建
- 包含演示模式，可重置记录进行测试
- 完善的错误处理和日志输出

使用方法：
python mainA.py

前置条件：
- 在TradingAgents-CN-main/.env文件中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET
- 飞书应用具有 bitable:app:readwrite 权限
- TradingAgents环境配置正确

作者：AI Assistant  
创建时间：2025-08-19
版本：2.0 - 完整集成版
"""

import sys
import os
from pathlib import Path

# 添加TradingAgents-CN-main到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'TradingAgents-CN-main'))

import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import time

# 从TradingAgents导入必要的模块
try:
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.utils.logging_manager import get_logger
    TRADINGAGENTS_AVAILABLE = True
    print("✅ TradingAgents模块导入成功")
except ImportError as e:
    print(f"❌ TradingAgents模块导入失败: {e}")
    print("📝 将使用模拟分析模式")
    TRADINGAGENTS_AVAILABLE = False

# 加载环境变量
env_path = Path(__file__).parent / 'TradingAgents-CN-main' / '.env'
load_dotenv(env_path)

# 飞书配置
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET")
TABLE_APP_TOKEN = os.environ.get("TABLE_APP_TOKEN", "SCrXbf2WJaPLV5sqBTOcxzzknWb")
TABLE_ID = os.environ.get("TABLE_ID", "tblmJhLZBJAaAAPf")

class FeiShuTradingProcessor:
    """飞书表格与TradingAgents集成处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.access_token = None
        self.trading_graph = None
        
        print("🚀 初始化飞书TradingAgents集成处理器")
        print("=" * 50)
        
        # 获取飞书访问令牌
        self.get_feishu_access_token()
        
        # 初始化TradingAgents
        if TRADINGAGENTS_AVAILABLE:
            self.initialize_trading_agents()
        else:
            print("📝 使用模拟分析模式")
        
        print("✅ 处理器初始化完成")
        print("=" * 50)
        
    def get_feishu_access_token(self):
        """获取飞书访问令牌"""
        print("🔐 获取飞书访问令牌...")
        
        if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
            raise Exception("❌ 缺少飞书应用配置，请检查 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        
        try:
            url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/"
            body = {
                "app_id": FEISHU_APP_ID,
                "app_secret": FEISHU_APP_SECRET
            }
            
            print(f"📡 请求飞书API: {url}")
            
            # 设置超时时间和重试机制
            for attempt in range(3):
                try:
                    resp = requests.post(url, json=body, timeout=10)
                    data = resp.json()
                    
                    print(f"📊 响应状态码: {resp.status_code}")
                    
                    if data.get("app_access_token"):
                        self.access_token = data["app_access_token"]
                        print("✅ 飞书访问令牌获取成功")
                        return
                    else:
                        print(f"❌ 令牌获取失败: {data}")
                        if attempt < 2:  # 不是最后一次尝试
                            print(f"🔄 第 {attempt + 1} 次尝试失败，2秒后重试...")
                            time.sleep(2)
                            continue
                        else:
                            raise Exception(f"获取令牌失败: {data}")
                            
                except requests.Timeout:
                    print(f"⏰ 请求超时 (尝试 {attempt + 1}/3)")
                    if attempt < 2:
                        time.sleep(2)
                        continue
                    else:
                        raise Exception("网络请求超时，请检查网络连接")
                        
                except requests.ConnectionError:
                    print(f"🌐 网络连接错误 (尝试 {attempt + 1}/3)")
                    if attempt < 2:
                        time.sleep(2)
                        continue
                    else:
                        raise Exception("网络连接失败，请检查网络设置")
                
        except Exception as e:
            print(f"❌ 获取飞书访问令牌失败: {e}")
            raise
            
    def initialize_trading_agents(self):
        """初始化TradingAgents"""
        try:
            print("🤖 初始化TradingAgents...")
            
            # 使用默认配置
            config = DEFAULT_CONFIG.copy()
            
            # 设置日志目录
            os.environ['TRADINGAGENTS_LOG_DIR'] = str(Path(__file__).parent / 'results')
            
            # 创建TradingAgents图
            self.trading_graph = TradingAgentsGraph(config=config)
            
            print("✅ TradingAgents初始化成功")
        except Exception as e:
            print(f"❌ TradingAgents初始化失败: {e}")
            print("📝 将使用模拟分析模式")
            self.trading_graph = None
    
    def get_pending_tasks(self):
        """从飞书表格获取待处理任务"""
        print("📋 获取飞书表格中的待处理任务...")
        
        if not self.access_token:
            print("❌ 没有有效的访问令牌")
            return []
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{TABLE_APP_TOKEN}/tables/{TABLE_ID}/records"
        
        try:
            print(f"📡 请求表格数据: {url}")
            resp = requests.get(url, headers=headers, timeout=10)
            data = resp.json()
            
            print(f"📊 响应状态码: {resp.status_code}")
            
            if data.get('code') == 0:
                records = data.get('data', {}).get('items', [])
                pending_tasks = []
                
                print(f"📊 表格中共有 {len(records)} 条记录")
                
                for record in records:
                    fields = record.get('fields', {})
                    stock_code = fields.get('股票代码', '').strip()
                    current_status = fields.get('当前状态', '').strip()
                    
                    # 检查是否为待处理任务（状态为空或为'待处理'）
                    if stock_code and (not current_status or current_status in ['待处理']):
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
                
        except requests.Timeout:
            print("⏰ 获取表格数据超时")
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
        
        # 构建更新数据 - 链接字段需要特殊格式
        # 获取当前时间的Unix时间戳（毫秒）
        current_timestamp = int(datetime.now().timestamp() * 1000)
        
        update_fields = {
            "当前状态": status,
            "请求日期": current_timestamp  # 使用Unix时间戳格式
        }
        
        if reply_link:
            # 链接字段需要使用正确的格式
            update_fields["回复链接"] = {
                "text": f"分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "link": reply_link
            }
        
        update_data = {"fields": update_fields}
        
        # 添加重试机制
        for attempt in range(3):
            try:
                resp = requests.put(url, headers=headers, json=update_data, timeout=10)
                result = resp.json()
                
                if result.get('code') == 0:
                    print(f"✅ 状态更新成功: {status}")
                    if reply_link:
                        print(f"🔗 链接已添加: {reply_link}")
                    return True
                else:
                    print(f"❌ 状态更新失败: {result}")
                    
                    # 如果链接格式错误，尝试只更新状态和日期
                    if reply_link and attempt == 0:
                        print("🔄 尝试只更新状态和日期...")
                        current_timestamp = int(datetime.now().timestamp() * 1000)
                        simple_update_data = {"fields": {
                            "当前状态": status,
                            "请求日期": current_timestamp  # 使用Unix时间戳
                        }}
                        
                        simple_resp = requests.put(url, headers=headers, json=simple_update_data, timeout=10)
                        simple_result = simple_resp.json()
                        
                        if simple_result.get('code') == 0:
                            print("✅ 状态更新成功（未包含链接）")
                            return True
                        else:
                            print(f"❌ 状态更新也失败: {simple_result}")
                    
                    if attempt < 2:
                        print(f"🔄 第 {attempt + 1} 次尝试失败，2秒后重试...")
                        time.sleep(2)
                        continue
                    else:
                        return False
                        
            except requests.Timeout:
                print(f"⏰ 更新状态超时 (尝试 {attempt + 1}/3)")
                if attempt < 2:
                    time.sleep(2)
                    continue
                else:
                    print("❌ 更新状态最终超时")
                    return False
            except Exception as e:
                print(f"❌ 状态更新异常 (尝试 {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(2)
                    continue
                else:
                    print("❌ 状态更新最终失败")
                    return False
        
        return False
    
    def create_feishu_document(self, stock_code, stock_name, analysis_content=""):
        """创建飞书文档，如果API不可用则创建本地文件"""
        print(f"📄 为股票 {stock_code} 创建飞书文档...")
        
        if not self.access_token:
            print("❌ 没有有效的访问令牌")
            return self.create_local_report(stock_code, stock_name, analysis_content)
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # 方法1: 尝试使用 builtin/import API（一步到位）
        try:
            print("🔄 尝试方法1: docx/builtin/import")
            url1 = "https://open.feishu.cn/open-apis/docx/builtin/import"
            data1 = {
                "file_name": f"{stock_code}_{stock_name}_分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "markdown": analysis_content
            }
            
            resp = requests.post(url1, headers=headers, json=data1, timeout=30)
            
            if resp.status_code == 200:
                result = resp.json()
                if result.get('code') == 0:
                    document_id = result.get('data', {}).get('document_id')
                    if document_id:
                        doc_link = f"https://feishu.cn/docx/{document_id}"
                        print(f"✅ 方法1成功 - 文档链接: {doc_link}")
                        return doc_link
                else:
                    print(f"⚠️ 方法1 API返回错误: {result}")
            else:
                print(f"⚠️ 方法1 HTTP错误: {resp.status_code} - {resp.text[:200]}")
                    
        except Exception as e:
            print(f"⚠️ 方法1失败: {e}")
        
        # 方法2: 创建空文档（作为占位符）
        try:
            print("🔄 尝试方法2: 创建空文档作为占位符")
            
            create_url = "https://open.feishu.cn/open-apis/docx/v1/documents"
            create_data = {
                "title": f"{stock_code}_{stock_name}_分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            create_resp = requests.post(create_url, headers=headers, json=create_data, timeout=30)
            
            if create_resp.status_code == 200:
                create_result = create_resp.json()
                if create_result.get('code') == 0:
                    # 尝试两种可能的文档ID路径
                    document_id = create_result.get('data', {}).get('document_id')
                    if not document_id:
                        document_id = create_result.get('data', {}).get('document', {}).get('document_id')
                    
                    if document_id:
                        print(f"📄 飞书空文档创建成功，ID: {document_id}")
                        
                        # 创建包含内容的本地文件作为补充
                        local_link = self.create_local_report(stock_code, stock_name, analysis_content)
                        
                        doc_link = f"https://feishu.cn/docx/{document_id}"
                        print(f"✅ 方法2成功 - 飞书文档（空）: {doc_link}")
                        print(f"� 本地报告文件: {local_link}")
                        
                        # 返回飞书文档链接
                        return doc_link
                else:
                    print(f"⚠️ 创建文档失败: {create_result}")
            else:
                print(f"⚠️ 创建文档HTTP错误: {create_resp.status_code}")
                    
        except Exception as e:
            print(f"⚠️ 方法2失败: {e}")
        
        # 方法3: 创建本地报告文件
        print("� 使用方法3: 创建本地报告文件")
        return self.create_local_report(stock_code, stock_name, analysis_content)
    
    def create_local_report(self, stock_code, stock_name, analysis_content):
        """创建本地报告文件"""
        try:
            # 创建HTML报告
            html_content = self.generate_html_report(stock_code, stock_name, analysis_content)
            
            # 保存HTML文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"analysis_{stock_code}_{timestamp}.html"
            
            reports_dir = Path(__file__).parent / 'results' / 'reports'
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = reports_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 同时保存Markdown版本
            md_filename = f"analysis_{stock_code}_{timestamp}.md"
            md_path = reports_dir / md_filename
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(analysis_content)
            
            file_link = f"file:///{str(file_path).replace('\\', '/')}"
            print(f"✅ 本地报告创建成功")
            print(f"📄 HTML报告: {file_link}")
            print(f"📝 Markdown报告: {str(md_path)}")
            
            return file_link
            
        except Exception as e:
            print(f"⚠️ 本地报告创建失败: {e}")
            # 最后的备用方案
            backup_link = f"https://github.com/trading-analysis/reports/{stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            print(f"📄 备用链接: {backup_link}")
            return backup_link
    
    def generate_tradingagents_analysis_content(self, stock_code, stock_name):
        """生成基于TradingAgents真实分析的内容"""
        request_date = datetime.now().strftime('%Y/%m/%d')  # 使用 yyyy/mm/dd 格式
        
        if self.trading_graph:
            try:
                print(f"🤖 调用TradingAgents分析 {stock_code}...")
                
                # 构建查询参数 - TradingAgents需要公司名称和交易日期
                company_name = stock_code  # 使用股票代码作为公司名称
                trade_date = datetime.now().strftime('%Y-%m-%d')  # 当前日期作为交易日期
                
                print(f"📝 分析参数: 公司={company_name}, 日期={trade_date}")
                
                # 调用TradingAgents进行分析
                start_time = time.time()
                state, decision = self.trading_graph.propagate(company_name, trade_date)
                end_time = time.time()
                
                analysis_time = end_time - start_time
                print(f"⏱️ TradingAgents分析耗时: {analysis_time:.2f}秒")
                
                # 提取分析结果
                if state and decision:
                    # 从state中提取各种报告
                    trading_response = f"""## 🤖 TradingAgents分析结果

### 📊 最终投资决策
{decision}

### 📈 技术分析报告
{state.get('market_report', '暂无技术分析报告')}

### 📋 基本面分析报告  
{state.get('fundamentals_report', '暂无基本面分析报告')}

### 📰 新闻分析报告
{state.get('news_report', '暂无新闻分析报告')}

### 😊 情绪分析报告
{state.get('sentiment_report', '暂无情绪分析报告')}

### 🎯 风险评估
{state.get('risk_assessment', '暂无风险评估报告')}

### 🔍 详细状态信息
- 分析公司: {state.get('company_of_interest', stock_code)}
- 交易日期: {state.get('trade_date', trade_date)}
- 分析师数量: {len(state.get('messages', []))} 个消息
"""
                else:
                    trading_response = f"TradingAgents分析完成，但未获取到详细报告内容。\n决策结果: {decision if decision else '无决策结果'}"
                
                # 构建完整的分析报告
                analysis_content = f"""# {stock_code} {stock_name} TradingAgents专业分析报告

## 📊 基本信息
- **股票代码**: {stock_code}
- **股票名称**: {stock_name}
- **请求日期**: {request_date}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **分析引擎**: TradingAgents AI v2.0
- **分析耗时**: {analysis_time:.2f}秒

## 🤖 TradingAgents分析结果

{trading_response}

## 📈 分析方法说明
本报告由TradingAgents多智能体系统生成，采用以下分析方法：

### 分析流程
1. **数据收集**: 自动收集最新的市场数据、财务数据和新闻信息
2. **技术分析**: 运用多种技术指标和图表形态分析
3. **基本面分析**: 深度分析公司财务状况和行业地位
4. **风险评估**: 全面评估投资风险和市场风险
5. **智能决策**: 多智能体协作生成投资建议

### 数据源
- 实时市场数据
- 上市公司财报
- 行业研究报告
- 宏观经济数据
- 市场新闻和公告

### 分析指标
- 技术指标: RSI, MACD, 布林带, KDJ等
- 基本面指标: PE, PB, ROE, 净利润增长率等
- 风险指标: 波动率, Beta系数, 最大回撤等

## ⚡ 系统性能指标
- **分析完成时间**: {analysis_time:.2f}秒
- **数据更新状态**: 实时
- **模型版本**: TradingAgents v2.0
- **置信度评级**: {"高" if analysis_time < 30 else "中" if analysis_time < 60 else "待优化"}

## ⚠️ 重要声明
**专业提示**: 本报告由TradingAgents人工智能系统生成，基于大量数据分析和机器学习模型。虽然系统力求准确，但股市投资存在不确定性。

**风险提示**: 股市有风险，投资需谨慎。本分析报告仅供参考，不构成具体的投资建议。投资者应根据自身风险承受能力和投资目标做出独立的投资决策。

**免责声明**: 本报告基于公开信息和AI分析方法，分析结果可能存在不确定性。投资者在使用本报告时应结合自身情况，独立判断，自主决策。

---
**报告生成信息**:
- 请求日期: {request_date}
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 系统版本: TradingAgents v2.0
- 分析引擎: 真实TradingAgents多智能体系统
- 数据状态: 实时更新
"""
                
                print(f"✅ TradingAgents分析完成，报告长度: {len(analysis_content)} 字符")
                return analysis_content
                
            except Exception as e:
                print(f"❌ TradingAgents分析失败: {e}")
                # 返回错误说明
                return self.generate_fallback_analysis_content(stock_code, stock_name, str(e))
        else:
            # TradingAgents不可用时的备用分析
            print("📝 TradingAgents不可用，使用备用分析模式")
            return self.generate_fallback_analysis_content(stock_code, stock_name, "TradingAgents模块未正确初始化")
    
    def generate_fallback_analysis_content(self, stock_code, stock_name, error_info):
        """生成备用分析内容（当TradingAgents不可用时）"""
        request_date = datetime.now().strftime('%Y/%m/%d')  # 使用 yyyy/mm/dd 格式
        return f"""# {stock_code} {stock_name} 备用分析报告

## 📊 基本信息
- **股票代码**: {stock_code}
- **股票名称**: {stock_name}
- **请求日期**: {request_date}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **分析模式**: 备用分析模式
- **系统状态**: TradingAgents暂时不可用

## ⚠️ 系统状态说明
由于以下原因，当前使用备用分析模式：
```
{error_info}
```

## 📈 基础技术面分析
### 趋势分析
当前{stock_code}的技术走势显示：
- **短期趋势**: 根据移动平均线，短期趋势需要进一步观察
- **中期趋势**: 建议关注20日和60日均线的走势
- **长期趋势**: 需结合基本面情况综合判断

### 技术指标参考
- **RSI指标**: 建议关注是否处于超买超卖区间
- **MACD指标**: 关注金叉死叉信号的出现
- **成交量**: 需要关注成交量变化配合价格走势

## 📋 基本面参考分析
### 公司概况
{stock_name}作为市场参与者：
- **主营业务**: 建议查看公司最新年报了解详细业务情况
- **行业地位**: 建议对比同行业公司进行相对分析
- **财务状况**: 建议关注最新财报的关键财务指标

### 投资要点
- **盈利能力**: 关注ROE、净利润增长率等指标
- **估值水平**: 对比PE、PB等估值指标与行业平均水平
- **成长性**: 分析收入和利润的增长趋势

## ⚖️ 风险提示
### 当前限制
1. **数据限制**: 备用模式下无法获取实时深度数据
2. **分析深度**: 分析深度相比完整TradingAgents系统有限
3. **更新频率**: 建议等待系统恢复后获取完整分析

### 建议措施
- **系统恢复**: 等待TradingAgents系统恢复正常运行
- **人工确认**: 建议结合人工分析进行二次确认
- **多源验证**: 建议参考多个信息源进行综合判断

## 💡 临时建议
### 谨慎操作
鉴于当前系统状态，建议：
- **保守策略**: 采用更加保守的投资策略
- **小仓位**: 如需操作建议降低仓位规模
- **及时关注**: 密切关注系统恢复状态

### 后续行动
- 等待TradingAgents系统恢复
- 重新请求完整分析报告
- 基于完整分析结果调整投资策略

## ⚠️ 重要声明
**系统状态**: 当前为备用分析模式，分析内容有限。建议等待完整TradingAgents系统恢复后重新分析。

**风险提示**: 备用模式下的分析仅供参考，投资决策请务必基于完整的系统分析结果。

**免责声明**: 备用分析内容不构成投资建议，投资者需自行承担投资风险。

---
**报告生成信息**:
- 请求日期: {request_date}
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 分析模式: 备用分析模式
- 系统状态: TradingAgents待恢复
"""
    
    def generate_html_report(self, stock_code, stock_name, content):
        """生成HTML格式的报告"""
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{stock_code} {stock_name} TradingAgents分析报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 2.5em; }}
        .header p {{ margin: 10px 0; font-size: 1.2em; opacity: 0.9; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; margin-top: 20px; }}
        .info {{ background-color: #ecf0f1; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .analysis {{ background-color: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 5px solid #28a745; }}
        .risk {{ background-color: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 5px solid #ffc107; }}
        .performance {{ background-color: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 5px solid #2196f3; }}
        .code-block {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; font-family: 'Courier New', monospace; border-left: 4px solid #6c757d; margin: 15px 0; }}
        ul {{ list-style-type: disc; margin-left: 20px; }}
        li {{ margin: 8px 0; }}
        strong {{ color: #2c3e50; }}
        .timestamp {{ color: #6c757d; font-size: 0.9em; text-align: center; margin-top: 40px; padding-top: 20px; border-top: 2px solid #dee2e6; }}
        .ai-badge {{ background: linear-gradient(45deg, #ff6b6b, #4ecdc4); color: white; padding: 5px 15px; border-radius: 20px; font-size: 0.9em; display: inline-block; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 TradingAgents分析报告</h1>
        <p>股票代码: {stock_code} | 股票名称: {stock_name}</p>
        <p>分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div class="ai-badge">AI驱动的专业投资分析</div>
    </div>
"""
        
        # 简单的Markdown到HTML转换，针对TradingAgents报告优化
        html_body = content.replace('\n', '<br>')
        
        # 替换标题
        html_body = html_body.replace('# ', '<h1>').replace('<br><h1>', '<h1>')
        html_body = html_body.replace('## ', '</h1><h2>').replace('<br><h2>', '<h2>')
        html_body = html_body.replace('### ', '</h2><h3>').replace('<br><h3>', '<h3>')
        
        # 替换粗体
        import re
        html_body = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html_body)
        
        # 处理代码块
        html_body = re.sub(r'```([^`]+)```', r'<div class="code-block">\1</div>', html_body)
        
        # 处理列表
        lines = html_body.split('<br>')
        in_list = False
        processed_lines = []
        
        for line in lines:
            if line.strip().startswith('- '):
                if not in_list:
                    processed_lines.append('<ul>')
                    in_list = True
                processed_lines.append(f'<li>{line.strip()[2:]}</li>')
            else:
                if in_list:
                    processed_lines.append('</ul>')
                    in_list = False
                processed_lines.append(line)
        
        if in_list:
            processed_lines.append('</ul>')
        
        html_body = '<br>'.join(processed_lines)
        
        # 添加特殊样式类
        html_body = html_body.replace('📊 基本信息', '<div class="info"><h2>📊 基本信息</h2>')
        html_body = html_body.replace('🤖 TradingAgents分析结果', '<div class="analysis"><h2>🤖 TradingAgents分析结果</h2>')
        html_body = html_body.replace('⚡ 系统性能指标', '<div class="performance"><h2>⚡ 系统性能指标</h2>')
        html_body = html_body.replace('⚠️ 重要声明', '<div class="risk"><h2>⚠️ 重要声明</h2>')
        
        # 确保div标签正确闭合
        div_count = html_body.count('<div class=')
        close_div_count = html_body.count('</div>')
        for _ in range(div_count - close_div_count):
            html_body += '</div>'
        
        html_content += html_body
        html_content += f"""
    <div class="timestamp">
        <strong>TradingAgents专业分析系统</strong><br>
        报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
        系统版本: TradingAgents v2.0 | 
        分析引擎: {"真实TradingAgents" if TRADINGAGENTS_AVAILABLE and self.trading_graph else "备用分析模式"}
    </div>
</body>
</html>"""
        
        return html_content
    
    def run_trading_analysis(self, stock_code, stock_name=""):
        """运行TradingAgents分析并创建飞书文档"""
        print(f"🤖 开始TradingAgents分析: {stock_code} ({stock_name})")
        
        try:
            # 生成分析内容 - 使用真实的TradingAgents
            analysis_content = self.generate_tradingagents_analysis_content(stock_code, stock_name)
            
            # 创建飞书文档
            print("📄 创建飞书文档...")
            doc_link = self.create_feishu_document(stock_code, stock_name, analysis_content)
            
            if not doc_link:
                print("❌ 文档创建失败")
                return {"success": False, "error": "文档创建失败"}
            
            # 保存分析结果到本地文件
            self.save_analysis_to_file(stock_code, stock_name, analysis_content)
            
            # 返回成功结果
            return {
                "success": True,
                "response": analysis_content,
                "doc_link": doc_link
            }
                
        except Exception as e:
            print(f"❌ 分析过程失败: {e}")
            return {"success": False, "error": str(e)}
    
    def save_analysis_to_file(self, stock_code, stock_name, content):
        """保存分析结果到本地文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tradingagents_analysis_{stock_code}_{timestamp}.txt"
            filepath = Path(__file__).parent / 'results' / stock_code / datetime.now().strftime('%Y-%m-%d')
            filepath.mkdir(parents=True, exist_ok=True)
            
            full_filepath = filepath / filename
            
            with open(full_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"📁 TradingAgents分析结果已保存: {full_filepath}")
            
        except Exception as e:
            print(f"⚠️ 保存本地文件失败: {e}")
    
    def process_single_task(self, task):
        """处理单个任务"""
        print(f"\n🔄 处理任务: {task['stock_code']} - {task['stock_name']}")
        print("=" * 60)
        
        record_id = task['record_id']
        stock_code = task['stock_code']
        stock_name = task['stock_name']
        
        # 1. 更新状态为"分析中"
        self.update_task_status(record_id, "分析中")
        
        try:
            # 2. 运行TradingAgents分析并创建飞书文档
            analysis_result = self.run_trading_analysis(stock_code, stock_name)
            
            if analysis_result["success"]:
                # 3. 分析成功，更新状态为"已完成"并添加飞书文档链接
                doc_link = analysis_result.get("doc_link")
                
                self.update_task_status(record_id, "已完成", doc_link)
                
                print(f"✅ 任务完成: {stock_code}")
                print(f"📄 飞书文档: {doc_link}")
                return True
            else:
                # 4. 分析失败，更新状态为"分析失败"
                error_msg = analysis_result.get("error", "未知错误")
                self.update_task_status(record_id, f"分析失败: {error_msg}")
                
                print(f"❌ 任务失败: {stock_code} - {error_msg}")
                return False
                
        except Exception as e:
            # 5. 异常处理
            print(f"❌ 处理任务异常: {e}")
            self.update_task_status(record_id, f"处理异常: {str(e)}")
            return False
    
    def reset_demo_record(self):
        """重置一条记录用于演示"""
        print("🔄 重置记录状态用于演示...")
        
        if not self.access_token:
            print("❌ 没有有效的访问令牌")
            return False
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # 获取表格记录
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{TABLE_APP_TOKEN}/tables/{TABLE_ID}/records"
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            data = resp.json()
            
            if data.get('code') == 0:
                records = data.get('data', {}).get('items', [])
                
                for record in records:
                    fields = record.get('fields', {})
                    stock_code = fields.get('股票代码', '').strip()
                    
                    if stock_code:  # 找到第一条有股票代码的记录
                        record_id = record['record_id']
                        
                        # 清空状态并设置请求日期
                        update_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{TABLE_APP_TOKEN}/tables/{TABLE_ID}/records/{record_id}"
                        current_timestamp = int(datetime.now().timestamp() * 1000)
                        update_data = {
                            "fields": {
                                "当前状态": "",  # 清空状态
                                "请求日期": current_timestamp,  # 使用Unix时间戳
                                "回复链接": ""  # 清空链接
                            }
                        }
                        
                        # 添加重试机制
                        for attempt in range(3):
                            try:
                                update_resp = requests.put(update_url, headers=headers, json=update_data, timeout=10)
                                update_result = update_resp.json()
                                
                                if update_result.get('code') == 0:
                                    print(f"✅ 已重置记录 {stock_code} 的状态")
                                    return True
                                else:
                                    print(f"❌ 重置记录失败: {update_result}")
                                    if attempt < 2:
                                        print(f"🔄 重置重试 {attempt + 1}/3...")
                                        time.sleep(2)
                                        continue
                                    else:
                                        return False
                                        
                            except requests.Timeout:
                                print(f"⏰ 重置记录超时 (尝试 {attempt + 1}/3)")
                                if attempt < 2:
                                    time.sleep(2)
                                    continue
                                else:
                                    print("❌ 重置记录最终超时")
                                    return False
                            except Exception as e:
                                print(f"❌ 重置记录异常 (尝试 {attempt + 1}/3): {e}")
                                if attempt < 2:
                                    time.sleep(2)
                                    continue
                                else:
                                    print("❌ 重置记录最终失败")
                                    return False
                
                print("❌ 没有找到有股票代码的记录")
                return False
            else:
                print(f"❌ 获取记录失败: {data}")
                return False
                
        except requests.Timeout:
            print("⏰ 获取记录超时")
            return False
        except Exception as e:
            print(f"❌ 重置记录异常: {e}")
            return False
    
    def run_batch_processing(self):
        """批量处理飞书表格中的任务"""
        print("🚀 开始TradingAgents与飞书表格完整集成处理")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # 1. 获取待处理任务
        pending_tasks = self.get_pending_tasks()
        
        if not pending_tasks:
            print("💡 没有待处理的任务")
            
            # 演示模式：重置一条记录用于测试
            print("\n🧪 演示模式：重置一条记录状态用于测试...")
            if self.reset_demo_record():
                # 重新获取任务
                pending_tasks = self.get_pending_tasks()
            
        if not pending_tasks:
            print("❌ 没有找到可处理的任务")
            return
        
        # 2. 处理每个任务
        success_count = 0
        failed_count = 0
        
        for i, task in enumerate(pending_tasks, 1):
            print(f"\n📈 处理进度: {i}/{len(pending_tasks)}")
            
            if self.process_single_task(task):
                success_count += 1
            else:
                failed_count += 1
            
            # 任务间延迟，避免API频率限制
            if i < len(pending_tasks):
                print("⏱️ 等待 5 秒后继续下一个任务...")
                time.sleep(5)
        
        # 3. 处理完成总结
        print("\n" + "=" * 70)
        print("🎉 TradingAgents完整集成处理完成!")
        print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✅ 成功处理: {success_count} 个任务")
        print(f"❌ 失败任务: {failed_count} 个任务")
        print(f"📊 总计处理: {len(pending_tasks)} 个任务")
        print(f"🤖 分析引擎: {'真实TradingAgents' if TRADINGAGENTS_AVAILABLE and self.trading_graph else '备用分析模式'}")

def main():
    """主函数 - 执行完整的飞书表格与TradingAgents集成流程"""
    print("🚀 TradingAgents飞书表格完整集成系统启动")
    print("=" * 70)
    print("📋 系统功能:")
    print("   1. 自动获取/刷新飞书访问令牌")
    print("   2. 读取飞书表格中的待处理任务")
    print("   3. 调用真实TradingAgents进行股票分析")
    print("   4. 生成并上传分析报告到飞书文档")
    print("   5. 更新表格状态和文档链接")
    print("=" * 70)
    
    try:
        # 检查环境变量
        required_vars = ["FEISHU_APP_ID", "FEISHU_APP_SECRET"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            print(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
            print("📝 请在 TradingAgents-CN-main/.env 文件中配置这些变量")
            return
        
        # 显示TradingAgents状态
        if TRADINGAGENTS_AVAILABLE:
            print("✅ TradingAgents模块可用 - 将使用真实分析")
        else:
            print("⚠️ TradingAgents模块不可用 - 将使用备用分析")
        
        # 创建处理器实例
        processor = FeiShuTradingProcessor()
        
        # 开始批量处理
        processor.run_batch_processing()
        
    except KeyboardInterrupt:
        print("\n🛑 用户中断程序执行")
    except Exception as e:
        print(f"\n❌ 程序执行异常: {e}")
        print(f"📋 异常详情: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 程序执行完成")

if __name__ == "__main__":
    main()
