import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": os.path.join(os.path.expanduser("~"), "Documents", "TradingAgents", "data"),
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    "llm_provider": "dashscope",
    "deep_think_llm": "qwen3-235b-a22b-thinking-2507",
    "quick_think_llm": "qwen3-235b-a22b-instruct-2507",
    # "backend_url": "https://api.openai.com/v1",
    "backend_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 150,
    # Tool settings
    "online_tools": True,
    
    # Cleanup settings
    "cleanup_expired_days": 7,  # 保留最近7天的数据
    "auto_cleanup": True,  # 是否自动清理过期文件
    "cleanup_on_startup": False,  # 是否在启动时自动清理
    "cleanup_checkpoints": True,  # 是否清理过期的断点文件

    # Note: Database and cache configuration is now managed by .env file and config.database_manager
    # No database/cache settings in default config to avoid configuration conflicts
}