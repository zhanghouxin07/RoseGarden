import requests
import time
import json
import random
import pandas as pd
import matplotlib.pyplot as plt
import logging
import os
from datetime import datetime
try:
    from .aom_reporter import AOMReporter
except ImportError:
    from aom_reporter import AOMReporter

logger = logging.getLogger(__name__)


class RouterMonitor:
    def __init__(self, config_file='config/config.json'):
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.router_ip = self.config['router']['ip']
        self.username = self.config['router']['username']
        self.password = self.config['router']['password']
        self.login_url = self.config['router']['login_url']
        self.allinfo_url = self.config['router'].get('allinfo_url', '/cgi-bin/luci/admin/allInfo')
        
        self.monitor_duration = self.config['monitor']['duration']
        self.collect_interval = self.config['monitor'].get('collect_interval', 10)
        self.aom_interval = self.config['monitor'].get('aom_interval', 60)
        self.data_file = os.path.join('data', self.config['monitor']['data_file'])
        self.report_file = os.path.join('output', self.config['monitor']['report_file'])
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'http://{self.router_ip}/cgi-bin/luci/admin/home'
        })
        self.devices = []
        self.data_log = []
        
        self.aom_reporter = AOMReporter(self.config.get('huaweicloud_aom', {}))
    
    def login(self):
        try:
            login_url = f'http://{self.router_ip}{self.login_url}'
            
            login_data = {
                'username': self.username,
                'psd': self.password
            }
            
            logger.debug(f"登录请求 URL: {login_url}")
            logger.debug(f"登录用户名: {self.username}")
            
            response = self.session.post(login_url, data=login_data)
            
            logger.debug(f"登录响应状态码: {response.status_code}")
            logger.debug(f"登录响应长度: {len(response.text)} 字符")
            logger.debug(f"登录响应内容预览: {response.text[:200] if len(response.text) > 200 else response.text}")
            logger.debug(f"登录响应 Cookies: {dict(self.session.cookies)}")
            
            if response.status_code == 200:
                if 'sysauth' in self.session.cookies:
                    logger.info("路由器登录成功")
                    return True
                else:
                    logger.error("登录成功但未获取到有效Cookie，可能用户名或密码错误")
                    return False
            else:
                logger.error(f"路由器登录失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"登录异常: {e}")
            return False
    
    def get_connected_devices(self):
        try:
            random_param = random.random()
            
            self.session.headers['Referer'] = f'http://{self.router_ip}/cgi-bin/luci/admin/home'
            allinfo_url = f'http://{self.router_ip}{self.allinfo_url}?_={random_param}'
            
            logger.debug(f"获取设备信息请求 URL: {allinfo_url}")
            
            response = self.session.get(allinfo_url)
            
            logger.debug(f"响应状态码: {response.status_code}")
            logger.debug(f"响应长度: {len(response.text)} 字符")
            logger.debug(f"响应内容预览: {response.text[:500] if len(response.text) > 500 else response.text}")
            
            if not response.text.strip():
                logger.error("响应内容为空，可能登录已过期")
                return []
            
            try:
                data = response.json()
            except Exception as json_err:
                logger.error(f"JSON解析失败: {json_err}")
                logger.error(f"响应内容类型: {response.headers.get('Content-Type', 'unknown')}")
                logger.error(f"完整响应内容: {response.text}")
                return []
            
            logger.debug(f"解析到的数据键: {list(data.keys())}")
            
            devices = []
            skip_keys = {'tWUp', 'tWDown', 'tWlUp', 'tWlDown', 'wcount', 'wlcount', 
                        'scount', 'wanUpTime', 'wanConnect', 'voip', 'itv'}
            
            for key, item in data.items():
                if key in skip_keys:
                    continue
                if isinstance(item, dict) and 'ip' in item:
                    try:
                        device_info = {
                            'id': key,
                            'ip': item.get('ip', 'N/A'),
                            'mac': item.get('mac', 'N/A'),
                            'type': item.get('type', 'N/A'),
                            'name': item.get('devName', 'N/A'),
                            'brand': item.get('brand', 'N/A'),
                            'model': item.get('model', 'N/A'),
                            'system': item.get('system', 'N/A'),
                            'online_time': item.get('onlineTime', 0),
                            'up_speed': item.get('upSpeed', 0),
                            'down_speed': item.get('downSpeed', 0),
                            'ipv6': item.get('ipv6', ''),
                            'restrict': item.get('restrict', False),
                            'black': item.get('black', False)
                        }
                        devices.append(device_info)
                        
                        if device_info['up_speed'] > 0 or device_info['down_speed'] > 0:
                            logger.debug(f"设备 {key} ({device_info['ip']}) 有网速活动: 上传={device_info['up_speed']}, 下载={device_info['down_speed']}")
                    except Exception as e:
                        logger.error(f"解析设备信息失败: {e}")
                        continue
            
            self.devices = devices
            logger.info(f"获取到 {len(devices)} 个连接设备")
            return devices
        except Exception as e:
            logger.error(f"获取设备列表失败: {e}")
            return []
    
    def push_to_aom(self, devices):
        if not self.aom_reporter.enabled:
            logger.debug("AOM上报未启用，跳过")
            return
        
        logger.debug(f"准备上报 {len(devices)} 个设备的指标到AOM")
        
        metrics = []
        
        for device in devices:
            labels = {
                'device_id': device['id'],
                'device_ip': device['ip'],
                'device_name': device['name'],
                'device_brand': device['brand'],
                'device_model': device['model'],
                'device_type': device['type']
            }
            
            metrics.append({
                'name': 'device_up_speed',
                'value': device['up_speed'],
                'labels': labels
            })
            
            metrics.append({
                'name': 'device_down_speed',
                'value': device['down_speed'],
                'labels': labels
            })
            
            metrics.append({
                'name': 'device_online_time',
                'value': device['online_time'],
                'labels': labels
            })
        
        total_up = sum(d['up_speed'] for d in devices)
        total_down = sum(d['down_speed'] for d in devices)
        device_count = len(devices)
        
        metrics.append({
            'name': 'total_up_speed',
            'value': total_up,
            'labels': {}
        })
        
        metrics.append({
            'name': 'total_down_speed',
            'value': total_down,
            'labels': {}
        })
        
        metrics.append({
            'name': 'device_count',
            'value': device_count,
            'labels': {}
        })
        
        logger.debug(f"总上传速度: {total_up} Bytes/s, 总下载速度: {total_down} Bytes/s")
        
        if self.aom_reporter.push_metrics(metrics):
            logger.info(f"已上报 {len(metrics)} 个指标到华为云AOM")
    
    def monitor_devices(self, duration=None, collect_interval=None, aom_interval=None):
        actual_duration = duration if duration is not None else self.monitor_duration
        actual_collect_interval = collect_interval if collect_interval is not None else self.collect_interval
        actual_aom_interval = aom_interval if aom_interval is not None else self.aom_interval
        
        start_time = time.time()
        end_time = start_time + actual_duration
        last_aom_time = 0
        
        logger.info(f"开始监测设备网速，持续 {actual_duration} 秒")
        logger.info(f"采集间隔: {actual_collect_interval} 秒, AOM上报间隔: {actual_aom_interval} 秒")
        
        while time.time() < end_time:
            try:
                current_time = time.time()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                devices = self.get_connected_devices()
                
                for device in devices:
                    data_point = {
                        'timestamp': timestamp,
                        'id': device['id'],
                        'ip': device['ip'],
                        'name': device['name'],
                        'brand': device['brand'],
                        'model': device['model'],
                        'type': device['type'],
                        'online_time': device['online_time'],
                        'up_speed': device['up_speed'],
                        'down_speed': device['down_speed']
                    }
                    self.data_log.append(data_point)
                    
                    up_speed_kb = device['up_speed'] / 1024
                    down_speed_kb = device['down_speed'] / 1024
                    logger.info(f"[{timestamp}] {device['name']} ({device['ip']}): 上传 {up_speed_kb:.2f} KB/s, 下载 {down_speed_kb:.2f} KB/s")
                
                if current_time - last_aom_time >= actual_aom_interval:
                    self.push_to_aom(devices)
                    last_aom_time = current_time
                    logger.info(f"AOM上报完成，下次上报将在 {actual_aom_interval} 秒后")
                
                remaining = int(end_time - time.time())
                logger.debug(f"剩余监控时间: {remaining} 秒")
                
                time.sleep(actual_collect_interval)
            except Exception as e:
                logger.error(f"监测失败: {e}")
                time.sleep(actual_collect_interval)
        
        logger.info("监控完成")
    
    def save_data(self, filename=None):
        actual_filename = filename if filename is not None else self.data_file
        os.makedirs(os.path.dirname(actual_filename), exist_ok=True)
        with open(actual_filename, 'w', encoding='utf-8') as f:
            json.dump(self.data_log, f, ensure_ascii=False, indent=2)
        logger.info(f"数据已保存到 {actual_filename}")
    
    def generate_report(self, data_file=None):
        try:
            actual_data_file = data_file if data_file is not None else self.data_file
            logger.debug(f"读取数据文件: {actual_data_file}")
            
            with open(actual_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            plt.figure(figsize=(14, 10))
            
            devices = df['id'].unique()
            colors = plt.cm.tab10(range(len(devices)))
            
            plt.subplot(2, 1, 1)
            for i, device_id in enumerate(devices):
                device_data = df[df['id'] == device_id]
                device_type = device_data['type'].iloc[0]
                device_ip = device_data['ip'].iloc[0]
                plt.plot(device_data['timestamp'], device_data['up_speed']/1024, 
                        label=f'{device_type} ({device_ip})', color=colors[i % len(colors)])
            plt.title('设备上传速度 (KB/s)')
            plt.xlabel('时间')
            plt.ylabel('速度 (KB/s)')
            plt.legend(loc='upper right', fontsize=8)
            plt.grid(True)
            
            plt.subplot(2, 1, 2)
            for i, device_id in enumerate(devices):
                device_data = df[df['id'] == device_id]
                device_type = device_data['type'].iloc[0]
                device_ip = device_data['ip'].iloc[0]
                plt.plot(device_data['timestamp'], device_data['down_speed']/1024, 
                        label=f'{device_type} ({device_ip})', color=colors[i % len(colors)])
            plt.title('设备下载速度 (KB/s)')
            plt.xlabel('时间')
            plt.ylabel('速度 (KB/s)')
            plt.legend(loc='upper right', fontsize=8)
            plt.grid(True)
            
            plt.tight_layout()
            os.makedirs(os.path.dirname(self.report_file), exist_ok=True)
            plt.savefig(self.report_file)
            logger.info(f"带宽报告已生成: {self.report_file}")
            
            logger.info("连接的设备汇总:")
            print("-" * 100)
            print(f"{'名称':<15} {'品牌':<8} {'型号':<20} {'IP地址':<18} {'在线时间':<12} {'上传(KB/s)':<12} {'下载(KB/s)':<12}")
            print("-" * 100)
            for device in self.devices:
                online_hours = device['online_time'] // 3600
                online_mins = (device['online_time'] % 3600) // 60
                online_str = f"{online_hours}h{online_mins}m"
                print(f"{device['name']:<15} {device['brand']:<8} {device['model']:<20} {device['ip']:<18} {online_str:<12} {device['up_speed']/1024:<12.2f} {device['down_speed']/1024:<12.2f}")
                
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
