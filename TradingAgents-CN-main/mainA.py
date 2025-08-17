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

# Initialize with custom config


# 股票代码作为变量，便于每次执行不同股票
import logging
from pathlib import Path

def get_today_str():
    from datetime import datetime
    return datetime.today().strftime('%Y-%m-%d')

stock_code = input("请输入股票代码（如300059）: ").strip()
if not stock_code:
    print("未输入股票代码，程序已退出。")
    exit(0)
today_str = get_today_str()
log_dir = Path(r'E:\my_agent_learning\TradingAgents\results') / stock_code / today_str
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / 'tradingagents.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file, encoding='utf-8')]
)

ta = TradingAgentsGraph(debug=True, config=config)


def get_today_str():
    return datetime.today().strftime('%Y-%m-%d')

# 示例用法
today_str = get_today_str() #"2024-05-10"
# forward propagate
final_state, decision = ta.propagate("300059", today_str)

# Markdown报告输出（极简版）
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

# 输出Markdown报告
stock_code = "300059"
md_report = generate_markdown_report(final_state, decision, stock_code)
print(md_report)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
