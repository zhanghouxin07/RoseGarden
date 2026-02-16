import requests
import time
import json
import psutil
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

class RouterMonitor:
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.router_ip = self.config['router']['ip']
        self.username = self.config['router']['username']
        self.password = self.config['router']['password']
        self.login_url = self.config['router']['login_url']
        self.devices_url = self.config['router']['devices_url']
        
        self.monitor_duration = self.config['monitor']['duration']
        self.monitor_interval = self.config['monitor']['interval']
        self.data_file = self.config['monitor']['data_file']
        self.report_file = self.config['monitor']['report_file']
        
        self.devices_parser = self.config['parsers']['devices']
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.devices = []
        self.data_log = []
    
    def login(self):
        try:
            login_url = f'http://{self.router_ip}{self.login_url}'
            
            login_data = {
                'username': self.username,
                'psd': self.password
            }
            
            response = self.session.post(login_url, data=login_data)
            return response.status_code == 200
        except Exception as e:
            print(f"登录失败: {e}")
            return False
    
    def get_connected_devices(self):
        try:
            devices_url = f'http://{self.router_ip}{self.devices_url}'
            response = self.session.get(devices_url)
            
            devices = []
            data = response.json()
            
            for key, item in data.items():
                if isinstance(item, dict) and 'ip' in item:
                    try:
                        device_info = {
                            'id': key,
                            'ip': item.get(self.devices_parser.get('ip_field', 'ip'), 'N/A'),
                            'mac': item.get(self.devices_parser.get('mac_field', 'mac'), 'N/A'),
                            'type': item.get(self.devices_parser.get('name_field', 'type'), 'N/A'),
                            'system': item.get(self.devices_parser.get('status_field', 'system'), 'N/A'),
                            'up_speed': item.get(self.devices_parser.get('up_speed_field', 'upSpeed'), 0),
                            'down_speed': item.get(self.devices_parser.get('down_speed_field', 'downSpeed'), 0),
                            'ipv6': item.get('ipv6', ''),
                            'restrict': item.get('restrict', False),
                            'black': item.get('black', False)
                        }
                        devices.append(device_info)
                    except Exception as e:
                        print(f"解析设备信息失败: {e}")
                        continue
            
            self.devices = devices
            return devices
        except Exception as e:
            print(f"获取设备列表失败: {e}")
            return []
    
    def monitor_devices(self, duration=None, interval=None):
        actual_duration = duration if duration is not None else self.monitor_duration
        actual_interval = interval if interval is not None else self.monitor_interval
        
        start_time = time.time()
        end_time = start_time + actual_duration
        
        print(f"开始监测设备网速，持续 {actual_duration} 秒，间隔 {actual_interval} 秒...")
        
        while time.time() < end_time:
            try:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                devices = self.get_connected_devices()
                
                for device in devices:
                    data_point = {
                        'timestamp': timestamp,
                        'id': device['id'],
                        'ip': device['ip'],
                        'mac': device['mac'],
                        'type': device['type'],
                        'system': device['system'],
                        'up_speed': device['up_speed'],
                        'down_speed': device['down_speed']
                    }
                    self.data_log.append(data_point)
                    
                    up_speed_kb = device['up_speed'] / 1024
                    down_speed_kb = device['down_speed'] / 1024
                    print(f"[{timestamp}] {device['type']} ({device['ip']}): 上传 {up_speed_kb:.2f} KB/s, 下载 {down_speed_kb:.2f} KB/s")
                
                time.sleep(actual_interval)
            except Exception as e:
                print(f"监测失败: {e}")
                time.sleep(actual_interval)
    
    def save_data(self, filename=None):
        actual_filename = filename if filename is not None else self.data_file
        with open(actual_filename, 'w', encoding='utf-8') as f:
            json.dump(self.data_log, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {actual_filename}")
    
    def generate_report(self, data_file=None):
        try:
            actual_data_file = data_file if data_file is not None else self.data_file
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
            print(f"带宽报告已生成: {self.report_file}")
            
            print("\n连接的设备:")
            print("-" * 80)
            print(f"{'类型':<10} {'IP地址':<18} {'MAC地址':<18} {'系统':<15} {'上传(KB/s)':<12} {'下载(KB/s)':<12}")
            print("-" * 80)
            for device in self.devices:
                print(f"{device['type']:<10} {device['ip']:<18} {device['mac']:<18} {device['system']:<15} {device['up_speed']/1024:<12.2f} {device['down_speed']/1024:<12.2f}")
                
        except Exception as e:
            print(f"生成报告失败: {e}")

if __name__ == '__main__':
    monitor = RouterMonitor()
    
    if monitor.login():
        print("登录成功!")
        
        devices = monitor.get_connected_devices()
        print(f"发现 {len(devices)} 个连接设备\n")
        
        monitor.monitor_devices()
        
        monitor.save_data()
        
        monitor.generate_report()
    else:
        print("登录失败，请检查用户名和密码")
