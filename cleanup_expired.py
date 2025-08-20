#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup_expired.py - TradingAgents过期文件清理脚本

功能：
1. 手动清理过期的股票分析结果文件
2. 清理过期的断点文件
3. 支持命令行参数配置
4. 详细的清理统计报告

使用方法：
    python scripts/cleanup_expired.py                    # 使用默认配置清理
    python scripts/cleanup_expired.py --days 14         # 保留14天数据
    python scripts/cleanup_expired.py --results-only    # 仅清理结果文件
    python scripts/cleanup_expired.py --checkpoints-only # 仅清理断点文件
    python scripts/cleanup_expired.py --dry-run         # 预览清理操作

作者：AI Assistant
创建时间：2025-01-27
版本：1.0
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'TradingAgents-CN-main'))

try:
    from tradingagents.utils.cleanup import cleanup_expired_files, cleanup_expired_checkpoints, auto_cleanup
    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.utils.logging_manager import get_logger
except ImportError as e:
    print(f"❌ 导入TradingAgents模块失败: {e}")
    print("📝 请确保TradingAgents环境配置正确")
    sys.exit(1)

# 设置日志
logger = get_logger("cleanup_script")


def format_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def print_cleanup_stats(stats, operation_name):
    """打印清理统计信息"""
    print(f"\n📊 {operation_name}统计:")
    print(f"   状态: {stats.get('status', 'unknown')}")
    
    if stats.get('status') == 'success':
        print(f"   清理目录: {stats.get('cleaned_directories', 0)}")
        print(f"   清理文件: {stats.get('cleaned_files', 0)}")
        print(f"   释放空间: {format_size(stats.get('total_size_freed', 0))}")
        print(f"   错误数量: {stats.get('errors', 0)}")
        print(f"   跳过数量: {stats.get('skipped', 0)}")
    elif stats.get('status') == 'disabled':
        print(f"   清理已禁用")
    elif stats.get('status') == 'skipped':
        print(f"   跳过原因: {stats.get('message', '未知')}")
    else:
        print(f"   错误信息: {stats.get('message', '未知错误')}")


def dry_run_cleanup(results_dir, checkpoints_dir, days_to_keep):
    """预览清理操作（不实际删除文件）"""
    print(f"🔍 预览清理操作 (保留{days_to_keep}天数据)")
    print(f"📁 结果目录: {results_dir}")
    print(f"💾 断点目录: {checkpoints_dir}")
    print("\n⚠️ 这是预览模式，不会实际删除文件")
    
    from datetime import timedelta
    expire_time = datetime.now() - timedelta(days=days_to_keep)
    
    # 检查结果目录
    results_path = Path(results_dir)
    if results_path.exists():
        print(f"\n📊 结果文件预览:")
        total_dirs = 0
        total_files = 0
        total_size = 0
        
        for ticker_dir in results_path.iterdir():
            if not ticker_dir.is_dir():
                continue
            
            for date_dir in ticker_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                
                try:
                    dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                    if dir_date < expire_time:
                        dir_size = sum(f.stat().st_size for f in date_dir.rglob('*') if f.is_file())
                        file_count = sum(1 for f in date_dir.rglob('*') if f.is_file())
                        
                        print(f"   🗑️ {date_dir} ({format_size(dir_size)}, {file_count}文件)")
                        total_dirs += 1
                        total_files += file_count
                        total_size += dir_size
                except ValueError:
                    continue
        
        print(f"   总计: {total_dirs}目录, {total_files}文件, {format_size(total_size)}")
    else:
        print(f"\n📊 结果目录不存在: {results_dir}")
    
    # 检查断点目录
    checkpoints_path = Path(checkpoints_dir)
    if checkpoints_path.exists():
        print(f"\n💾 断点文件预览:")
        total_files = 0
        total_size = 0
        
        for ticker_dir in checkpoints_path.iterdir():
            if not ticker_dir.is_dir():
                continue
            
            for checkpoint_file in ticker_dir.iterdir():
                if not checkpoint_file.is_file() or not checkpoint_file.name.endswith('.json'):
                    continue
                
                try:
                    if checkpoint_file.name.startswith('checkpoint_'):
                        date_str = checkpoint_file.name[11:19]
                        file_date = datetime.strptime(date_str, "%Y%m%d")
                        
                        if file_date < expire_time:
                            file_size = checkpoint_file.stat().st_size
                            print(f"   🗑️ {checkpoint_file} ({format_size(file_size)})")
                            total_files += 1
                            total_size += file_size
                except ValueError:
                    continue
        
        print(f"   总计: {total_files}文件, {format_size(total_size)}")
    else:
        print(f"\n💾 断点目录不存在: {checkpoints_dir}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="TradingAgents过期文件清理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s                          # 使用默认配置清理所有过期文件
  %(prog)s --days 14                # 保留14天数据
  %(prog)s --results-only           # 仅清理结果文件
  %(prog)s --checkpoints-only       # 仅清理断点文件
  %(prog)s --dry-run                # 预览清理操作
  %(prog)s --results-dir /custom/path --days 30  # 自定义目录和保留天数
        """
    )
    
    parser.add_argument(
        "--results-dir", 
        default=None,
        help="结果目录路径 (默认使用配置文件中的设置)"
    )
    parser.add_argument(
        "--checkpoints-dir",
        default="checkpoints",
        help="断点目录路径 (默认: checkpoints)"
    )
    parser.add_argument(
        "--days", 
        type=int, 
        default=None,
        help="保留天数 (默认使用配置文件中的设置)"
    )
    parser.add_argument(
        "--results-only", 
        action="store_true",
        help="仅清理结果文件"
    )
    parser.add_argument(
        "--checkpoints-only", 
        action="store_true",
        help="仅清理断点文件"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="预览清理操作，不实际删除文件"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出"
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    import logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 获取配置
    config = DEFAULT_CONFIG.copy()
    results_dir = args.results_dir or config.get("results_dir", "./results")
    checkpoints_dir = args.checkpoints_dir
    days_to_keep = args.days if args.days is not None else config.get("cleanup_expired_days", 7)
    
    print("🧹 TradingAgents过期文件清理工具")
    print("=" * 50)
    print(f"📁 结果目录: {results_dir}")
    print(f"💾 断点目录: {checkpoints_dir}")
    print(f"📅 保留天数: {days_to_keep}")
    print(f"🕒 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 预览模式
    if args.dry_run:
        dry_run_cleanup(results_dir, checkpoints_dir, days_to_keep)
        return
    
    # 确认操作
    if not args.results_only and not args.checkpoints_only:
        confirm = input(f"\n⚠️ 将清理超过{days_to_keep}天的所有文件，是否继续？(y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ 操作已取消")
            return
    
    print(f"\n🚀 开始清理过期文件...")
    start_time = datetime.now()
    
    try:
        if args.checkpoints_only:
            # 仅清理断点文件
            print("💾 清理断点文件...")
            checkpoint_stats = cleanup_expired_checkpoints(checkpoints_dir, days_to_keep)
            print_cleanup_stats(checkpoint_stats, "断点清理")
            
        elif args.results_only:
            # 仅清理结果文件
            print("📊 清理结果文件...")
            results_stats = cleanup_expired_files(results_dir, days_to_keep)
            print_cleanup_stats(results_stats, "结果清理")
            
        else:
            # 清理所有文件
            config_for_cleanup = {
                "results_dir": results_dir,
                "cleanup_expired_days": days_to_keep,
                "auto_cleanup": True
            }
            
            combined_stats = auto_cleanup(config_for_cleanup)
            
            if "results_cleanup" in combined_stats:
                print_cleanup_stats(combined_stats["results_cleanup"], "结果清理")
            
            if "checkpoint_cleanup" in combined_stats:
                print_cleanup_stats(combined_stats["checkpoint_cleanup"], "断点清理")
            
            total_freed = combined_stats.get("total_freed_space", 0)
            if total_freed > 0:
                print(f"\n🎉 总共释放空间: {format_size(total_freed)}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"\n✅ 清理完成，耗时: {duration:.1f}秒")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 清理过程中出错: {e}")
        logger.exception("清理过程异常")
        sys.exit(1)


if __name__ == "__main__":
    main()