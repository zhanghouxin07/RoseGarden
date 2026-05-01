#!/usr/bin/env python3
import socket
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

class DNSRedirectHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        client_ip = self.client_address[0]
        redirect_url = f"http://{client_ip}:5000{self.path}"
        self.send_response(302)
        self.send_header('Location', redirect_url)
        self.end_headers()
        print(f"🔀 重定向 {self.headers.get('Host', 'unknown')} -> {redirect_url}")
    
    def log_message(self, format, *args):
        print(f"🌐 HTTP访问: {format % args}")

class DNSRedirectService:
    
    def __init__(self, redirect_port=80, web_port=5000):
        self.redirect_port = redirect_port
        self.web_port = web_port
        self.http_server = None
        self.running = False
    
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def start(self):
        try:
            local_ip = self.get_local_ip()
            server_address = ('', self.redirect_port)
            self.http_server = HTTPServer(server_address, DNSRedirectHandler)
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
        try:
            self.http_server.serve_forever()
        except Exception as e:
            print(f"❌ HTTP服务器错误: {e}")
        finally:
            self.running = False
    
    def stop(self):
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()
            print("✅ DNS重定向服务已停止")

def setup_hosts_entry(domain="rosegarden.local"):
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
    service = DNSRedirectService()
    
    print("=" * 50)
    print("DNS重定向服务测试")
    print("=" * 50)
    
    setup_hosts_entry()
    print()
    
    if service.start():
        try:
            while service.running:
                time.sleep(1)
        except KeyboardInterrupt:
            service.stop()
    else:
        print("服务启动失败")
