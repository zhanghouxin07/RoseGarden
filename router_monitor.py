import requests
import time
import json
import random
import pandas as pd
import matplotlib.pyplot as plt
import logging
from datetime import datetime
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.http.http_config import HttpConfig
from huaweicloudsdkaom.v2.region.aom_region import AomRegion
from huaweicloudsdkaom.v2 import AomClient, AddMetricDataRequest, MetricDataItem, MetricItemInfo, Dimension2, ValueData

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class AOMReporter:
    def __init__(self, config):
        self.enabled = config.get('enabled', False)
        self.region = config.get('region', 'ap-southeast-1')
        self.project_id = config.get('project_id', '')
        self.ak = config.get('ak', '')
        self.sk = config.get('sk', '')
        
        logger.debug(f"AOM Reporter 初始化: enabled={self.enabled}, region={self.region}, project_id={self.project_id}")
        
        if self.enabled:
            self._init_client()
    
    def _init_client(self):
        config = HttpConfig.get_default_config()
        config.ignore_ssl_verification = True
        
        credentials = BasicCredentials(self.ak, self.sk, self.project_id)
        
        region = AomRegion.value_of(self.region)
        
        logger.debug(f"AOM 客户端初始化: region={region}")
        
        self.client = AomClient.new_builder() \
            .with_http_config(config) \
            .with_credentials(credentials) \
            .with_region(region) \
            .build()
    
    def push_metrics(self, metrics):
        if not self.enabled:
            return False
        
        try:
            collect_time = int(time.time() * 1000)
            
            logger.debug(f"AOM上报时间戳: {collect_time}")
            logger.debug(f"AOM上报指标数量: {len(metrics)}")
            
            metric_data_items = []
            for metric in metrics:
                name = metric['name']
                value = metric['value']
                labels = metric.get('labels', {})
                
                dimensions = []
                for key, val in labels.items():
                    dim_name = str(key)[:32] if len(str(key)) > 32 else str(key)
                    dim_value = str(val)[:64] if len(str(val)) > 64 else str(val)
                    if dim_name and dim_value:
                        dimensions.append(Dimension2(
                            name=dim_name,
                            value=dim_value
                        ))
                
                if not dimensions:
                    dimensions = [Dimension2(name='default', value='router')]
                
                metric_value = int(value) if isinstance(value, int) else float(value) if isinstance(value, (int, float)) else 0
                
                metric_item = MetricDataItem(
                    collect_time=collect_time,
                    metric=MetricItemInfo(
                        namespace='RoseGarden.Router',
                        dimensions=dimensions
                    ),
                    values=[ValueData(
                        metric_name=name,
                        type='int',
                        unit='Bytes/s',
                        value=metric_value
                    )]
                )
                
                metric_data_items.append(metric_item)
                
                logger.debug(f"指标: {name}={value}, 维度: {labels}")
            
            request = AddMetricDataRequest(body=metric_data_items)
            
            logger.debug(f"发送AOM请求: namespace=RoseGarden.Router, 指标数={len(metric_data_items)}")
            
            response = self.client.add_metric_data(request)
            
            logger.debug(f"AOM响应状态码: {response.status_code}")
            logger.debug(f"AOM响应体: {response}")
            
            if response.status_code in [200, 201, 202, 204]:
                logger.info(f"AOM上报成功: {len(metrics)} 个指标")
                return True
            else:
                logger.error(f"AOM上报失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"AOM上报异常: {e}")
            return False


class RouterMonitor:
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.router_ip = self.config['router']['ip']
        self.username = self.config['router']['username']
        self.password = self.config['router']['password']
        self.login_url = self.config['router']['login_url']
        self.devices_url = self.config['router']['devices_url']
        self.device_detail_url = self.config['router'].get('device_detail_url', '')
        
        self.monitor_duration = self.config['monitor']['duration']
        self.monitor_interval = self.config['monitor']['interval']
        self.data_file = self.config['monitor']['data_file']
        self.report_file = self.config['monitor']['report_file']
        
        self.devices_parser = self.config['parsers']['devices']
        
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
            logger.debug(f"登录请求参数: {login_data}")
            logger.debug(f"请求头: {dict(self.session.headers)}")
            
            response = self.session.post(login_url, data=login_data)
            
            logger.debug(f"登录响应状态码: {response.status_code}")
            logger.debug(f"登录响应 Cookies: {dict(self.session.cookies)}")
            
            if response.status_code == 200:
                logger.info("路由器登录成功")
                return True
            else:
                logger.error(f"路由器登录失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"登录异常: {e}")
            return False
    
    def get_connected_devices(self):
        try:
            random_param = random.random()
            
            self.session.headers['Referer'] = f'http://{self.router_ip}/cgi-bin/luci/admin/device/pc?ip=192.168.1.1'
            devices_url = f'http://{self.router_ip}{self.devices_url}?type=0&_={random_param}'
            
            logger.debug(f"获取设备网速请求 URL: {devices_url}")
            
            response = self.session.get(devices_url)
            
            logger.debug(f"响应状态码: {response.status_code}")
            logger.debug(f"响应长度: {len(response.text)} 字符")
            
            devices = []
            speed_data = response.json()
            
            logger.debug(f"解析到的设备数据键: {list(speed_data.keys())}")
            
            device_details = {}
            if self.device_detail_url:
                try:
                    self.session.headers['Referer'] = f'http://{self.router_ip}/cgi-bin/luci/admin/home'
                    detail_url = f'http://{self.router_ip}{self.device_detail_url}?_={random.random()}'
                    logger.debug(f"获取设备详情请求 URL: {detail_url}")
                    detail_response = self.session.get(detail_url)
                    detail_data = detail_response.json()
                    
                    skip_keys = {'tWUp', 'tWDown', 'tWlUp', 'tWlDown', 'wcount', 'wlcount', 
                                'scount', 'wanUpTime', 'wanConnect', 'voip', 'itv'}
                    
                    for key, item in detail_data.items():
                        if key in skip_keys:
                            continue
                        if isinstance(item, dict) and 'ip' in item:
                            device_details[item.get('ip')] = {
                                'name': item.get('devName', ''),
                                'brand': item.get('brand', ''),
                                'model': item.get('model', ''),
                                'online_time': item.get('onlineTime', 0)
                            }
                    logger.debug(f"获取到 {len(device_details)} 个设备详情")
                except Exception as e:
                    logger.warning(f"获取设备详情失败: {e}")
            
            skip_keys = {'count', 'curip'}
            
            for key, item in speed_data.items():
                if key in skip_keys:
                    continue
                if isinstance(item, dict) and 'ip' in item:
                    try:
                        ip = item.get('ip', 'N/A')
                        detail = device_details.get(ip, {})
                        
                        device_info = {
                            'id': key,
                            'ip': ip,
                            'mac': item.get('mac', 'N/A'),
                            'type': item.get('type', 'N/A'),
                            'name': detail.get('name') or item.get('devName', 'N/A'),
                            'brand': detail.get('brand', 'N/A'),
                            'model': detail.get('model') or item.get('system', 'N/A'),
                            'system': item.get('system', 'N/A'),
                            'online_time': detail.get('online_time', 0),
                            'up_speed': item.get('upSpeed', 0),
                            'down_speed': item.get('downSpeed', 0),
                            'ipv6': item.get('ipv6', ''),
                            'restrict': item.get('restrict', False),
                            'black': item.get('black', False)
                        }
                        devices.append(device_info)
                        
                        if device_info['up_speed'] > 0 or device_info['down_speed'] > 0:
                            logger.debug(f"设备 {key} ({ip}) 有网速活动: 上传={device_info['up_speed']}, 下载={device_info['down_speed']}")
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
    
    def monitor_devices(self, duration=None, interval=None):
        actual_duration = duration if duration is not None else self.monitor_duration
        actual_interval = interval if interval is not None else self.monitor_interval
        
        start_time = time.time()
        end_time = start_time + actual_duration
        
        logger.info(f"开始监测设备网速，持续 {actual_duration} 秒，间隔 {actual_interval} 秒")
        
        while time.time() < end_time:
            try:
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
                
                self.push_to_aom(devices)
                
                remaining = int(end_time - time.time())
                logger.debug(f"剩余监控时间: {remaining} 秒")
                
                time.sleep(actual_interval)
            except Exception as e:
                logger.error(f"监测失败: {e}")
                time.sleep(actual_interval)
        
        logger.info("监控完成")
    
    def save_data(self, filename=None):
        actual_filename = filename if filename is not None else self.data_file
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

if __name__ == '__main__':
    logger.info("启动路由器监控程序")
    
    monitor = RouterMonitor()
    
    if monitor.login():
        devices = monitor.get_connected_devices()
        
        monitor.monitor_devices()
        
        monitor.save_data()
        
        monitor.generate_report()
    else:
        logger.error("登录失败，请检查用户名和密码")
    
    logger.info("程序结束")
