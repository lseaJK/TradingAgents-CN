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
FEISHU_ACCESS_TOKEN = os.getenv('FEISHU_ACCESS_TOKEN')
FEISHU_APP_TOKEN = "JuW6bVdlYajxlDsVU80cds6Tnxq"  # 飞书表格 app_token（最新创建）
FEISHU_TABLE_ID = "tblBktnrVWeojVLE"  # 飞书表格 table_id
FEISHU_TABLE_FIELDS = {
    'stock_code': '股票代码',
    'request_date': '请求日期',
    'status': '当前状态',
    'reply_link': '回复链接'
}

def get_feishu_access_token():
    """
    实时获取飞书AccessToken（每次API请求前都刷新，避免过期）
    """
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/"
    resp = requests.post(url, json={
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    })
    data = resp.json()
    token = data.get('app_access_token')
    if not token:
        logger.error(f"飞书 access_token 获取失败: {data}")
    return token

def fetch_pending_tasks_from_feishu_table():
    """
    获取飞书表格中待处理（当前状态为空）的任务行
    """
    access_token = get_feishu_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    resp = requests.get(url, headers=headers)
    data = resp.json()
    tasks = []
    for item in data.get('data', {}).get('items', []):
        fields = item.get('fields', {})
        record_id = item.get('record_id')
        stock_code = fields.get(FEISHU_TABLE_FIELDS['stock_code'])
        status = fields.get(FEISHU_TABLE_FIELDS['status'])
        if stock_code and not status:
            tasks.append({'record_id': record_id, 'stock_code': stock_code})
    return tasks

def update_feishu_table_row(record_id, request_date, status, reply_link):
    """
    更新飞书表格指定行（通过record_id）
    """
    access_token = get_feishu_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/{record_id}"
    fields = {
        FEISHU_TABLE_FIELDS['request_date']: request_date,
        FEISHU_TABLE_FIELDS['status']: status,
        FEISHU_TABLE_FIELDS['reply_link']: reply_link
    }
    resp = requests.put(url, headers=headers, json={"fields": fields})
    return resp.json()


def create_feishu_doc(title, md_content):
    """
    创建飞书文档并写入Markdown内容，并写入日志
    """
    access_token = get_feishu_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    # 创建文档
    create_url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    resp = requests.post(create_url, headers=headers, json={
        "title": title
    })
    doc_data = resp.json()
    doc_id = doc_data.get('data', {}).get('document_id')
    if not doc_id:
        logger.error(f"飞书文档创建失败: {doc_data}")
        print("飞书文档创建失败", doc_data)
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



from datetime import datetime
def generate_markdown_report(final_state, decision, stock_symbol):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action = decision.get('action', 'N/A').upper()
    target_price = decision.get('target_price', 'N/A')
    reasoning = decision.get('reasoning', '暂无分析推理')
    confidence = decision.get('confidence', 0)
    risk_score = decision.get('risk_score', 0)

    md = f"# {stock_symbol} 股票分析报告\n\n"
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
    ta = TradingAgentsGraph(debug=True, config=config)
    tasks = fetch_pending_tasks_from_feishu_table()
    for task in tasks:
        record_id = task['record_id']
        stock_code = task['stock_code']
        today_str = get_today_str()
        # 日志目录
        log_dir = Path(r'E:\my_agent_learning\TradingAgents\results') / stock_code / today_str
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'tradingagents.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler(log_file, encoding='utf-8')]
        )
        try:
            final_state, decision = ta.propagate(stock_code, today_str)
            md_report = generate_markdown_report(final_state, decision, stock_code)
            print(md_report)
            feishu_title = f"{stock_code}_{today_str}"
            doc_id = create_feishu_doc(feishu_title, md_report)
            doc_url = f"https://feishu.cn/docx/{doc_id}" if doc_id else ""
            update_feishu_table_row(record_id, today_str, "已完成", doc_url)
            logger.info(f"{stock_code} 分析完成，已更新飞书表格。")
        except Exception as e:
            update_feishu_table_row(record_id, today_str, "失败", str(e))
            logger.error(f"{stock_code} 分析失败: {e}")

if __name__ == "__main__":
    # 打印当前表格基础信息，便于用户查看
    print("飞书表格信息：")
    print(f"表格名称: TradingAgents任务表")
    print(f"表格 app_token: {FEISHU_APP_TOKEN}")
    print(f"表格 table_id: {FEISHU_TABLE_ID}")
    print(f"表格链接: https://tcnab3awhbc1.feishu.cn/base/{FEISHU_APP_TOKEN}")
    # main()
