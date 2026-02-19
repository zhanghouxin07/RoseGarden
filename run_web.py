#!/usr/bin/env python3
import os
import sys
import logging
import atexit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.logger import setup_logger
from src.web_app import app, start_background_monitor

# 尝试导入mDNS服务
try:
    from mdns_service import MDNSService
    MDNS_AVAILABLE = True
except ImportError:
    MDNS_AVAILABLE = False
    print("⚠️  mDNS服务不可用，请安装zeroconf: pip install zeroconf")

def main():
    setup_logger(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 启动mDNS服务
    mdns_service = None
    if MDNS_AVAILABLE:
        try:
            mdns_service = MDNSService()
            if mdns_service.start():
                atexit.register(mdns_service.stop)
        except Exception as e:
            logger.warning(f"mDNS服务启动失败: {e}")
    
    print("=" * 50)
    print("天翼网关设备监控系统")
    print("=" * 50)
    print("访问地址:")
    print("  • http://localhost:5000")
    if MDNS_AVAILABLE and mdns_service:
        print(f"  • http://rosegarden.local:5000 (mDNS)")
    print("  • http://<您的IP地址>:5000")
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
