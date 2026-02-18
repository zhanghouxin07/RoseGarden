import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from logger import setup_logger
from router_monitor import RouterMonitor

logger = logging.getLogger(__name__)


def main():
    logger.info("启动路由器监控程序")
    
    monitor = RouterMonitor()
    
    if monitor.login():
        monitor.get_connected_devices()
        
        monitor.monitor_devices()
        
        monitor.save_data()
        
        monitor.generate_report()
    else:
        logger.error("登录失败，请检查用户名和密码")
    
    logger.info("程序结束")


if __name__ == '__main__':
    setup_logger(level=logging.DEBUG)
    main()
