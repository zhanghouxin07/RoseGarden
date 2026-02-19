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
            
            # 检查是否是本地回环地址
            if local_ip == "127.0.0.1":
                print("⚠️  无法获取有效本地IP，使用回环地址")
                print("   请检查网络连接或手动设置IP")
            
            self.service_info = ServiceInfo(
                self.service_type,
                f"{self.service_name}.{self.service_type}",
                addresses=[socket.inet_aton(local_ip)],
                port=self.port,
                properties={'path': '/', 'name': 'RoseGarden Monitor'},
                server=f"{self.service_name}.local.",
            )
            
            self.zeroconf = Zeroconf()
            self.zeroconf.register_service(self.service_info)
            
            print(f"✅ mDNS服务已启动")
            print(f"   域名: http://{self.service_name}.local:{self.port}")
            print(f"   本地IP: http://{local_ip}:{self.port}")
            print(f"   服务类型: {self.service_type}")
            
            # 检查Windows mDNS支持
            import platform
            if platform.system() == "Windows":
                print("⚠️  Windows需要安装Bonjour服务才能支持mDNS")
                print("   下载: https://support.apple.com/kb/DL999")
                print("   或使用下面的替代方案")
            
            return True
            
        except Exception as e:
            print(f"❌ mDNS服务启动失败: {e}")
            print("💡 尝试以下解决方案:")
            print("   1. 安装Bonjour服务 (Windows)")
            print("   2. 使用hosts文件方法")
            print("   3. 使用DNS重定向服务")
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