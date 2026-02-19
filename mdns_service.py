#!/usr/bin/env python3
import socket
import time
import threading
from zeroconf import ServiceInfo, Zeroconf

class MDNSService:
    def __init__(self, service_name="rosegarden", service_type="_http._tcp.local.", port=5000):
        self.service_name = service_name
        self.service_type = service_type
        self.port = port
        self.zeroconf = None
        self.service_info = None
        
    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            # 创建一个临时socket连接来获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def start(self):
        """启动mDNS服务"""
        try:
            local_ip = self.get_local_ip()
            
            self.service_info = ServiceInfo(
                self.service_type,
                f"{self.service_name}.{self.service_type}",
                addresses=[socket.inet_aton(local_ip)],
                port=self.port,
                properties={'path': '/'},
                server=f"{self.service_name}.local.",
            )
            
            self.zeroconf = Zeroconf()
            self.zeroconf.register_service(self.service_info)
            print(f"✅ mDNS服务已启动: http://{self.service_name}.local:{self.port}")
            print(f"   本地IP: {local_ip}:{self.port}")
            return True
            
        except Exception as e:
            print(f"❌ mDNS服务启动失败: {e}")
            print("⚠️  请安装zeroconf库: pip install zeroconf")
            return False
    
    def stop(self):
        """停止mDNS服务"""
        if self.zeroconf and self.service_info:
            self.zeroconf.unregister_service(self.service_info)
            self.zeroconf.close()
            print("✅ mDNS服务已停止")

if __name__ == "__main__":
    # 测试mDNS服务
    mdns = MDNSService()
    mdns.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mdns.stop()