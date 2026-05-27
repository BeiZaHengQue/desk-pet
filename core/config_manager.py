import os
import json
import logging
from PyQt5.QtCore import QObject, pyqtSignal
from utils.paths import resource_path

logger = logging.getLogger(__name__)

class ConfigManager(QObject):
    config_changed = pyqtSignal()
    _instance = None

    HARD_DEFAULT = {
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
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        
        self.CONFIG_FILE = resource_path("config", "config.json")
        self.CONFIG_BAK = resource_path("config", "config.bak")
        self.DEFAULT_FILE = resource_path("config", "default_config.json")
        self.DEFAULT_BAK = resource_path("config", "default_config.bak")
        
        os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
        self._config = {}           
        self.DEFAULT_CONFIG = {}    
        self._bootstrap_system()
        self._initialized = True

    def _align_with_default(self, target_dict, base_dict):
        result = base_dict.copy()
        if isinstance(target_dict, dict):
            result.update(target_dict)
        return result

    def _bootstrap_system(self):
        """自愈启动链路"""
        need_repair = False  

        # 加载默认配置轨道
        default_loaded = False
        if os.path.exists(self.DEFAULT_FILE):
            try:
                with open(self.DEFAULT_FILE, "r", encoding="utf-8") as f:
                    self.DEFAULT_CONFIG = self._align_with_default(json.load(f), self.HARD_DEFAULT)
                    default_loaded = True
                    logger.info("配置加载 | 成功解析默认配置主文件 | 路径: %s", self.DEFAULT_FILE)
            except Exception as e:
                logger.warning("配置异常 | 默认配置主文件损坏，尝试切入备份轨道 | 异常: %s", e)

        if not default_loaded and os.path.exists(self.DEFAULT_BAK):
            try:
                with open(self.DEFAULT_BAK, "r", encoding="utf-8") as f:
                    self.DEFAULT_CONFIG = self._align_with_default(json.load(f), self.HARD_DEFAULT)
                    default_loaded = True
                    need_repair = True
                    logger.info("配置自愈 | 成功从备份轨道 (.bak) 恢复默认配置")
            except Exception as e:
                logger.error("配置瘫痪 | 默认配置备份轨道亦失效 | 异常: %s", e)

        if not default_loaded:
            self.DEFAULT_CONFIG = self.HARD_DEFAULT.copy()
            need_repair = True
            logger.warning("配置绝境 | 未检测到任何有效默认配置文件，被迫应用硬编码配置")

        # 加载运行配置轨道
        config_loaded = False
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = self._align_with_default(json.load(f), self.DEFAULT_CONFIG)
                    config_loaded = True
            except Exception as e:
                logger.warning("配置异常 | 运行配置文件损坏，尝试切入备份轨道 | 异常: %s", e)

        if not config_loaded and os.path.exists(self.CONFIG_BAK):
            try:
                with open(self.CONFIG_BAK, "r", encoding="utf-8") as f:
                    self._config = self._align_with_default(json.load(f), self.DEFAULT_CONFIG)
                    config_loaded = True
                    need_repair = True
                    logger.info("配置自愈 | 成功从备份轨道 (.bak) 恢复当前运行配置")
            except Exception as e:
                logger.error("配置瘫痪 | 运行配置备份轨道亦失效 | 异常: %s", e)

        if not config_loaded:
            self._config = self.DEFAULT_CONFIG.copy()
            need_repair = True
            logger.info("配置克隆 | 运行配置缺失，克隆当前默认配置轨道")

        if need_repair:
            logger.info("配置保存 | 检测到配置触发过自愈/初始化行为，执行写盘固化")
            self._save_file_atomic(self.CONFIG_FILE, self.CONFIG_BAK, self._config)
            self._save_file_atomic(self.DEFAULT_FILE, self.DEFAULT_BAK, self.DEFAULT_CONFIG)

    def _save_file_atomic(self, main_path, bak_path, data_dict):
        tmp_file = main_path + ".tmp"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data_dict, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_file, main_path)  

            tmp_bak = bak_path + ".tmp"
            with open(tmp_bak, "w", encoding="utf-8") as f:
                json.dump(data_dict, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_bak, bak_path)
            logger.debug("配置写盘 | 同步写入成功 | 路径: %s", main_path)
        except Exception as e:
            logger.error("配置异常 | 磁盘写入遭遇阻碍 | 路径: %s | 异常: %s", main_path, e, exc_info=True)
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

    def get(self, key, default=None):
        return self._config.get(key, default)

    def get_all(self):
        return self._config.copy()

    def set(self, key, value, source="unknown"):
        """动态修改配置项"""
        if key in self._config and self._config[key] == value:
            return
        old_val = self._config.get(key)
        self._config[key] = value
        
        logger.info("配置变更 | key=[%s] | 旧值=[%s] -> 新值=[%s] | 来源=[%s]", key, old_val, value, source)
        self._save_file_atomic(self.CONFIG_FILE, self.CONFIG_BAK, self._config)
        self.config_changed.emit()

    def reset_to_default(self, source="unknown"):
        logger.warning("配置警告 | 接收到重置默认指令 | 来源=[%s]", source)
        self._config = self.DEFAULT_CONFIG.copy()
        self._save_file_atomic(self.CONFIG_FILE, self.CONFIG_BAK, self._config)
        self.config_changed.emit()

    def save_current_as_default(self, source="unknown"):
        logger.info("配置留痕 | 固化当前运行配置为默认配置 | 来源=[%s]", source)
        self.DEFAULT_CONFIG = self._config.copy()
        self._save_file_atomic(self.DEFAULT_FILE, self.DEFAULT_BAK, self.DEFAULT_CONFIG)