# RoseGarden - 路由器监测工具

RoseGarden 是一个用于监测路由器连接设备网速和活动情况的工具。它可以帮助你了解网络中各设备的带宽使用情况，及时发现网络异常。

## 功能特性

- 自动登录路由器管理界面
- 检测并列出所有连接的设备
- 实时监测带宽使用情况
- 保存监测数据到 JSON 文件
- 生成带宽使用报告图表

## 安装依赖

在运行脚本之前，需要安装以下依赖包：

```bash
pip install -r requirements.txt
```

## 配置路由器信息

在运行脚本之前，需要根据你的路由器型号修改 `config.json` 文件中的配置信息：

```json
{
    "router": {
        "ip": "192.168.1.1",  // 路由器 IP 地址
        "username": "admin",  // 路由器登录用户名
        "password": "admin",  // 路由器登录密码
        "login_url": "/login.cgi",  // 登录页面路径
        "devices_url": "/devices.cgi",  // 设备列表页面路径
        "bandwidth_url": "/bandwidth.cgi"  // 带宽监测页面路径
    },
    "monitor": {
        "duration": 60,  // 监测持续时间（秒）
        "interval": 5,  // 监测间隔（秒）
        "data_file": "router_monitor_data.json",  // 数据保存文件
        "report_file": "bandwidth_report.png"  // 报告图表文件
    },
    "parsers": {
        "devices": {
            "row_selector": "tr.device-row",  // 设备行选择器
            "ip_selector": "td.ip",  // IP 地址选择器
            "mac_selector": "td.mac",  // MAC 地址选择器
            "name_selector": "td.name",  // 设备名称选择器
            "status_selector": "td.status"  // 设备状态选择器
        }
    }
}
```

### 配置说明

- **router.ip**: 你的路由器网关地址，通常是 `192.168.1.1` 或 `192.168.0.1`
- **router.username** 和 **router.password**: 登录路由器管理界面的用户名和密码
- **router.login_url**, **router.devices_url**: 这些路径可能因路由器型号而异，需要根据实际情况修改
- **parsers.devices**: 这些选择器用于解析路由器页面上的设备信息，需要根据实际页面结构修改

## 运行脚本

在配置完成后，运行以下命令启动监测：

```bash
python router_monitor.py
```

## 查看结果

运行完成后，你将看到以下输出：

1. 登录状态
2. 连接设备列表
3. 实时带宽使用情况
4. 数据保存位置
5. 报告生成位置

同时，脚本会生成以下文件：

- **router_monitor_data.json**: 包含详细的带宽监测数据
- **bandwidth_report.png**: 带宽使用情况的图表报告

## 注意事项

1. 不同品牌和型号的路由器管理界面结构可能不同，需要根据实际情况修改配置文件中的路径和选择器
2. 部分路由器可能有防爬虫机制，可能会导致脚本运行失败
3. 脚本需要在能够访问路由器管理界面的网络环境中运行
4. 长时间运行脚本可能会对路由器性能造成影响

## 常见问题

### 登录失败

如果遇到登录失败的情况，请检查：

1. 路由器 IP 地址是否正确
2. 用户名和密码是否正确
3. 登录页面路径是否正确

### 无法获取设备列表

如果无法获取设备列表，请检查：

1. 设备列表页面路径是否正确
2. 页面解析选择器是否与实际页面结构匹配

### 带宽监测不准确

如果带宽监测数据不准确，请检查：

1. 监测间隔设置是否合理
2. 网络接口名称是否正确（脚本默认监测 Ethernet、Wi-Fi 和 Local Area Connection）

## 示例输出

```
登录成功!
发现 5 个连接设备
开始监测带宽使用情况，持续 60 秒，间隔 5 秒...
[2026-02-16 15:30:00] Wi-Fi: 发送 1234.56 KB, 接收 7890.12 KB
[2026-02-16 15:30:05] Wi-Fi: 发送 1345.67 KB, 接收 8901.23 KB
...
数据已保存到 router_monitor_data.json
带宽报告已生成: bandwidth_report.png

连接的设备:
Device1 - 192.168.1.2 - AA:BB:CC:DD:EE:FF - 在线
Device2 - 192.168.1.3 - GG:HH:II:JJ:KK:LL - 在线
...
```

## 许可证

本项目采用 MIT 许可证。
