#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - TradingAgents简化版本（支持断点续传）

功能：
1. 调用TradingAgents进行股票分析
2. 支持断点续传功能，可从中断处恢复
3. 生成本地分析报告
4. 完善的错误处理和日志输出

使用方法：
python main.py

前置条件：
- TradingAgents环境配置正确
- 在TradingAgents-CN-main/.env文件中配置相关API密钥

作者：AI Assistant  
创建时间：2025-01-20
版本：3.0 - 简化版本，支持断点续传
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import json

# 添加TradingAgents-CN-main到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'TradingAgents-CN-main'))

# 从TradingAgents导入必要的模块
try:
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.utils.logging_manager import get_logger
    from tradingagents.utils.checkpoints import clear_checkpoint
    from tradingagents.utils.cleanup import auto_cleanup
    TRADINGAGENTS_AVAILABLE = True
    print("✅ TradingAgents模块导入成功")
except ImportError as e:
    print(f"❌ TradingAgents模块导入失败: {e}")
    print("📝 请检查TradingAgents环境配置")
    TRADINGAGENTS_AVAILABLE = False
    sys.exit(1)

# 加载环境变量
env_path = Path(__file__).parent / 'TradingAgents-CN-main' / '.env'
load_dotenv(env_path)

class TradingProcessor:
    """TradingAgents处理器（简化版）"""
    
    def __init__(self):
        """初始化处理器"""
        self.trading_graph = None
        
        print("🚀 初始化TradingAgents处理器")
        print("=" * 50)
        
        # 初始化TradingAgents
        self.initialize_trading_agents()
        
        print("✅ 处理器初始化完成")
        print("=" * 50)
        
    def initialize_trading_agents(self):
        """初始化TradingAgents图"""
        print("🤖 初始化TradingAgents...")
        
        try:
            # 使用默认配置
            config = DEFAULT_CONFIG.copy()
            
            # 创建TradingAgents图实例
            self.trading_graph = TradingAgentsGraph(
                selected_analysts=["market", "social", "news", "fundamentals"],
                debug=False,
                config=config
            )
            
            print("✅ TradingAgents初始化成功")
            
        except Exception as e:
            print(f"❌ TradingAgents初始化失败: {e}")
            raise
    
    def run_trading_analysis(self, stock_code, stock_name="", analysis_date=None):
        """运行TradingAgents分析（支持断点续传）"""
        print(f"\n📊 开始分析股票: {stock_code} ({stock_name})")
        
        if analysis_date is None:
            analysis_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # 调用TradingAgents进行分析（内置断点续传支持）
            final_state, processed_signal = self.trading_graph.propagate(
                company_name=stock_code,
                trade_date=analysis_date
            )
            
            print("✅ TradingAgents分析完成")
            
            return {
                "success": True,
                "final_state": final_state,
                "processed_signal": processed_signal,
                "analysis_date": analysis_date
            }
            
        except Exception as e:
            print(f"❌ TradingAgents分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_date": analysis_date
            }
    
    def generate_analysis_content(self, analysis_result):
        """生成分析内容"""
        if not analysis_result["success"]:
            return f"分析失败: {analysis_result['error']}"
        
        final_state = analysis_result["final_state"]
        processed_signal = analysis_result["processed_signal"]
        
        # 提取各类报告
        market_report = final_state.get("market_report", "暂无市场分析")
        fundamentals_report = final_state.get("fundamentals_report", "暂无基本面分析")
        news_report = final_state.get("news_report", "暂无新闻分析")
        sentiment_report = final_state.get("sentiment_report", "暂无情绪分析")
        
        # 投资计划和风险评估
        investment_plan = final_state.get("investment_plan", "暂无投资建议")
        final_trade_decision = final_state.get("final_trade_decision", "暂无交易决策")
        
        # 构建完整分析报告
        content = f"""
# 股票分析报告

## 📈 市场分析
{market_report}

## 📊 基本面分析
{fundamentals_report}

## 📰 新闻分析
{news_report}

## 💭 情绪分析
{sentiment_report}

## 💡 投资建议
{investment_plan}

## 🎯 最终交易决策
{final_trade_decision}

## 📋 处理后的信号
- **动作**: {processed_signal.get('action', '未知')}
- **目标价格**: {processed_signal.get('target_price', '未设定')}
- **信心度**: {processed_signal.get('confidence', '未知')}
- **风险评分**: {processed_signal.get('risk_score', '未知')}
- **推理**: {processed_signal.get('reasoning', '无')}

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*分析日期: {analysis_result['analysis_date']}*
"""
        
        return content
    
    def save_analysis_to_file(self, stock_code, stock_name, content, analysis_date):
        """保存分析结果到本地文件"""
        try:
            # 创建结果目录
            results_dir = Path("analysis_results") / stock_code / analysis_date
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存Markdown格式报告
            md_file = results_dir / f"{stock_code}_{stock_name}_analysis.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"📄 分析报告已保存: {md_file}")
            return str(md_file)
            
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
            return None
    
    def clear_checkpoint(self, stock_code, analysis_date):
        """清除指定股票和日期的断点文件"""
        try:
            checkpoint_dir = Path(self.trading_graph.config["results_dir"]) / stock_code / analysis_date
            checkpoint_path = checkpoint_dir / "checkpoint.json"
            
            if checkpoint_path.exists():
                clear_checkpoint(checkpoint_path)
                print(f"🗑️ 已清除断点文件: {checkpoint_path}")
            else:
                print(f"ℹ️ 断点文件不存在: {checkpoint_path}")
                
        except Exception as e:
            print(f"❌ 清除断点文件失败: {e}")
    
    def _format_size(self, size_bytes):
        """格式化文件大小显示"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def process_stock_analysis(self, stock_code, stock_name="", analysis_date=None, clear_existing_checkpoint=False):
        """处理单个股票分析"""
        print(f"\n🎯 处理股票分析任务")
        print(f"📈 股票代码: {stock_code}")
        print(f"📝 股票名称: {stock_name}")
        print(f"📅 分析日期: {analysis_date or '今日'}")
        
        if analysis_date is None:
            analysis_date = datetime.now().strftime("%Y-%m-%d")
        
        # 清除现有断点（如果需要）
        if clear_existing_checkpoint:
            self.clear_checkpoint(stock_code, analysis_date)
        
        # 运行分析
        analysis_result = self.run_trading_analysis(stock_code, stock_name, analysis_date)
        
        if analysis_result["success"]:
            # 生成分析内容
            content = self.generate_analysis_content(analysis_result)
            
            # 保存到本地文件
            file_path = self.save_analysis_to_file(stock_code, stock_name, content, analysis_date)
            
            # 执行自动清理（如果启用）
            try:
                if self.config.get("auto_cleanup", True):
                    print("🧹 执行自动清理过期文件...")
                    cleanup_stats = auto_cleanup(self.config)
                    if cleanup_stats.get("status") == "success":
                        total_freed = cleanup_stats.get("total_freed_space", 0)
                        if total_freed > 0:
                            print(f"✅ 清理完成，释放空间: {self._format_size(total_freed)}")
                        else:
                            print("✅ 清理完成，无过期文件")
                    elif cleanup_stats.get("status") != "disabled":
                        print(f"⚠️ 清理过程中出现问题: {cleanup_stats.get('message', '未知错误')}")
            except Exception as e:
                print(f"⚠️ 自动清理失败: {e}")
            
            print(f"✅ 股票 {stock_code} 分析完成")
            return {
                "success": True,
                "file_path": file_path,
                "content": content
            }
        else:
            print(f"❌ 股票 {stock_code} 分析失败: {analysis_result['error']}")
            return {
                "success": False,
                "error": analysis_result["error"]
            }

def main():
    """主函数"""
    print("🚀 TradingAgents 简化版本启动")
    print("支持断点续传功能")
    print("=" * 60)
    
    # 检查环境
    if not TRADINGAGENTS_AVAILABLE:
        print("❌ TradingAgents不可用，程序退出")
        return
    
    try:
        # 创建处理器
        processor = TradingProcessor()
        
        # 示例：分析单个股票
        stock_code = input("\n请输入股票代码 (例如: AAPL): ").strip()
        if not stock_code:
            stock_code = "AAPL"  # 默认值
        
        stock_name = input(f"请输入股票名称 (可选，默认为空): ").strip()
        
        # 询问是否清除现有断点
        clear_checkpoint = input("是否清除现有断点重新开始？(y/N): ").strip().lower() == 'y'
        
        # 处理分析
        result = processor.process_stock_analysis(
            stock_code=stock_code,
            stock_name=stock_name,
            clear_existing_checkpoint=clear_checkpoint
        )
        
        if result["success"]:
            print(f"\n🎉 分析成功完成！")
            print(f"📄 报告文件: {result['file_path']}")
        else:
            print(f"\n❌ 分析失败: {result['error']}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断程序")
        print("💾 断点已自动保存，下次运行时可继续")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        print("💾 如有断点文件，下次运行时可尝试恢复")
    
    print("\n👋 程序结束")

if __name__ == "__main__":
    main()
