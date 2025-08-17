from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
from datetime import datetime
logger = get_logger('default')


# Create a custom config
config = DEFAULT_CONFIG.copy()

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)


def get_today_str():
    return datetime.today().strftime('%Y-%m-%d')

# 示例用法
today_str = get_today_str() #"2024-05-10"
# forward propagate
_, decision = ta.propagate("300059", today_str)
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
