#!/usr/bin/env python3
import os
import sys
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.logger import setup_logger
from src.web_app import app, start_background_monitor

def main():
    setup_logger(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    print("=" * 50)
    print("天翼网关设备监控系统")
    print("=" * 50)
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    
    logger.info("启动后台监控线程...")
    bg_monitor = start_background_monitor()
    
    if bg_monitor:
        logger.info("后台监控线程已启动，AOM上报功能已启用")
    else:
        logger.info("AOM上报未启用，仅运行Web服务")
    
    logger.info("启动Web服务...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
