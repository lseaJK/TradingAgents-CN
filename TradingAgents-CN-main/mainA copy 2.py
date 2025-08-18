from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
from datetime import datetime
logger = get_logger('default')

# Create a custom config
import os
config = DEFAULT_CONFIG.copy()
os.environ['TRADINGAGENTS_LOG_DIR'] = r'E:\my_agent_learning\TradingAgents\results'



# 股票代码作为变量，便于每次执行不同股票
import logging
from pathlib import Path

def get_today_str():
    from datetime import datetime
    return datetime.today().strftime('%Y-%m-%d')


# 飞书API依赖
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import requests


# 加载.env配置
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# 飞书表格相关配置（需在.env中配置）
FEISHU_APP_ID = os.getenv('FEISHU_APP_ID')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET')
FEISHU_USER_ACCESS_TOKEN = os.getenv('FEISHU_USER_ACCESS_TOKEN')
FEISHU_REFRESH_TOKEN = os.getenv('FEISHU_REFRESH_TOKEN')
FEISHU_APP_TOKEN = "JuW6bVdlYajxlDsVU80cds6Tnxq"  # 飞书表格 app_token（最新创建）
FEISHU_TABLE_ID = "tblBktnrVWeojVLE"  # 飞书表格 table_id

# 表格字段配置（根据实际字段信息更新）
FEISHU_TABLE_FIELDS = {
    'stock_code': {'name': '股票代码', 'id': 'fld2C6SJHN', 'type': 1},
    'stock_name': {'name': '股票名称', 'id': 'fldY9bygVX', 'type': 1}, 
    'request_date': {'name': '请求日期', 'id': 'fldYbistOj', 'type': 5},
    'status': {'name': '当前状态', 'id': 'fldaesRzlV', 'type': 1},
    'reply_link': {'name': '回复链接', 'id': 'fldZ346X93', 'type': 15}
}

def refresh_feishu_user_access_token():
    """
    使用refresh_token刷新用户访问令牌，并更新环境变量
    """
    if not FEISHU_REFRESH_TOKEN:
        logger.error("缺少 FEISHU_REFRESH_TOKEN，无法刷新访问令牌")
        return None
        
    url = "https://open.feishu.cn/open-apis/authen/v1/refresh_access_token"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": FEISHU_REFRESH_TOKEN
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload)
        data = resp.json()
        
        if data.get('code') == 0:
            new_access_token = data['data']['access_token']
            new_refresh_token = data['data']['refresh_token']
            
            # 更新环境变量
            import subprocess
            subprocess.run([
                'powershell', '-Command', 
                f'[Environment]::SetEnvironmentVariable("FEISHU_USER_ACCESS_TOKEN", "{new_access_token}", "User")'
            ], shell=True)
            subprocess.run([
                'powershell', '-Command', 
                f'[Environment]::SetEnvironmentVariable("FEISHU_REFRESH_TOKEN", "{new_refresh_token}", "User")'
            ], shell=True)
            
            logger.info("飞书用户访问令牌刷新成功")
            return new_access_token
        else:
            logger.error(f"刷新飞书用户访问令牌失败: {data}")
            return None
    except Exception as e:
        logger.error(f"刷新飞书用户访问令牌异常: {e}")
        return None

def get_feishu_access_token():
    """
    获取飞书AccessToken（优先使用用户令牌，回退到应用令牌）
    """
    # 首先尝试使用用户访问令牌
    if FEISHU_USER_ACCESS_TOKEN:
        return FEISHU_USER_ACCESS_TOKEN
    
    # 尝试刷新用户访问令牌
    refreshed_token = refresh_feishu_user_access_token()
    if refreshed_token:
        return refreshed_token
    
    # 回退到应用访问令牌
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/"
    resp = requests.post(url, json={
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    })
    data = resp.json()
    token = data.get('app_access_token')
    if not token:
        logger.error(f"飞书 app_access_token 获取失败: {data}")
    return token

def fetch_pending_tasks_from_feishu_table():
    """
    获取飞书表格中待处理（当前状态为空）的任务行
    """
    access_token = get_feishu_access_token()
    if not access_token:
        logger.error("无法获取飞书访问令牌")
        return []
        
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    
    try:
        resp = requests.get(url, headers=headers)
        data = resp.json()
        
        if data.get('code') != 0:
            logger.error(f"获取飞书表格数据失败: {data}")
            return []
            
        tasks = []
        for item in data.get('data', {}).get('items', []):
            fields = item.get('fields', {})
            record_id = item.get('record_id')
            
            # 使用字段名获取数据
            stock_code = fields.get(FEISHU_TABLE_FIELDS['stock_code']['name'])
            stock_name = fields.get(FEISHU_TABLE_FIELDS['stock_name']['name'])
            status = fields.get(FEISHU_TABLE_FIELDS['status']['name'])
            
            # 筛选：有股票代码且状态为空的行
            if stock_code and not status:
                tasks.append({
                    'record_id': record_id, 
                    'stock_code': stock_code,
                    'stock_name': stock_name or ''
                })
                logger.info(f"发现待处理任务: {stock_code} ({stock_name})")
                
        return tasks
        
    except Exception as e:
        logger.error(f"获取飞书表格数据异常: {e}")
        return []

def update_feishu_table_row(record_id, request_date, status, reply_link):
    """
    更新飞书表格指定行（通过record_id）
    """
    access_token = get_feishu_access_token()
    if not access_token:
        logger.error("无法获取飞书访问令牌，无法更新表格")
        return None
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/{record_id}"
    
    # 使用字段名构建更新数据
    fields = {
        FEISHU_TABLE_FIELDS['request_date']['name']: request_date,
        FEISHU_TABLE_FIELDS['status']['name']: status,
        FEISHU_TABLE_FIELDS['reply_link']['name']: reply_link
    }
    
    try:
        resp = requests.put(url, headers=headers, json={"fields": fields})
        result = resp.json()
        
        if result.get('code') == 0:
            logger.info(f"飞书表格更新成功: record_id={record_id}, status={status}")
        else:
            logger.error(f"飞书表格更新失败: {result}")
            
        return result
        
    except Exception as e:
        logger.error(f"更新飞书表格异常: {e}")
        return None


def create_feishu_doc(title, md_content):
    """
    创建飞书文档并写入Markdown内容，并写入日志
    """
    access_token = get_feishu_access_token()
    if not access_token:
        logger.error("无法获取飞书访问令牌，无法创建文档")
        return None
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    try:
        # 创建文档
        create_url = "https://open.feishu.cn/open-apis/docx/v1/documents"
        resp = requests.post(create_url, headers=headers, json={
            "title": title
        })
        doc_data = resp.json()
        
        if doc_data.get('code') != 0:
            logger.error(f"飞书文档创建失败: {doc_data}")
            print("飞书文档创建失败", doc_data)
            return None
            
        doc_id = doc_data.get('data', {}).get('document_id')
        if not doc_id:
            logger.error(f"飞书文档创建失败，未获取到document_id: {doc_data}")
            return None
            
        # 写入内容
        import_content_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/import"
        resp2 = requests.post(import_content_url, headers=headers, json={
            "markdown": md_content
        })
        result = resp2.json()
        
        if result.get('code', 0) == 0:
            logger.info(f"已写入飞书文档: {title} (ID: {doc_id})")
            print(f"✅ 已写入飞书文档: {title} (ID: {doc_id})")
            return doc_id
        else:
            logger.error(f"飞书文档写入失败: {result}")
            print("飞书文档写入失败", result)
            return None
            
    except Exception as e:
        logger.error(f"创建飞书文档异常: {e}")
        print(f"创建飞书文档异常: {e}")
        return None



def generate_markdown_report(final_state, decision, stock_symbol, stock_name=""):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action = decision.get('action', 'N/A').upper()
    target_price = decision.get('target_price', 'N/A')
    reasoning = decision.get('reasoning', '暂无分析推理')
    confidence = decision.get('confidence', 0)
    risk_score = decision.get('risk_score', 0)

    # 添加股票名称到标题
    title = f"{stock_symbol} 股票分析报告"
    if stock_name:
        title = f"{stock_symbol} ({stock_name}) 股票分析报告"
    
    md = f"# {title}\n\n"
    md += f"**生成时间**: {timestamp}\n\n"
    md += "## 🎯 投资决策摘要\n\n"
    md += "| 指标 | 数值 |\n|------|------|\n"
    md += f"| **投资建议** | {action} |\n"
    md += f"| **置信度** | {confidence:.1%} |\n"
    md += f"| **风险评分** | {risk_score:.1%} |\n"
    md += f"| **目标价位** | {target_price} |\n\n"
    md += f"### 分析推理\n{reasoning}\n\n---\n"

    # 各分析模块
    def add_section(title, key):
        content = final_state.get(key)
        if content:
            return f"## {title}\n\n{content}\n\n"
        return ""
    md += add_section("📈 市场技术分析", "market_report")
    md += add_section("💰 基本面分析", "fundamentals_report")
    md += add_section("💭 市场情绪分析", "sentiment_report")
    md += add_section("📰 新闻事件分析", "news_report")

    # 研究团队决策
    debate_state = final_state.get('investment_debate_state', {})
    if debate_state:
        md += "---\n\n## 🔬 研究团队决策\n\n"
        if debate_state.get('bull_history'):
            md += f"### 📈 多头研究员分析\n{debate_state['bull_history']}\n\n"
        if debate_state.get('bear_history'):
            md += f"### 📉 空头研究员分析\n{debate_state['bear_history']}\n\n"
        if debate_state.get('judge_decision'):
            md += f"### 🎯 研究经理综合决策\n{debate_state['judge_decision']}\n\n"

    # 交易团队计划
    if final_state.get('trader_investment_plan'):
        md += "---\n\n## 💼 交易团队计划\n\n"
        md += f"{final_state['trader_investment_plan']}\n\n"

    # 风险管理团队决策
    risk_state = final_state.get('risk_debate_state', {})
    if risk_state:
        md += "---\n\n## ⚖️ 风险管理团队决策\n\n"
        if risk_state.get('risky_history'):
            md += f"### 🚀 激进分析师评估\n{risk_state['risky_history']}\n\n"
        if risk_state.get('safe_history'):
            md += f"### 🛡️ 保守分析师评估\n{risk_state['safe_history']}\n\n"
        if risk_state.get('neutral_history'):
            md += f"### ⚖️ 中性分析师评估\n{risk_state['neutral_history']}\n\n"
        if risk_state.get('judge_decision'):
            md += f"### 🎯 投资组合经理决策\n{risk_state['judge_decision']}\n\n"

    # 最终投资信号
    if final_state.get('final_trade_decision'):
        md += "---\n\n## 🏁 最终投资信号\n\n"
        md += f"{final_state['final_trade_decision']}\n\n"

    # 风险提示
    md += "---\n\n## ⚠️ 重要风险提示\n\n"
    md += "**仅供参考，投资有风险，决策需谨慎。**\n"
    return md

# 主流程：自动处理飞书表格中的待分析任务
def main():
    logger.info("启动TradingAgents自动分析流程")
    
    # 获取待处理任务
    tasks = fetch_pending_tasks_from_feishu_table()
    if not tasks:
        logger.info("当前没有待处理的任务")
        print("当前没有待处理的任务")
        return
    
    logger.info(f"发现 {len(tasks)} 个待处理任务")
    print(f"发现 {len(tasks)} 个待处理任务")
    
    # 初始化TradingAgents
    ta = TradingAgentsGraph(debug=True, config=config)
    
    for i, task in enumerate(tasks, 1):
        record_id = task['record_id']
        stock_code = task['stock_code']
        stock_name = task['stock_name']
        today_str = get_today_str()
        
        print(f"\n{'='*50}")
        print(f"处理任务 {i}/{len(tasks)}: {stock_code} ({stock_name})")
        print(f"{'='*50}")
        
        # 配置日志目录（按需求文档要求）
        log_dir = Path(r'E:\my_agent_learning\TradingAgents\results') / stock_code / today_str
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'tradingagents.log'
        
        # 配置任务专用日志处理器
        task_logger = logging.getLogger(f'task_{stock_code}')
        task_logger.setLevel(logging.INFO)
        
        # 移除旧的处理器
        for handler in task_logger.handlers[:]:
            task_logger.removeHandler(handler)
            
        # 添加文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        task_logger.addHandler(file_handler)
        
        # 同时输出到控制台
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        task_logger.addHandler(console_handler)
        
        task_logger.info(f"开始分析股票: {stock_code} ({stock_name})")
        
        try:
            # 先更新状态为"进行中"
            update_feishu_table_row(record_id, today_str, "进行中", "")
            task_logger.info(f"已更新表格状态为'进行中': {stock_code}")
            
            # 执行分析
            final_state, decision = ta.propagate(stock_code, today_str)
            task_logger.info(f"股票分析完成: {stock_code}")
            
            # 生成报告
            md_report = generate_markdown_report(final_state, decision, stock_code, stock_name)
            
            # 保存本地报告文件
            report_file = log_dir / 'report.md'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(md_report)
            task_logger.info(f"本地报告已保存: {report_file}")
            
            print(f"\n📊 {stock_code} 分析报告预览:")
            print("=" * 60)
            print(md_report[:500] + "..." if len(md_report) > 500 else md_report)
            print("=" * 60)
            
            # 创建飞书文档
            feishu_title = f"{stock_code}_{stock_name}_{today_str}" if stock_name else f"{stock_code}_{today_str}"
            doc_id = create_feishu_doc(feishu_title, md_report)
            
            if doc_id:
                doc_url = f"https://feishu.cn/docx/{doc_id}"
                # 更新表格为"已完成"
                update_feishu_table_row(record_id, today_str, "已完成", doc_url)
                task_logger.info(f"任务完成，已更新飞书表格: {stock_code}")
                print(f"✅ {stock_code} 分析完成，飞书文档: {doc_url}")
            else:
                # 文档创建失败，但分析成功
                local_report_path = str(report_file)
                update_feishu_table_row(record_id, today_str, "已完成(本地)", local_report_path)
                task_logger.warning(f"飞书文档创建失败，但分析完成，本地报告: {local_report_path}")
                print(f"⚠️ {stock_code} 分析完成，但飞书文档创建失败，本地报告: {local_report_path}")
                
        except Exception as e:
            error_msg = f"分析失败: {str(e)}"
            update_feishu_table_row(record_id, today_str, "失败", error_msg)
            task_logger.error(f"股票 {stock_code} 分析失败: {e}", exc_info=True)
            print(f"❌ {stock_code} 分析失败: {e}")
        
        finally:
            # 清理任务专用日志处理器
            for handler in task_logger.handlers[:]:
                handler.close()
                task_logger.removeHandler(handler)
    
    logger.info("所有任务处理完成")
    print(f"\n{'='*50}")
    print("所有任务处理完成")
    print(f"{'='*50}")

if __name__ == "__main__":
    # 打印当前表格基础信息，便于用户查看
    print("飞书表格信息：")
    print(f"表格名称: TradingAgents任务表")
    print(f"表格 app_token: {FEISHU_APP_TOKEN}")
    print(f"表格 table_id: {FEISHU_TABLE_ID}")
    print(f"表格链接: https://tcnab3awhbc1.feishu.cn/base/{FEISHU_APP_TOKEN}")
    print(f"日志目录: E:\\my_agent_learning\\TradingAgents\\results")
    
    # 检查环境变量配置
    print("\n环境变量检查：")
    env_vars = ['FEISHU_APP_ID', 'FEISHU_APP_SECRET', 'FEISHU_USER_ACCESS_TOKEN', 'FEISHU_REFRESH_TOKEN']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 10}...{value[-4:] if len(value) > 4 else '****'}")
        else:
            print(f"❌ {var}: 未设置")
    
    print("\n" + "="*60)
    print("启动自动分析流程...")
    print("="*60)
    
    # 启用主流程
    main()
