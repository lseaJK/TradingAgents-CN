#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
checkpoints.py - TradingAgents断点续传功能实现

功能：
1. 保存和加载分析过程的中间状态
2. 支持节点级别的断点续传
3. 处理不可序列化对象的转换
4. 提供异常恢复机制

作者：AI Assistant
创建时间：2025-01-27
版本：1.0
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# 导入统一日志系统
try:
    from tradingagents.utils.logging_init import get_logger
    logger = get_logger("checkpoints")
except ImportError:
    import logging
    logger = logging.getLogger("checkpoints")


class CustomEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理不可序列化的对象"""
    
    def default(self, obj):
        """处理特殊对象的序列化"""
        # 处理有dict方法的对象（如Pydantic模型）
        if hasattr(obj, 'dict'):
            try:
                return obj.dict()
            except Exception:
                pass
        
        # 处理有__dict__属性的对象
        if hasattr(obj, '__dict__'):
            try:
                return obj.__dict__
            except Exception:
                pass
        
        # 处理LangChain消息对象
        if hasattr(obj, 'content') and hasattr(obj, 'type'):
            try:
                return {
                    'type': getattr(obj, 'type', 'unknown'),
                    'content': getattr(obj, 'content', ''),
                    'additional_kwargs': getattr(obj, 'additional_kwargs', {}),
                    'response_metadata': getattr(obj, 'response_metadata', {}),
                    'id': getattr(obj, 'id', '')
                }
            except Exception:
                pass
        
        # 处理datetime对象
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # 其他对象转为字符串
        try:
            return str(obj)
        except Exception:
            return f"<不可序列化对象: {type(obj).__name__}>"


def get_checkpoint_path(ticker: str, analysis_date: str) -> Path:
    """获取断点文件路径
    
    Args:
        ticker: 股票代码
        analysis_date: 分析日期 (YYYY-MM-DD格式)
    
    Returns:
        断点文件的完整路径
    """
    # 使用项目根目录下的checkpoints文件夹
    checkpoint_dir = Path("checkpoints") / ticker
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # 文件名包含日期信息
    filename = f"checkpoint_{analysis_date.replace('-', '')}.json"
    return checkpoint_dir / filename


def save_checkpoint(state: Dict[str, Any], ticker: str, analysis_date: str) -> bool:
    """保存断点状态到文件
    
    Args:
        state: 要保存的状态字典
        ticker: 股票代码
        analysis_date: 分析日期
    
    Returns:
        保存是否成功
    """
    try:
        checkpoint_path = get_checkpoint_path(ticker, analysis_date)
        
        # 添加保存时间戳
        state_with_timestamp = state.copy()
        state_with_timestamp['_checkpoint_timestamp'] = datetime.now().isoformat()
        
        # 保存到文件
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(state_with_timestamp, f, ensure_ascii=False, indent=2, cls=CustomEncoder)
        
        logger.info(f"断点保存成功: {checkpoint_path}")
        return True
        
    except Exception as e:
        logger.error(f"断点保存失败: {e}")
        return False


def load_checkpoint(ticker: str, analysis_date: str) -> Optional[Dict[str, Any]]:
    """从文件加载断点状态
    
    Args:
        ticker: 股票代码
        analysis_date: 分析日期
    
    Returns:
        加载的状态字典，如果文件不存在或加载失败则返回None
    """
    try:
        checkpoint_path = get_checkpoint_path(ticker, analysis_date)
        
        if not checkpoint_path.exists():
            logger.info(f"断点文件不存在: {checkpoint_path}")
            return None
        
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        # 检查时间戳
        timestamp = state.get('_checkpoint_timestamp')
        if timestamp:
            logger.info(f"加载断点文件，保存时间: {timestamp}")
        
        logger.info(f"断点加载成功: {checkpoint_path}")
        return state
        
    except Exception as e:
        logger.error(f"断点加载失败: {e}")
        return None


def clear_checkpoint(ticker: str, analysis_date: str) -> bool:
    """清除断点文件
    
    Args:
        ticker: 股票代码
        analysis_date: 分析日期
    
    Returns:
        清除是否成功
    """
    try:
        checkpoint_path = get_checkpoint_path(ticker, analysis_date)
        
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            logger.info(f"断点文件已清除: {checkpoint_path}")
        return True
        
    except Exception as e:
        logger.error(f"清除断点文件失败: {e}")
        return False


def is_node_completed(state: Dict[str, Any], node_name: str) -> bool:
    """检查节点是否已完成
    
    Args:
        state: 状态字典
        node_name: 节点名称
    
    Returns:
        节点是否已完成
    """
    completed_nodes = state.get("completed_nodes", [])
    return node_name in completed_nodes


def mark_node_completed(state: Dict[str, Any], node_name: str) -> None:
    """标记节点为已完成
    
    Args:
        state: 状态字典
        node_name: 节点名称
    """
    if "completed_nodes" not in state:
        state["completed_nodes"] = []
    
    if node_name not in state["completed_nodes"]:
        state["completed_nodes"].append(node_name)
        logger.debug(f"节点标记为已完成: {node_name}")


def get_checkpoint_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """获取断点状态摘要
    
    Args:
        state: 状态字典
    
    Returns:
        断点摘要信息
    """
    completed_nodes = state.get("completed_nodes", [])
    
    return {
        "total_nodes_completed": len(completed_nodes),
        "completed_nodes": completed_nodes,
        "checkpoint_timestamp": state.get("_checkpoint_timestamp"),
        "company_of_interest": state.get("company_of_interest"),
        "trade_date": state.get("trade_date")
    }