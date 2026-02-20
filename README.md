# RoseGarden - 天翼网关设备监控系统

一个用于监控中国电信智能网关（天翼网关）连接设备的实时监控系统，支持 Web 可视化界面和华为云 AOM 指标上报。

## 功能特性

### 核心功能
- 自动登录路由器管理界面
- 实时检测所有连接设备
- 监测每个设备的上传/下载速度
- 记录设备在线时长、IP、MAC、品牌型号等信息
- 支持设备类型自动识别（手机/电脑/平板/路由器/电视/智能设备）

### Web 可视化
- 响应式设计，支持手机/平板/电脑访问
- 实时显示 WAN 连接状态和在线时长
- 设备筛选（按类型）和排序（按名称/在线时间/网速）
- 显示完整设备信息：名称、IP、MAC、品牌、型号、操作系统、IPv6
- 设备状态标签（黑名单/受限）

### 云端监控
- 支持上报指标到华为云 AOM
- 可配置采集间隔和上报间隔
- 支持多区域部署

## 项目结构

```
RoseGarden/
├── config/
│   └── config.json          # 配置文件
├── data/
│   └── router_monitor_data.json  # 监测数据存储
├── output/
│   └── bandwidth_report.png # 带宽报告图表
├── src/
│   ├── router_monitor.py    # 核心监控类
│   ├── background_monitor.py # 后台监控线程
│   ├── web_app.py           # Flask Web 应用
│   ├── aom_reporter.py      # 华为云 AOM 上报
│   └── logger.py            # 日志配置
├── templates/
│   └── index.html           # Web 界面模板
├── debug/                   # 调试脚本
├── run_web.py               # Web 服务启动入口
├── mdns_service.py          # mDNS 服务
├── dns_redirect.py          # DNS 重定向服务
└── requirements.txt         # Python 依赖
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- Flask - Web 框架
- requests - HTTP 请求
- pandas - 数据处理
- matplotlib - 图表生成
- huaweicloudsdkcore/huaweicloudsdkaom - 华为云 SDK

### 配置

编辑 `config/config.json`：

```json
{
    "router": {
        "ip": "192.168.1.1",
        "username": "useradmin",
        "password": "your_password",
        "login_url": "/cgi-bin/luci",
        "allinfo_url": "/cgi-bin/luci/admin/allInfo"
    },
    "monitor": {
        "duration": 86400,
        "collect_interval": 10,
        "aom_interval": 60,
        "data_file": "router_monitor_data.json",
        "report_file": "bandwidth_report.png"
    },
    "huaweicloud_aom": {
        "enabled": false,
        "region": "cn-north-4",
        "project_id": "",
        "ak": "",
        "sk": ""
    }
}
```

### 启动服务

```bash
python run_web.py
```

启动后访问：
- 本地：http://localhost:5000
- 局域网：http://<您的IP地址>:5000
- mDNS（需安装 zeroconf）：http://rosegarden.local:5000

## Web 界面功能

### 状态栏
- WAN 连接状态
- 路由器在线时长
- 在线设备数量
- 总上传/下载速度

### 监控状态
- 后台监控运行状态
- AOM 上报状态
- 上报次数统计
- 采集间隔配置

### 设备列表
- 设备筛选：全部/手机/电脑/平板/路由器/电视/智能设备
- 排序方式：名称/在线时间/上传速度/下载速度/设备类型
- 显示信息：
  - 设备名称、品牌、型号
  - IP 地址、MAC 地址
  - 在线时长、操作系统
  - IPv6 地址（如有）
  - 实时上传/下载速度
  - 状态标签（黑名单/受限）

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/devices` | GET | 获取设备列表 |
| `/api/network-status` | GET | 获取网络状态 |
| `/api/monitor-status` | GET | 获取监控状态 |

### 示例响应

**设备列表** `/api/devices`
```json
{
    "devices": [
        {
            "id": "1",
            "ip": "192.168.1.100",
            "mac": "AA:BB:CC:DD:EE:FF",
            "name": "iPhone",
            "brand": "Apple",
            "model": "iPhone 15",
            "type": "phone",
            "system": "iOS 17.0",
            "online_time": 3600,
            "up_speed": 1024,
            "down_speed": 51200,
            "ipv6": "fe80::..."
        }
    ],
    "total": 1,
    "timestamp": "2024-01-01 12:00:00"
}
```

**网络状态** `/api/network-status`
```json
{
    "wan_connect": "CONNECTED",
    "wan_up_time": "5天12时30分",
    "wired_count": 3,
    "wireless_count": 8,
    "total_up_speed": "125.5 KB/s",
    "total_down_speed": "2.5 MB/s"
}
```

## 华为云 AOM 集成

### 配置步骤

1. 登录华为云控制台，进入 **应用运维管理 AOM**
2. 获取访问密钥（AK/SK）和项目ID
3. 修改 `config.json` 中的 `huaweicloud_aom` 配置

### 支持区域

| 区域 | region 值 |
|------|-----------|
| 华北-北京一 | cn-north-1 |
| 华北-北京四 | cn-north-4 |
| 华东-上海一 | cn-east-3 |
| 华东-上海二 | cn-east-2 |
| 华南-广州 | cn-south-1 |
| 中国-香港 | ap-southeast-1 |
| 亚太-新加坡 | ap-southeast-3 |

### 上报指标

| 指标名称 | 说明 | 标签 |
|----------|------|------|
| `device_up_speed` | 设备上传速度 | device_id, device_ip, device_name, device_type |
| `device_down_speed` | 设备下载速度 | device_id, device_ip, device_name, device_type |
| `device_online_time` | 设备在线时间 | device_id, device_ip, device_name, device_type |
| `total_up_speed` | 总上传速度 | - |
| `total_down_speed` | 总下载速度 | - |
| `device_count` | 在线设备数量 | - |

### PromQL 查询示例

```promql
device_up_speed
sum by (device_type) (device_down_speed)
total_up_speed
total_down_speed
device_count
```

## 局域网访问

### 方式一：mDNS（推荐）

安装依赖：
```bash
pip install zeroconf
```

启动后可通过 `http://rosegarden.local:5000` 访问。

支持设备：
- macOS - 原生支持
- Windows 10/11 - 需安装 Bonjour
- Linux - 需安装 avahi-daemon
- iOS/Android - 大部分支持

### 方式二：DNS 重定向

```bash
python dns_redirect.py
```

使用标准 80 端口，无需记忆端口号。

### 方式三：hosts 文件

Windows: `C:\Windows\System32\drivers\etc\hosts`
```
192.168.1.100    rosegarden.local
```

macOS/Linux: `/etc/hosts`
```
192.168.1.100    rosegarden.local
```

## 开发说明

### 目录说明

- `src/` - 核心源代码
- `config/` - 配置文件
- `data/` - 数据存储
- `output/` - 输出文件
- `templates/` - HTML 模板
- `debug/` - 调试脚本

### 日志级别

```python
from src.logger import setup_logger
setup_logger(level=logging.DEBUG)
```

### 自定义监控

```python
from src.router_monitor import RouterMonitor

monitor = RouterMonitor('config/config.json')
monitor.login()
devices = monitor.get_connected_devices()
monitor.push_to_aom(devices)
```

## 注意事项

1. 路由器密码存储在配置文件中，请注意安全
2. 华为云 AK/SK 是敏感信息，请勿泄露
3. 建议采集间隔不低于 10 秒，避免频繁请求
4. AOM 上报间隔建议不低于 60 秒

## License

MIT License
