#!/usr/bin/env python3
"""
简单的DNS重定向服务
将特定域名重定向到本地IP，方便局域网内访问
"""
import socket
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

class DNSRedirectHandler(BaseHTTPRequestHandler):
    """HTTP重定向处理器"""
    
    def do_GET(self):
        """处理GET请求，重定向到实际IP"""
        # 获取客户端IP
        client_ip = self.client_address[0]
        
        # 构建重定向URL
        redirect_url = f"http://{client_ip}:5000{self.path}"
        
        # 发送重定向响应
        self.send_response(302)
        self.send_header('Location', redirect_url)
        self.end_headers()
        
        # 记录访问日志
        print(f"🔀 重定向 {self.headers.get('Host', 'unknown')} -> {redirect_url}")
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"🌐 HTTP访问: {format % args}")

class DNSRedirectService:
    """DNS重定向服务"""
    
    def __init__(self, redirect_port=80, web_port=5000):
        self.redirect_port = redirect_port
        self.web_port = web_port
        self.http_server = None
        self.running = False
    
    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def start(self):
        """启动重定向服务"""
        try:
            local_ip = self.get_local_ip()
            
            # 启动HTTP重定向服务
            server_address = ('', self.redirect_port)
            self.http_server = HTTPServer(server_address, DNSRedirectHandler)
            
            # 启动服务线程
            self.running = True
            server_thread = threading.Thread(target=self._run_server)
            server_thread.daemon = True
            server_thread.start()
            
            print(f"✅ DNS重定向服务已启动")
            print(f"   访问地址: http://{local_ip} (自动重定向到端口5000)")
            print(f"   或直接访问: http://{local_ip}:5000")
            return True
            
        except Exception as e:
            print(f"❌ DNS重定向服务启动失败: {e}")
            return False
    
    def _run_server(self):
        """运行HTTP服务器"""
        try:
            self.http_server.serve_forever()
        except Exception as e:
            print(f"❌ HTTP服务器错误: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """停止服务"""
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()
            print("✅ DNS重定向服务已停止")

# 简单的hosts文件修改工具
def setup_hosts_entry(domain="rosegarden.local"):
    """设置hosts文件条目（需要管理员权限）"""
    import platform
    
    local_ip = DNSRedirectService().get_local_ip()
    hosts_entry = f"{local_ip}\t{domain}\n"
    
    if platform.system() == "Windows":
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    else:
        hosts_path = "/etc/hosts"
    
    print(f"📝 手动设置hosts文件:")
    print(f"   文件路径: {hosts_path}")
    print(f"   添加内容: {hosts_entry.strip()}")
    print(f"   设置后可通过 http://{domain}:5000 访问")

if __name__ == "__main__":
    # 测试DNS重定向服务
    service = DNSRedirectService()
    
    print("=" * 50)
    print("DNS重定向服务测试")
    print("=" * 50)
    
    # 显示hosts设置信息
    setup_hosts_entry()
    print()
    
    # 启动服务
    if service.start():
        try:
            while service.running:
                time.sleep(1)
        except KeyboardInterrupt:
            service.stop()
    else:
        print("服务启动失败")