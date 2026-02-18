#!/usr/bin/env python3
import requests
import json
import re

def test_router_api():
    router_ip = "192.168.1.1"
    username = "useradmin"
    password = "mt46s"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    })
    
    print("=" * 60)
    print("步骤 1: 获取登录页面")
    print("=" * 60)
    
    login_url = f"http://{router_ip}/cgi-bin/luci"
    
    try:
        response = session.get(login_url, timeout=10)
        print(f"状态码: {response.status_code}")
        
        # 查找可能的 token 或隐藏字段
        token_match = re.search(r'name="token"\s+value="([^"]*)"', response.text)
        if token_match:
            print(f"找到 token: {token_match.group(1)}")
        
        # 查找表单字段
        form_fields = re.findall(r'<input[^>]*name="([^"]*)"[^>]*>', response.text)
        print(f"表单字段: {form_fields}")
        
    except Exception as e:
        print(f"获取登录页面失败: {e}")
        return
    
    print("\n" + "=" * 60)
    print("步骤 2: 尝试登录 (方式1: username/psd)")
    print("=" * 60)
    
    login_data = {
        'username': username,
        'psd': password
    }
    
    try:
        response = session.post(login_url, data=login_data, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        # 检查是否登录成功（通过检查响应是否为登录页面）
        if 'login' in response.text.lower() and 'password' in response.text.lower():
            print("响应仍然是登录页面，登录可能失败")
        else:
            print("登录可能成功!")
            
    except Exception as e:
        print(f"登录失败: {e}")
        return
    
    print("\n" + "=" * 60)
    print("步骤 3: 测试设备信息接口")
    print("=" * 60)
    
    devices_url = f"http://{router_ip}/cgi-bin/luci/admin/device/devInfo?type=0"
    print(f"\n请求URL: {devices_url}")
    
    try:
        response = session.get(devices_url, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        print("\n响应内容前500字符:")
        print("-" * 40)
        print(response.text[:500])
        
        try:
            data = response.json()
            print("\n解析为 JSON 成功!")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
        except json.JSONDecodeError:
            print("\n响应不是 JSON 格式")
            
            # 检查是否被重定向到登录页面
            if 'login' in response.text.lower():
                print("响应包含登录页面内容，可能需要先登录")
                
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n" + "=" * 60)
    print("步骤 4: 尝试其他可能的接口")
    print("=" * 60)
    
    # 尝试其他可能的设备信息接口
    test_urls = [
        f"http://{router_ip}/cgi-bin/luci/admin/status/overview",
        f"http://{router_ip}/cgi-bin/luci/admin/network/wireless",
        f"http://{router_ip}/cgi-bin/luci/admin/system/system",
    ]
    
    for url in test_urls:
        print(f"\n尝试: {url}")
        try:
            response = session.get(url, timeout=5)
            print(f"  状态码: {response.status_code}")
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                print(f"  Content-Type: {content_type}")
                if 'json' in content_type:
                    print(f"  JSON 响应: {response.text[:200]}")
        except Exception as e:
            print(f"  失败: {e}")

if __name__ == '__main__':
    test_router_api()
