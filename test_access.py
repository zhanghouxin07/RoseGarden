#!/usr/bin/env python3
"""
网络访问测试工具
诊断和解决局域网访问问题
"""
import socket
import subprocess
import platform
import requests
import threading
import time

class NetworkTester:
    def __init__(self, port=5000):
        self.port = port
        self.local_ip = self.get_local_ip()
    
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
    
    def check_port_listening(self):
        """检查端口是否在监听"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(("127.0.0.1", self.port))
            sock.close()
            return result == 0
        except:
            return False
    
    def check_firewall(self):
        """检查防火墙设置"""
        if platform.system() == "Windows":
            try:
                # 检查Windows防火墙规则
                cmd = f"netsh advfirewall firewall show rule name=RoseGarden"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return "RoseGarden" in result.stdout
            except:
                return False
        return True
    
    def test_local_access(self):
        """测试本地访问"""
        try:
            response = requests.get(f"http://localhost:{self.port}", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_ip_access(self):
        """测试IP访问"""
        try:
            response = requests.get(f"http://{self.local_ip}:{self.port}", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_mdns_support(self):
        """测试mDNS支持"""
        if platform.system() == "Windows":
            # 检查是否安装了Bonjour
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Apple Inc.")
                winreg.CloseKey(key)
                return True
            except:
                return False
        else:
            # Linux/macOS通常支持mDNS
            return True
    
    def run_comprehensive_test(self):
        """运行全面测试"""
        print("=" * 60)
        print("🌐 RoseGarden 网络访问诊断工具")
        print("=" * 60)
        
        print(f"\n📊 系统信息:")
        print(f"   操作系统: {platform.system()} {platform.release()}")
        print(f"   本地IP: {self.local_ip}")
        print(f"   服务端口: {self.port}")
        
        print(f"\n🔍 诊断结果:")
        
        # 测试1: 端口监听
        port_ok = self.check_port_listening()
        print(f"   1. 端口监听: {'✅ 正常' if port_ok else '❌ 失败'}")
        
        # 测试2: 本地访问
        local_ok = self.test_local_access()
        print(f"   2. 本地访问: {'✅ 正常' if local_ok else '❌ 失败'}")
        
        # 测试3: IP访问
        ip_ok = self.test_ip_access()
        print(f"   3. IP访问: {'✅ 正常' if ip_ok else '❌ 失败'}")
        
        # 测试4: mDNS支持
        mdns_ok = self.test_mdns_support()
        print(f"   4. mDNS支持: {'✅ 已安装' if mdns_ok else '❌ 未安装'}")
        
        # 测试5: 防火墙
        firewall_ok = self.check_firewall()
        print(f"   5. 防火墙: {'✅ 已配置' if firewall_ok else '⚠️  需要配置'}")
        
        print(f"\n💡 解决方案:")
        
        if not port_ok:
            print("   • 确保RoseGarden服务正在运行")
            print("   • 检查端口5000是否被其他程序占用")
        
        if not local_ok:
            print("   • 重启RoseGarden服务")
            print("   • 检查服务日志是否有错误")
        
        if not ip_ok:
            print("   • 检查防火墙设置")
            print("   • 确保网络连接正常")
        
        if not mdns_ok and platform.system() == "Windows":
            print("   • 安装Bonjour服务: https://support.apple.com/kb/DL999")
            print("   • 或使用hosts文件方法")
        
        if not firewall_ok:
            print("   • 添加防火墙规则允许端口5000")
        
        print(f"\n🚀 推荐访问方式:")
        
        if ip_ok:
            print(f"   • http://{self.local_ip}:{self.port} (最可靠)")
        
        if local_ok:
            print(f"   • http://localhost:{self.port} (本机访问)")
        
        if mdns_ok:
            print(f"   • http://rosegarden.local:{self.port} (mDNS)")
        else:
            print(f"   • 使用hosts文件: http://rosegarden.local:{self.port}")
        
        print(f"\n🔧 快速修复:")
        print(f"   1. 运行: py setup_hosts.py (配置hosts文件)")
        print(f"   2. 以管理员身份运行防火墙配置")
        print(f"   3. 重启RoseGarden服务")
        
        print("\n" + "=" * 60)

def setup_firewall_rule():
    """设置防火墙规则（需要管理员权限）"""
    if platform.system() == "Windows":
        print("\n🛡️  配置Windows防火墙...")
        
        commands = [
            f'netsh advfirewall firewall add rule name="RoseGarden" dir=in action=allow protocol=TCP localport=5000',
            f'netsh advfirewall firewall add rule name="RoseGarden" dir=out action=allow protocol=TCP localport=5000'
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True, check=True)
                print(f"✅ {cmd}")
            except subprocess.CalledProcessError:
                print(f"❌ 需要管理员权限: {cmd}")
    else:
        print("⚠️  防火墙配置仅支持Windows系统")

if __name__ == "__main__":
    tester = NetworkTester()
    tester.run_comprehensive_test()
    
    # 询问是否配置防火墙
    choice = input("\n是否配置防火墙规则? (y/N): ").lower()
    if choice == 'y':
        setup_firewall_rule()
    
    # 询问是否配置hosts文件
    choice = input("\n是否运行hosts配置工具? (Y/n): ").lower()
    if choice != 'n':
        subprocess.run(["py", "setup_hosts.py"])