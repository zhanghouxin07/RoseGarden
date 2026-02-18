import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
CORS(app)

logger = logging.getLogger(__name__)

monitor = None
background_monitor = None

def get_monitor():
    global monitor
    if monitor is None:
        from src.router_monitor import RouterMonitor
        config_path = os.path.join(BASE_DIR, 'config', 'config.json')
        monitor = RouterMonitor(config_file=config_path)
    return monitor

def start_background_monitor():
    global background_monitor
    if background_monitor is None:
        from src.background_monitor import BackgroundMonitor
        
        config_path = os.path.join(BASE_DIR, 'config', 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        collect_interval = config.get('monitor', {}).get('collect_interval', 10)
        aom_interval = config.get('monitor', {}).get('aom_interval', 60)
        aom_enabled = config.get('huaweicloud_aom', {}).get('enabled', False)
        
        mon = get_monitor()
        background_monitor = BackgroundMonitor(
            mon, 
            collect_interval=collect_interval,
            aom_interval=aom_interval
        )
        background_monitor.start()
        
        if aom_enabled:
            logger.info("后台监控线程已启动，AOM上报功能已启用")
        else:
            logger.info("后台监控线程已启动，AOM上报未启用")
    
    return background_monitor

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/devices')
def get_devices():
    global background_monitor
    
    if background_monitor is None:
        return jsonify({'error': '后台监控未启动', 'devices': []}), 500
    
    try:
        devices = background_monitor.get_cached_devices()
        status = background_monitor.get_status()
        
        for device in devices:
            device['online_time_formatted'] = format_online_time(device.get('online_time', 0))
            device['up_speed_formatted'] = format_speed(device.get('up_speed', 0))
            device['down_speed_formatted'] = format_speed(device.get('down_speed', 0))
        
        return jsonify({
            'devices': devices,
            'total': len(devices),
            'timestamp': status.get('last_collect_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        })
    except Exception as e:
        return jsonify({'error': str(e), 'devices': []}), 500

@app.route('/api/network-status')
def get_network_status():
    global background_monitor
    
    if background_monitor is None:
        return jsonify({'error': '后台监控未启动'}), 500
    
    try:
        status = background_monitor.get_cached_network_status()
        
        network_status = {
            'wan_connect': status.get('wan_connect', 'UNKNOWN'),
            'wan_up_time': format_online_time(status.get('wan_up_time', 0)),
            'wired_count': status.get('wired_count', 0),
            'wireless_count': status.get('wireless_count', 0),
            'total_up_speed': format_speed(status.get('total_up_speed', 0)),
            'total_down_speed': format_speed(status.get('total_down_speed', 0)),
            'voip': status.get('voip', False),
            'itv': status.get('itv', False)
        }
        
        return jsonify(network_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor-status')
def get_monitor_status():
    global background_monitor
    
    if background_monitor is None:
        config_path = os.path.join(BASE_DIR, 'config', 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        aom_enabled = config.get('huaweicloud_aom', {}).get('enabled', False)
        
        return jsonify({
            'background_monitor_running': False,
            'aom_enabled': aom_enabled,
            'message': '后台监控未启动'
        })
    
    status = background_monitor.get_status()
    config_path = os.path.join(BASE_DIR, 'config', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return jsonify({
        'background_monitor_running': status['running'],
        'aom_enabled': config.get('huaweicloud_aom', {}).get('enabled', False),
        'collect_interval': status['collect_interval'],
        'aom_interval': status['aom_interval'],
        'last_collect_time': status['last_collect_time'],
        'last_report_time': status['last_report_time'],
        'report_count': status['report_count'],
        'cached_devices_count': status['cached_devices_count']
    })

def format_online_time(seconds):
    if not seconds or seconds <= 0:
        return '0秒'
    
    seconds = int(seconds)
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f'{days}天')
    if hours > 0:
        parts.append(f'{hours}时')
    if minutes > 0:
        parts.append(f'{minutes}分')
    if secs > 0 or not parts:
        parts.append(f'{secs}秒')
    
    return ''.join(parts)

def format_speed(bytes_per_sec):
    if not bytes_per_sec or bytes_per_sec <= 0:
        return '0 B/s'
    
    bytes_per_sec = float(bytes_per_sec)
    if bytes_per_sec < 1024:
        return f'{bytes_per_sec:.0f} B/s'
    elif bytes_per_sec < 1024 * 1024:
        return f'{bytes_per_sec / 1024:.1f} KB/s'
    elif bytes_per_sec < 1024 * 1024 * 1024:
        return f'{bytes_per_sec / (1024 * 1024):.2f} MB/s'
    else:
        return f'{bytes_per_sec / (1024 * 1024 * 1024):.2f} GB/s'
