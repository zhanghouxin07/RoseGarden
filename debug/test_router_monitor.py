#!/usr/bin/env python3
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    with open('../config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    print("✓ 配置文件读取成功")
    print(f"  路由器 IP: {config['router']['ip']}")
    print(f"  监测持续时间: {config['monitor']['duration']} 秒")
    print(f"  监测间隔: {config['monitor']['interval']} 秒")
except Exception as e:
    print(f"✗ 配置文件读取失败: {e}")
    sys.exit(1)

# 测试依赖项导入
try:
    import requests
    import psutil
    import pandas as pd
    import matplotlib.pyplot as plt
    from bs4 import BeautifulSoup
    print("✓ 所有依赖项导入成功")
except ImportError as e:
    print(f"✗ 依赖项导入失败: {e}")
    print("  请运行 'pip install -r requirements.txt' 安装依赖项")
    sys.exit(1)

# 测试路由器监测类
try:
    from src.router_monitor import RouterMonitor
    print("✓ 路由器监测类导入成功")
    
    monitor = RouterMonitor(config_file='../config/config.json')
    print("✓ 路由器监测实例创建成功")
    
except Exception as e:
    print(f"✗ 路由器监测类测试失败: {e}")
    sys.exit(1)

print("\n所有测试通过！")
print("请根据实际情况修改 config/config.json 文件中的配置信息，然后运行 'py src/router_monitor.py' 开始监测。")
