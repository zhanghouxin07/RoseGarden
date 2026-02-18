#!/usr/bin/env python3
import requests
import json
import random
from collections import defaultdict

def test_gateway_api():
    router_ip = "192.168.1.1"
    username = "useradmin"
    password = "mt46s"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'X-Requested-With': 'XMLHttpRequest',
    })
    
    print("=" * 70)
    print("步骤 1: 登录天翼网关")
    print("=" * 70)
    
    login_url = f"http://{router_ip}/cgi-bin/luci"
    login_data = {
        'username': username,
        'psd': password
    }
    
    try:
        response = session.post(login_url, data=login_data, timeout=10)
        print(f"登录状态码: {response.status_code}")
        if response.status_code == 200:
            print("登录成功!")
        else:
            print("登录可能失败")
            return
    except Exception as e:
        print(f"登录失败: {e}")
        return
    
    print("\n" + "=" * 70)
    print("步骤 2: 获取设备信息 (allInfo 接口)")
    print("=" * 70)
    
    random_param = random.random()
    allinfo_url = f"http://{router_ip}/cgi-bin/luci/admin/allInfo?_={random_param}"
    
    try:
        response = session.get(allinfo_url, timeout=10)
        print(f"请求状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if not response.text.strip():
            print("响应内容为空!")
            return
            
        data = response.json()
        
        print("\n" + "=" * 70)
        print("步骤 3: 分析原始返回数据")
        print("=" * 70)
        
        print(f"\n返回数据的顶层键 (共 {len(data)} 个):")
        print("-" * 50)
        for key in sorted(data.keys()):
            value = data[key]
            if isinstance(value, dict):
                print(f"  {key}: dict, 包含 {len(value)} 个子键")
            elif isinstance(value, list):
                print(f"  {key}: list, 长度 {len(value)}")
            elif isinstance(value, str):
                preview = value[:30] + "..." if len(value) > 30 else value
                print(f"  {key}: str = '{preview}'")
            else:
                print(f"  {key}: {type(value).__name__} = {value}")
        
        print("\n" + "=" * 70)
        print("步骤 4: 分析设备信息")
        print("=" * 70)
        
        skip_keys = {'tWUp', 'tWDown', 'tWlUp', 'tWlDown', 'wcount', 'wlcount', 
                    'scount', 'wanUpTime', 'wanConnect', 'voip', 'itv'}
        
        device_keys = [k for k in data.keys() if k not in skip_keys]
        print(f"\n可能的设备键 (共 {len(device_keys)} 个): {device_keys}")
        
        all_fields = set()
        field_examples = defaultdict(set)
        device_types = defaultdict(int)
        device_systems = defaultdict(int)
        device_brands = defaultdict(int)
        
        devices = []
        
        for key in device_keys:
            item = data[key]
            if isinstance(item, dict):
                if 'ip' in item:
                    devices.append((key, item))
                    for field, value in item.items():
                        all_fields.add(field)
                        if value and str(value).strip() and str(value) not in ['N/A', '']:
                            field_examples[field].add(str(value)[:50])
        
        print(f"\n找到 {len(devices)} 个设备")
        
        print("\n" + "-" * 50)
        print("设备信息的所有字段:")
        print("-" * 50)
        for field in sorted(all_fields):
            examples = list(field_examples[field])[:3]
            print(f"  {field}:")
            for ex in examples:
                print(f"    示例: {ex}")
        
        print("\n" + "=" * 70)
        print("步骤 5: 统计设备类型分布")
        print("=" * 70)
        
        for key, item in devices:
            dtype = item.get('type', 'unknown')
            dsys = item.get('system', 'unknown')
            dbrand = item.get('brand', 'unknown')
            device_types[dtype or 'unknown'] += 1
            device_systems[dsys or 'unknown'] += 1
            device_brands[dbrand or 'unknown'] += 1
        
        print("\n设备类型 (type) 分布:")
        print("-" * 50)
        for dtype, count in sorted(device_types.items(), key=lambda x: -x[1]):
            print(f"  {dtype or '(空)'}: {count} 个")
        
        print("\n设备系统 (system) 分布:")
        print("-" * 50)
        for dsys, count in sorted(device_systems.items(), key=lambda x: -x[1]):
            print(f"  {dsys or '(空)'}: {count} 个")
        
        print("\n设备品牌 (brand) 分布:")
        print("-" * 50)
        for dbrand, count in sorted(device_brands.items(), key=lambda x: -x[1]):
            print(f"  {dbrand or '(空)'}: {count} 个")
        
        print("\n" + "=" * 70)
        print("步骤 6: 显示完整设备信息示例")
        print("=" * 70)
        
        for i, (key, item) in enumerate(devices[:3]):
            print(f"\n设备 {i+1} (键: {key}):")
            print("-" * 50)
            for field, value in sorted(item.items()):
                print(f"  {field}: {value}")
        
        print("\n" + "=" * 70)
        print("步骤 7: 分析非设备数据 (网络状态等)")
        print("=" * 70)
        
        for key in skip_keys:
            if key in data:
                print(f"\n{key}:")
                value = data[key]
                if isinstance(value, dict):
                    for k, v in value.items():
                        print(f"  {k}: {v}")
                else:
                    print(f"  值: {value}")
        
        print("\n" + "=" * 70)
        print("完整原始 JSON 数据:")
        print("=" * 70)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"获取设备信息失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_gateway_api()
