import threading
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BackgroundMonitor(threading.Thread):
    def __init__(self, monitor, collect_interval=10, aom_interval=60):
        super().__init__(daemon=True)
        self.monitor = monitor
        self.collect_interval = collect_interval
        self.aom_interval = aom_interval
        self._running = False
        self._stop_event = threading.Event()
        
        self._cached_devices = []
        self._cached_network_status = {}
        self._last_collect_time = None
        self._last_report_time = None
        self._report_count = 0
        self._lock = threading.Lock()
        
    def run(self):
        self._running = True
        logger.info(f"后台监控线程启动，采集间隔: {self.collect_interval}秒, AOM上报间隔: {self.aom_interval}秒")
        
        last_aom_time = 0
        
        while not self._stop_event.is_set():
            try:
                current_time = time.time()
                
                self._collect_data()
                
                if current_time - last_aom_time >= self.aom_interval:
                    self._report_to_aom()
                    last_aom_time = current_time
                
            except Exception as e:
                logger.error(f"监控周期异常: {e}")
            
            self._stop_event.wait(self.collect_interval)
        
        self._running = False
        logger.info("后台监控线程已停止")
    
    def _collect_data(self):
        if not self.monitor.login():
            logger.warning("后台监控登录失败，跳过本次采集")
            return
        
        devices = self.monitor.get_connected_devices()
        
        import random
        random_param = random.random()
        allinfo_url = f'http://{self.monitor.router_ip}{self.monitor.allinfo_url}?_={random_param}'
        self.monitor.session.headers['Referer'] = f'http://{self.monitor.router_ip}/cgi-bin/luci/admin/home'
        
        response = self.monitor.session.get(allinfo_url)
        data = response.json()
        
        network_status = {
            'wan_connect': data.get('wanConnect', 'UNKNOWN'),
            'wan_up_time': data.get('wanUpTime', 0),
            'wired_count': data.get('wcount', 0),
            'wireless_count': data.get('wlcount', 0),
            'total_up_speed': data.get('tWUp', 0),
            'total_down_speed': data.get('tWDown', 0),
            'voip': data.get('voip', False),
            'itv': data.get('itv', False)
        }
        
        with self._lock:
            self._cached_devices = devices
            self._cached_network_status = network_status
            self._last_collect_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logger.debug(f"数据采集完成，设备数: {len(devices)}")
    
    def _report_to_aom(self):
        with self._lock:
            devices = self._cached_devices.copy()
        
        if devices:
            self.monitor.push_to_aom(devices)
            self._report_count += 1
            self._last_report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"AOM上报完成 (第{self._report_count}次)，设备数: {len(devices)}")
    
    def get_cached_devices(self):
        with self._lock:
            return self._cached_devices.copy()
    
    def get_cached_network_status(self):
        with self._lock:
            return self._cached_network_status.copy()
    
    def stop(self):
        logger.info("正在停止后台监控线程...")
        self._stop_event.set()
    
    def get_status(self):
        with self._lock:
            return {
                'running': self._running,
                'collect_interval': self.collect_interval,
                'aom_interval': self.aom_interval,
                'last_collect_time': self._last_collect_time,
                'last_report_time': self._last_report_time,
                'report_count': self._report_count,
                'cached_devices_count': len(self._cached_devices)
            }
