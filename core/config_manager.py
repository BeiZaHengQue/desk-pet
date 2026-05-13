import sys
import json
import os
from PyQt5.QtCore import QObject, pyqtSignal


class ConfigManager(QObject):
    config_changed = pyqtSignal()
    _instance = None

    CONFIG_FILE = "config.json"

    DEFAULT_CONFIG = {
        "always_on_top": True,
        "random_move": True,
        "opacity": 1.0,
        "scale": 0.8,
        "move_idle_sec": 60,
        "move_speed": 5,
        "idle_text": True,
        "bubble_idle_sec": 60,
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
        # 获取程序运行的根目录
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.CONFIG_FILE = os.path.join(base_dir, "config.json")
        if self.__initialized:
            return
        super().__init__()
        self._config = {}
        # 初始化顺序：先尝试从本地加载，失败则使用默认并保存
        self._load_from_json()
        self.__initialized = True

    def _load_from_json(self):
        """检测并读取 JSON 文件"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # 使用默认配置做兜底，防止 JSON 缺少某些新增加的键
                    self._config = self.DEFAULT_CONFIG.copy()
                    self._config.update(loaded_data)
            except Exception as e:
                print(f"配置文件读取失败，将重置为默认: {e}")
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