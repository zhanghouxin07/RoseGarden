# RoseGarden - 路由器监测工具

RoseGarden 是一个用于监测路由器连接设备网速和活动情况的工具，支持将数据上报到华为云AOM进行可视化监控。

## 功能特性

- 自动登录路由器管理界面（支持中国电信智能网关）
- 检测并列出所有连接的设备
- 实时监测每个设备的上传/下载速度
- 保存监测数据到 JSON 文件
- 生成带宽使用报告图表
- 支持上报指标到华为云AOM

## 安装依赖

```bash
py -m pip install requests pandas matplotlib psutil
```

## 配置

### 基础配置

修改 `config.json` 文件：

```json
{
    "router": {
        "ip": "192.168.1.1",
        "username": "useradmin",
        "password": "your_password",
        "login_url": "/cgi-bin/luci",
        "devices_url": "/cgi-bin/luci/admin/device/devInfo?type=0"
    },
    "monitor": {
        "duration": 60,
        "interval": 5
    }
}
```

### 华为云AOM配置

1. 登录华为云控制台，进入 **应用运维管理 AOM**
2. 在左侧菜单选择 **接入管理**
3. 创建接入配置，获取以下信息：
   - `project_id` - 项目ID
   - `prometheus_id` - Prometheus实例ID
   - `access_code` - 认证凭据

4. 修改 `config.json` 中的 `huaweicloud_aom` 配置：

```json
{
    "huaweicloud_aom": {
        "enabled": true,
        "region": "cn-north-4",
        "project_id": "your_project_id",
        "prometheus_id": "your_prometheus_id",
        "access_code": "your_access_code"
    }
}
```

#### 支持的区域

| 区域 | region 值 |
|------|-----------|
| 华北-北京一 | cn-north-1 |
| 华北-北京四 | cn-north-4 |
| 华东-上海一 | cn-east-3 |
| 华东-上海二 | cn-east-2 |
| 华南-广州 | cn-south-1 |
| 中国-香港 | ap-southeast-1 |
| 亚太-新加坡 | ap-southeast-3 |

## 运行

```bash
py router_monitor.py
```

## 上报的指标

当启用AOM上报后，以下指标会被推送到华为云：

| 指标名称 | 说明 | 标签 |
|----------|------|------|
| `router_device_up_speed_bytes` | 设备上传速度 (Bytes/s) | device_id, device_ip, device_mac, device_type, device_system |
| `router_device_down_speed_bytes` | 设备下载速度 (Bytes/s) | device_id, device_ip, device_mac, device_type, device_system |
| `router_total_up_speed_bytes` | 总上传速度 (Bytes/s) | - |
| `router_total_down_speed_bytes` | 总下载速度 (Bytes/s) | - |
| `router_device_count` | 在线设备数量 | - |

## 在AOM中查看数据

1. 登录华为云AOM控制台
2. 选择 **指标浏览** 或 **仪表盘**
3. 使用PromQL查询，例如：
   ```promql
   # 查看所有设备的上传速度
   router_device_up_speed_bytes
   
   # 按设备类型聚合
   sum by (device_type) (router_device_up_speed_bytes)
   
   # 查看总带宽
   router_total_up_speed_bytes
   router_total_down_speed_bytes
   ```

## 配置告警

在AOM中可以配置告警规则：

1. 进入 **告警管理** > **告警规则**
2. 创建规则，例如：
   - 当 `router_device_count > 20` 时告警（设备过多）
   - 当 `router_total_down_speed_bytes > 104857600` 时告警（下载超过100MB/s）

## 输出文件

- **router_monitor_data.json** - 监测数据
- **bandwidth_report.png** - 带宽报告图表

## 注意事项

1. 华为云AOM接入管理需要在支持的区域开通
2. `access_code` 是敏感信息，请妥善保管
3. 建议将监测间隔设置为30秒以上，避免上报过于频繁
