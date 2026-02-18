import requests
import time
import json
import logging
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 请修改这里 ---
ROUTER_IP = '192.168.1.1'
USERNAME = 'useradmin'
PASSWORD = 'mt46s'
# -----------------

def monitor_with_heartbeat():
    session = requests.Session()
    
    # 1. 极度拟真的 Headers (非常重要)
    # 有些路由器会检测 Referer，如果不是来自 /admin/home，就不启动统计服务
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': f'http://{ROUTER_IP}/cgi-bin/luci/admin/home', # 伪装成是从首页发起的
        'Origin': f'http://{ROUTER_IP}'
    })

    # 2. 登录
    try:
        logger.info("正在登录...")
        login_url = f'http://{ROUTER_IP}/cgi-bin/luci'
        # 注意：这里根据你的路由器情况，可能是 username/psd 或者是 luci_username/luci_password
        # 如果你之前能登录成功，这里保持不变即可
        login_data = {'username': USERNAME, 'psd': PASSWORD} 
        
        resp = session.post(login_url, data=login_data)
        if resp.status_code != 200:
            logger.error(f"登录失败: {resp.status_code}")
            return
    except Exception as e:
        logger.error(f"连接异常: {e}")
        return

    logger.info("登录成功，开始模拟浏览器心跳...")
    
    # 3. 连续请求循环
    allinfo_url = f'http://{ROUTER_IP}/cgi-bin/luci/admin/allInfo'
    
    for i in range(1, 6): # 尝试循环 5 次
        try:
            # 加上时间戳参数，防止 requests 库读取本地缓存
            target_url = f"{allinfo_url}?_={random.random()}"
            
            resp = session.get(target_url)
            data = resp.json()
            
            # 提取速度非 0 的设备
            active_devices = []
            for key, item in data.items():
                if isinstance(item, dict) and ('upSpeed' in item or 'downSpeed' in item):
                    # 注意：有些固件返回的是字符串 "1024"，需要转 int
                    u = int(item.get('upSpeed', 0))
                    d = int(item.get('downSpeed', 0))
                    
                    if u > 0 or d > 0:
                        name = item.get('devName', 'Unknown')
                        active_devices.append(f"{name} (↑{u} ↓{d})")
            
            print(f"\n--- 第 {i} 次心跳探测 ---")
            if active_devices:
                logger.info(f"发现活跃设备: {', '.join(active_devices)}")
            else:
                logger.warning("当前所有设备速度均为 0 (可能是刚唤醒统计服务)")
                
            # 关键：检查总速度
            total_up = data.get('tWUp', 0)
            total_down = data.get('tWDown', 0)
            print(f"路由器总速: 上传 {total_up}, 下载 {total_down}")

            # 4. 等待 2 秒，给路由器计算下一秒速度的时间
            time.sleep(5)

        except Exception as e:
            logger.error(f"请求报错: {e}")
            break

if __name__ == '__main__':
    monitor_with_heartbeat()