#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试数据用于验证清理功能
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
import json

def create_test_data():
    """创建测试数据"""
    print("🔧 创建测试数据...")
    
    # 创建结果目录测试数据
    results_dir = Path('./results')
    
    # 创建多个股票的测试数据
    stocks = ['AAPL', 'TSLA', 'MSFT']
    
    for stock in stocks:
        stock_dir = results_dir / stock
        stock_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建过期数据（10天前）
        old_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        old_dir = stock_dir / old_date
        old_dir.mkdir(exist_ok=True)
        
        # 创建测试文件
        test_report = old_dir / 'analysis_report.json'
        test_data = {
            'stock': stock,
            'date': old_date,
            'analysis': 'This is test data for cleanup testing',
            'created_at': datetime.now().isoformat()
        }
        test_report.write_text(json.dumps(test_data, indent=2, ensure_ascii=False))
        
        # 创建更多测试文件
        (old_dir / 'market_data.json').write_text('{"test": "market data"}')
        (old_dir / 'news_analysis.txt').write_text('Test news analysis content')
        
        print(f"   📁 {stock}: {old_dir} ({len(list(old_dir.iterdir()))} 文件)")
        
        # 创建新数据（2天前，应该保留）
        new_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        new_dir = stock_dir / new_date
        new_dir.mkdir(exist_ok=True)
        
        new_report = new_dir / 'analysis_report.json'
        new_data = {
            'stock': stock,
            'date': new_date,
            'analysis': 'This is recent data that should be kept',
            'created_at': datetime.now().isoformat()
        }
        new_report.write_text(json.dumps(new_data, indent=2, ensure_ascii=False))
        
        print(f"   📁 {stock}: {new_dir} (保留数据)")
    
    # 创建checkpoint测试数据
    checkpoint_dir = Path('./checkpoints')
    
    for stock in stocks:
        stock_checkpoint_dir = checkpoint_dir / stock
        stock_checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建过期checkpoint（10天前）
        old_date_str = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
        old_checkpoint = stock_checkpoint_dir / f'checkpoint_{old_date_str}.json'
        checkpoint_data = {
            'stock_code': stock,
            'analysis_date': old_date_str,
            'completed_nodes': ['node1', 'node2'],
            'created_at': datetime.now().isoformat()
        }
        old_checkpoint.write_text(json.dumps(checkpoint_data, indent=2))
        
        # 创建新checkpoint（2天前，应该保留）
        new_date_str = (datetime.now() - timedelta(days=2)).strftime('%Y%m%d')
        new_checkpoint = stock_checkpoint_dir / f'checkpoint_{new_date_str}.json'
        new_checkpoint_data = {
            'stock_code': stock,
            'analysis_date': new_date_str,
            'completed_nodes': ['node1', 'node2', 'node3'],
            'created_at': datetime.now().isoformat()
        }
        new_checkpoint.write_text(json.dumps(new_checkpoint_data, indent=2))
        
        print(f"   💾 {stock}: checkpoint文件已创建")
    
    print("\n✅ 测试数据创建完成！")
    print("\n📊 数据统计:")
    
    # 统计创建的文件
    total_result_files = sum(len(list(d.rglob('*'))) for d in results_dir.iterdir() if d.is_dir())
    total_checkpoint_files = sum(len(list(d.rglob('*.json'))) for d in checkpoint_dir.iterdir() if d.is_dir())
    
    print(f"   结果文件: {total_result_files}")
    print(f"   Checkpoint文件: {total_checkpoint_files}")
    print(f"   股票数量: {len(stocks)}")
    
    return True

if __name__ == '__main__':
    create_test_data()