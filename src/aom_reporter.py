import time
import logging
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.http.http_config import HttpConfig
from huaweicloudsdkaom.v2.region.aom_region import AomRegion
from huaweicloudsdkaom.v2 import AomClient, AddMetricDataRequest, MetricDataItem, MetricItemInfo, Dimension2, ValueData

logger = logging.getLogger(__name__)


class AOMReporter:
    def __init__(self, config):
        self.enabled = config.get('enabled', False)
        self.region = config.get('region', 'ap-southeast-1')
        self.project_id = config.get('project_id', '')
        self.ak = config.get('ak', '')
        self.sk = config.get('sk', '')
        self.namespace = config.get('namespace', 'RoseGarden.Router')
        
        logger.debug(f"AOM Reporter 初始化: enabled={self.enabled}, region={self.region}, project_id={self.project_id}")
        
        if self.enabled:
            self._init_client()
    
    def _init_client(self):
        config = HttpConfig.get_default_config()
        config.ignore_ssl_verification = True
        
        credentials = BasicCredentials(self.ak, self.sk, self.project_id)
        
        region = AomRegion.value_of(self.region)
        
        logger.debug(f"AOM 客户端初始化: region={region}")
        
        self.client = AomClient.new_builder() \
            .with_http_config(config) \
            .with_credentials(credentials) \
            .with_region(region) \
            .build()
    
    def push_metrics(self, metrics):
        if not self.enabled:
            return False
        
        try:
            collect_time = int(time.time() * 1000)
            
            logger.debug(f"AOM上报时间戳: {collect_time}")
            logger.debug(f"AOM上报指标数量: {len(metrics)}")
            
            metric_data_items = []
            for metric in metrics:
                name = metric['name']
                value = metric['value']
                labels = metric.get('labels', {})
                
                dimensions = []
                for key, val in labels.items():
                    dim_name = str(key)[:32] if len(str(key)) > 32 else str(key)
                    dim_value = str(val)[:64] if len(str(val)) > 64 else str(val)
                    if dim_name and dim_value:
                        dimensions.append(Dimension2(
                            name=dim_name,
                            value=dim_value
                        ))
                
                if not dimensions:
                    dimensions = [Dimension2(name='default', value='router')]
                
                metric_value = int(value) if isinstance(value, int) else float(value) if isinstance(value, (int, float)) else 0
                
                metric_item = MetricDataItem(
                    collect_time=collect_time,
                    metric=MetricItemInfo(
                        namespace=self.namespace,
                        dimensions=dimensions
                    ),
                    values=[ValueData(
                        metric_name=name,
                        type='int',
                        unit='Bytes/s',
                        value=metric_value
                    )]
                )
                
                metric_data_items.append(metric_item)
                
                logger.debug(f"指标: {name}={value}, 维度: {labels}")
            
            request = AddMetricDataRequest(body=metric_data_items)
            
            logger.debug(f"发送AOM请求: namespace={self.namespace}, 指标数={len(metric_data_items)}")
            
            response = self.client.add_metric_data(request)
            
            logger.debug(f"AOM响应状态码: {response.status_code}")
            logger.debug(f"AOM响应体: {response}")
            
            if response.status_code in [200, 201, 202, 204]:
                logger.info(f"AOM上报成功: {len(metrics)} 个指标")
                return True
            else:
                logger.error(f"AOM上报失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"AOM上报异常: {e}")
            return False
