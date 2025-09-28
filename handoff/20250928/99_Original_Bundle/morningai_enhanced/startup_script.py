#!/usr/bin/env python3
"""
Morning AI 系統啟動腳本
版本: 2.0 (優化版 + 冷啟動解決方案)
日期: 2025-09-12
作者: Manus AI

這個腳本會自動初始化整個 Morning AI 系統，
包括冷啟動解決方案的智能初始化。
"""

import asyncio
import logging
import sys
import os
import yaml
from pathlib import Path

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """主啟動函數"""
    try:
        logger.info("=== Morning AI 系統啟動 ===")
        
        # 1. 加載配置
        config_path = Path(__file__).parent / "config_optimized.yaml"
        if not config_path.exists():
            logger.error(f"配置文件不存在: {config_path}")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info("配置文件加載成功")
        
        # 2. 執行智能初始化
        logger.info("開始執行智能初始化...")
        
        from smart_initialization import quick_initialize_system
        
        init_success = await quick_initialize_system(
            database_url=config['database_url'],
            force_reinit=False  # 如果已初始化過則跳過
        )
        
        if not init_success:
            logger.error("智能初始化失敗")
            return False
        
        logger.info("智能初始化完成")
        
        # 3. 啟動 Meta-Agent
        logger.info("啟動 Meta-Agent...")
        
        from meta_agent_implementation import MetaAgent
        
        meta_agent = MetaAgent(config)
        
        # 在後台啟動 Meta-Agent
        meta_agent_task = asyncio.create_task(meta_agent.start())
        
        logger.info("Meta-Agent 已啟動")
        
        # 4. 顯示系統狀態
        from smart_initialization import get_smart_initializer
        
        initializer = get_smart_initializer(config['database_url'])
        status = await initializer.get_initialization_status()
        
        logger.info("=== 系統狀態 ===")
        logger.info(f"預訓練策略數量: {status.get('pretrained_strategies_count', 0)}")
        logger.info(f"候選策略總數: {status.get('total_candidate_strategies', 0)}")
        logger.info(f"歷史指標數量: {status.get('historical_metrics_count', 0)}")
        logger.info(f"系統就緒分數: {status.get('system_readiness_score', 0):.1f}/100")
        
        # 5. 導出初始化報告
        report_path = Path(__file__).parent / "initialization_report.json"
        await initializer.export_initialization_report(str(report_path))
        logger.info(f"初始化報告已導出: {report_path}")
        
        logger.info("=== Morning AI 系統啟動完成 ===")
        logger.info("系統現在已準備好處理決策請求")
        
        # 保持運行
        try:
            await meta_agent_task
        except KeyboardInterrupt:
            logger.info("收到停止信號，正在關閉系統...")
            await meta_agent.stop()
            logger.info("系統已安全關閉")
        
        return True
        
    except Exception as e:
        logger.error(f"系統啟動失敗: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

