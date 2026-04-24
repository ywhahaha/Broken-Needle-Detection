import yaml
from function.get_resource_path import get_path

class ConfigReader:
    """最简单的配置文件读取类"""
    
    def __init__(self, config_path='config.yaml'):
        self.config_path = get_path(config_path)
        self.data = self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"配置文件 {self.config_path} 不存在，使用默认配置")
            return {}
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.data.get(key, default)
    
    def __getattr__(self, name):
        """支持点号访问，如 config.half"""
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"配置项 '{name}' 不存在")

# # 使用示例
if __name__ == "__main__":
    from get_resource_path import get_path

    config = ConfigReader(get_path('default.yaml'))
    
    # 方式1：使用点号访问
    print(f"roi: {config.roi}")
    print(config.roi[0])
    print(config.roi[1])
    print(config.roi[2])
    print(config.roi[3])
