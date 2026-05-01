#!/usr/bin/env python3
import os
import sys
import logging
import atexit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.logger import setup_logger
from src.web_app import app, start_background_monitor

try:
    from mdns_service import MDNSService
    MDNS_AVAILABLE = True
except ImportError:
    MDNS_AVAILABLE = False
    print("[WARNING] mDNS service not available, install zeroconf: pip install zeroconf")

def main():
    setup_logger(level=logging.INFO)
    logger = logging.getLogger(__name__)

    mdns_service = None
    if MDNS_AVAILABLE:
        try:
            mdns_service = MDNSService()
            if mdns_service.start():
                atexit.register(mdns_service.stop)
        except Exception as e:
            logger.warning(f"mDNS service failed to start: {e}")

    print("=" * 50)
    print(" 天翼网关设备监控系统")
    print("=" * 50)
    print("Access URLs:")
    print("  - http://localhost:5000")
    if MDNS_AVAILABLE and mdns_service:
        print(f"  - http://rosegarden.local:5000 (mDNS)")
    print("  - http://<your-ip>:5000")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    logger.info("Starting background monitor thread...")
    bg_monitor = start_background_monitor()

    if bg_monitor:
        logger.info("Background monitor started, AOM reporting enabled")
    else:
        logger.info("AOM reporting disabled, running Web service only")

    logger.info("Starting Web service...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
