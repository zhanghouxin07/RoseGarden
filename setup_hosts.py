#!/usr/bin/env python3
"""
自动配置hosts文件工具
为Windows系统提供可靠的域名访问方案
"""
import os
import platform
import shutil
import tempfile
import subprocess

class HostsConfigurator:
    def __init__(self, domain="rosegarden.local"):
        self.domain = domain
        self.hosts_path = self.get_hosts_path()
        
    def get_hosts_path(self):
        """获取hosts文件路径"""
        if platform.system() == "Windows":
            return r"C:\Windows\System32\drivers\etc\hosts"
        else:
            return "/etc/hosts"
    
    def get_local_ip(self):
        """获取本机IP地址"""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def check_admin_privileges(self):
        """检查是否具有管理员权限"""
        if platform.system() == "Windows":
            try:
                # 尝试在系统目录创建文件来检查权限
                temp_file = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'temp_test.txt')
                with open(temp_file, 'w') as f:
                    f.write('test')
                os.remove(temp_file)
                return True
            except:
                return False
        else:
            return os.geteuid() == 0
    
    def is_entry_exists(self):
        """检查hosts条目是否已存在"""
        if not os.path.exists(self.hosts_path):
            return False
            
        with open(self.hosts_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return self.domain in content
    
    def add_hosts_entry(self):
        """添加hosts条目"""
        local_ip = self.get_local_ip()
        entry = f"{local_ip}\t{self.domain}\n"
        
        print(f"📝 准备添加hosts条目:")
        print(f"   {entry.strip()}")
        
        if not self.check_admin_privileges():
            print("❌ 需要管理员权限才能修改hosts文件")
            print("💡 请以管理员身份运行此脚本")
            return False
        
        try:
            # 备份原文件
            backup_path = self.hosts_path + ".backup"
            if os.path.exists(self.hosts_path):
                shutil.copy2(self.hosts_path, backup_path)
                print(f"✅ 已备份hosts文件到: {backup_path}")
            
            # 读取现有内容
            if os.path.exists(self.hosts_path):
                with open(self.hosts_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = ""
            
            # 移除可能存在的旧条目
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if self.domain not in line:
                    new_lines.append(line)
            
            # 添加新条目
            new_lines.append(entry.strip())
            new_content = '\n'.join(new_lines) + '\n'
            
            # 写入新文件
            with open(self.hosts_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ hosts文件已更新")
            print(f"🌐 现在可以通过 http://{self.domain}:5000 访问")
            
            # 刷新DNS缓存
            self.flush_dns_cache()
            
            return True
            
        except Exception as e:
            print(f"❌ 修改hosts文件失败: {e}")
            return False
    
    def flush_dns_cache(self):
        """刷新DNS缓存"""
        try:
            if platform.system() == "Windows":
                subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
                print("✅ DNS缓存已刷新")
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], capture_output=True)
                print("✅ DNS缓存已刷新")
            else:  # Linux
                subprocess.run(["sudo", "systemctl", "restart", "systemd-resolved"], capture_output=True)
                print("✅ DNS缓存已刷新")
        except Exception as e:
            print(f"⚠️  刷新DNS缓存失败: {e}")
    
    def remove_hosts_entry(self):
        """移除hosts条目"""
        if not self.check_admin_privileges():
            print("❌ 需要管理员权限")
            return False
        
        try:
            if os.path.exists(self.hosts_path):
                with open(self.hosts_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    if self.domain not in line:
                        new_lines.append(line)
                
                with open(self.hosts_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                
                print("✅ hosts条目已移除")
                self.flush_dns_cache()
                return True
            
        except Exception as e:
            print(f"❌ 移除hosts条目失败: {e}")
            return False

def main():
    print("=" * 50)
    print("RoseGarden Hosts配置工具")
    print("=" * 50)
    
    configurator = HostsConfigurator()
    
    if configurator.is_entry_exists():
        print("✅ hosts条目已存在")
        print(f"🌐 可以通过 http://{configurator.domain}:5000 访问")
        
        choice = input("是否移除条目? (y/N): ").lower()
        if choice == 'y':
            configurator.remove_hosts_entry()
    else:
        print("❌ hosts条目不存在")
        print("💡 建议使用hosts文件方法，这是最可靠的解决方案")
        
        choice = input("是否添加hosts条目? (Y/n): ").lower()
        if choice != 'n':
            configurator.add_hosts_entry()
    
    print("\n" + "=" * 50)
    print("其他访问方式:")
    print(f"• 直接IP: http://{configurator.get_local_ip()}:5000")
    print(f"• 本地访问: http://localhost:5000")
    print("=" * 50)

if __name__ == "__main__":
    main()