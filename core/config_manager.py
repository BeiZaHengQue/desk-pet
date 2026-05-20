import sys
import json
import os
from PyQt5.QtCore import QObject, pyqtSignal
from utils.paths import resource_path


class ConfigManager(QObject):
    config_changed = pyqtSignal()
    _instance = None

    CONFIG_FILE = "config.json"
    DEFAULT_CONFIG_FILE = "default_config.json"

    DEFAULT_CONFIG = {
        "always_on_top": True,
        "random_move": True,
        "opacity": 1.0,
        "scale": 0.8,
        "move_idle_sec": 60,
        "move_speed": 5,
        "idle_text": True,
        "bubble_duration_sec": 3,
        "hourly": False,
        "half_hourly": False
    }

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        if self.__initialized:
            return
        super().__init__()
        
        self.CONFIG_FILE = resource_path("config.json")
        self.DEFAULT_CONFIG_FILE = resource_path("default_config.json")
        self._load_default_config_from_json()
        
        self._config = {}
        # 初始化顺序：先尝试从本地加载，失败则使用默认并保存
        self._load_from_json()
        self.__initialized = True

    def _load_default_config_from_json(self):
        """从磁盘加载默认配置"""
        if os.path.exists(self.DEFAULT_CONFIG_FILE):
            try:
                with open(self.DEFAULT_CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded_default = json.load(f)
                    # 采用 copy + update 结构防止结构缺失
                    new_default = self.DEFAULT_CONFIG.copy()
                    new_default.update(loaded_default)
                    # 动态覆写类属性
                    ConfigManager.DEFAULT_CONFIG = new_default
            except Exception as e:
                print(f"读取默认配置: {e}")
    
    def _load_from_json(self):
        """检测并读取 JSON 文件"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # 使用默认配置兜底，防止 JSON 缺少某些新增加的键
                    self._config = self.DEFAULT_CONFIG.copy()
                    self._config.update(loaded_data)
            except Exception as e:
                print(f"无法读取配置文件，重置为默认: {e}")
                self._config = self.DEFAULT_CONFIG.copy()
                self._save_to_json()
        else:
            # 文件不存在，生成初始文件
            self._config = self.DEFAULT_CONFIG.copy()
            self._save_to_json()

    def _save_to_json(self):
        """将当前配置写入磁盘"""
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"写入配置失败: {e}")

    def get(self, key, default=None):
        return self._config.get(key, default)

    def get_all(self):
        return self._config.copy()

    def set(self, key, value):
        if key in self._config and self._config[key] == value:
            return
        self._config[key] = value
        # 每次设置后自动同步磁盘
        self._save_to_json()
        self.config_changed.emit()

    def reset_to_default(self):
        """恢复默认并保留"""
        self._config = self.DEFAULT_CONFIG.copy()
        self._save_to_json()
        self.config_changed.emit()

    def save_current_as_default(self):
        """将当前配置直接重写到 DEFAULT_CONFIG"""
        ConfigManager.DEFAULT_CONFIG = self._config.copy()
 
        try:
            with open(self.DEFAULT_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(ConfigManager.DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存默认配置失败: {e}")