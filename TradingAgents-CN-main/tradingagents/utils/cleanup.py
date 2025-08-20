#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup.py - TradingAgents结果文件清理工具

功能：
1. 清理过期的股票分析结果文件
2. 按股票目录隔离清理
3. 保留指定天数的最新数据
4. 安全的递归目录删除

作者：AI Assistant
创建时间：2025-01-27
版本：1.0
"""

import os
import time
from pathlib import Path
from datetime import datetime, timedelta
import logging

# 导入统一日志系统
try:
    from tradingagents.utils.logging_init import get_logger
    logger = get_logger("cleanup")
except ImportError:
    logger = logging.getLogger("cleanup")


def cleanup_expired_files(results_root: str, days_to_keep: int = 7) -> dict:
    """
    清理结果目录下过期的股票分析文件
    
    Args:
        results_root: 结果根目录路径
        days_to_keep: 保留最近多少天的文件，默认7天
    
    Returns:
        清理统计信息字典
    """
    root_path = Path(results_root)
    if not root_path.exists():
        logger.warning(f"结果根目录不存在: {root_path}")
        return {"status": "error", "message": "根目录不存在"}

    # 计算过期时间点
    expire_time = datetime.now() - timedelta(days=days_to_keep)
    logger.info(f"开始清理过期文件，保留最近{days_to_keep}天的数据，过期时间点: {expire_time}")

    # 统计信息
    stats = {
        "status": "success",
        "cleaned_directories": 0,
        "cleaned_files": 0,
        "errors": 0,
        "skipped": 0,
        "total_size_freed": 0
    }

    # 遍历所有股票目录
    for ticker_dir in root_path.iterdir():
        if not ticker_dir.is_dir():
            continue  # 只处理目录
        
        logger.debug(f"检查股票目录: {ticker_dir.name}")
        
        # 遍历股票目录下的日期目录
        for date_dir in ticker_dir.iterdir():
            if not date_dir.is_dir():
                continue
                
            try:
                # 解析日期目录名称 (假设格式为 YYYY-MM-DD)
                dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                
                # 判断是否过期
                if dir_date < expire_time:
                    logger.info(f"清理过期目录: {date_dir}")
                    
                    # 计算目录大小
                    dir_size = _get_directory_size(date_dir)
                    
                    # 递归删除目录
                    files_count = _count_files_in_directory(date_dir)
                    _delete_directory(date_dir)
                    
                    # 更新统计
                    stats["cleaned_directories"] += 1
                    stats["cleaned_files"] += files_count
                    stats["total_size_freed"] += dir_size
                    
                else:
                    logger.debug(f"保留目录: {date_dir.name} (日期: {dir_date})")
                    
            except ValueError:
                logger.warning(f"无效的日期目录格式: {date_dir.name}，跳过清理")
                stats["skipped"] += 1
            except Exception as e:
                logger.error(f"清理目录 {date_dir} 时出错: {str(e)}")
                stats["errors"] += 1

    # 清理空的股票目录
    _cleanup_empty_ticker_directories(root_path, stats)

    # 输出清理结果
    logger.info(f"清理完成 - 目录: {stats['cleaned_directories']}, "
               f"文件: {stats['cleaned_files']}, "
               f"释放空间: {_format_size(stats['total_size_freed'])}, "
               f"错误: {stats['errors']}, 跳过: {stats['skipped']}")
    
    return stats


def cleanup_expired_checkpoints(checkpoints_root: str = "checkpoints", days_to_keep: int = 7) -> dict:
    """
    清理过期的断点文件
    
    Args:
        checkpoints_root: 断点根目录路径
        days_to_keep: 保留最近多少天的断点文件
    
    Returns:
        清理统计信息字典
    """
    root_path = Path(checkpoints_root)
    if not root_path.exists():
        logger.info(f"断点目录不存在: {root_path}")
        return {"status": "skipped", "message": "断点目录不存在"}

    expire_time = datetime.now() - timedelta(days=days_to_keep)
    logger.info(f"开始清理过期断点文件，保留最近{days_to_keep}天的数据")

    stats = {
        "status": "success",
        "cleaned_files": 0,
        "errors": 0,
        "total_size_freed": 0
    }

    # 遍历所有股票目录
    for ticker_dir in root_path.iterdir():
        if not ticker_dir.is_dir():
            continue
        
        # 遍历断点文件
        for checkpoint_file in ticker_dir.iterdir():
            if not checkpoint_file.is_file() or not checkpoint_file.name.endswith('.json'):
                continue
            
            try:
                # 从文件名解析日期 (checkpoint_YYYYMMDD.json)
                if checkpoint_file.name.startswith('checkpoint_'):
                    date_str = checkpoint_file.name[11:19]  # 提取YYYYMMDD
                    file_date = datetime.strptime(date_str, "%Y%m%d")
                    
                    if file_date < expire_time:
                        file_size = checkpoint_file.stat().st_size
                        checkpoint_file.unlink()
                        
                        stats["cleaned_files"] += 1
                        stats["total_size_freed"] += file_size
                        
                        logger.debug(f"删除过期断点文件: {checkpoint_file}")
                        
            except (ValueError, OSError) as e:
                logger.error(f"处理断点文件 {checkpoint_file} 时出错: {str(e)}")
                stats["errors"] += 1

    # 清理空的股票目录
    _cleanup_empty_ticker_directories(root_path, stats)

    logger.info(f"断点清理完成 - 文件: {stats['cleaned_files']}, "
               f"释放空间: {_format_size(stats['total_size_freed'])}, "
               f"错误: {stats['errors']}")
    
    return stats


def _delete_directory(path: Path) -> None:
    """递归删除目录及其中所有文件"""
    if not path.exists():
        return
        
    if path.is_file():
        path.unlink()
        return
        
    for item in path.iterdir():
        _delete_directory(item)
    
    path.rmdir()


def _get_directory_size(path: Path) -> int:
    """计算目录总大小（字节）"""
    total_size = 0
    try:
        for item in path.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
    except Exception as e:
        logger.warning(f"计算目录大小时出错 {path}: {e}")
    return total_size


def _count_files_in_directory(path: Path) -> int:
    """计算目录中的文件数量"""
    count = 0
    try:
        for item in path.rglob('*'):
            if item.is_file():
                count += 1
    except Exception as e:
        logger.warning(f"计算文件数量时出错 {path}: {e}")
    return count


def _cleanup_empty_ticker_directories(root_path: Path, stats: dict) -> None:
    """清理空的股票目录"""
    for ticker_dir in root_path.iterdir():
        if ticker_dir.is_dir():
            try:
                # 检查目录是否为空
                if not any(ticker_dir.iterdir()):
                    logger.info(f"删除空的股票目录: {ticker_dir}")
                    ticker_dir.rmdir()
                    stats["cleaned_directories"] += 1
            except Exception as e:
                logger.warning(f"清理空目录时出错 {ticker_dir}: {e}")


def _format_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def auto_cleanup(config: dict) -> dict:
    """
    根据配置自动执行清理任务
    
    Args:
        config: 配置字典，包含清理相关设置
    
    Returns:
        清理结果统计
    """
    if not config.get("auto_cleanup", True):
        logger.info("自动清理已禁用")
        return {"status": "disabled"}
    
    results_dir = config.get("results_dir", "results")
    days_to_keep = config.get("cleanup_expired_days", 7)
    
    logger.info(f"开始自动清理任务，保留{days_to_keep}天数据")
    
    # 清理结果文件
    results_stats = cleanup_expired_files(results_dir, days_to_keep)
    
    # 清理断点文件
    checkpoint_stats = cleanup_expired_checkpoints("checkpoints", days_to_keep)
    
    # 合并统计结果
    combined_stats = {
        "status": "success",
        "results_cleanup": results_stats,
        "checkpoint_cleanup": checkpoint_stats,
        "total_freed_space": results_stats.get("total_size_freed", 0) + checkpoint_stats.get("total_size_freed", 0)
    }
    
    logger.info(f"自动清理完成，总共释放空间: {_format_size(combined_stats['total_freed_space'])}")
    
    return combined_stats


if __name__ == "__main__":
    # 独立运行时的测试代码
    import argparse
    
    parser = argparse.ArgumentParser(description="TradingAgents文件清理工具")
    parser.add_argument("--results-dir", default="results", help="结果目录路径")
    parser.add_argument("--days", type=int, default=7, help="保留天数")
    parser.add_argument("--checkpoints-only", action="store_true", help="仅清理断点文件")
    parser.add_argument("--results-only", action="store_true", help="仅清理结果文件")
    
    args = parser.parse_args()
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    if args.checkpoints_only:
        stats = cleanup_expired_checkpoints(days_to_keep=args.days)
    elif args.results_only:
        stats = cleanup_expired_files(args.results_dir, args.days)
    else:
        # 清理所有
        config = {
            "results_dir": args.results_dir,
            "cleanup_expired_days": args.days,
            "auto_cleanup": True
        }
        stats = auto_cleanup(config)
    
    print(f"清理完成: {stats}")