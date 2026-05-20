import sys
import json
import os
from PyQt5.QtCore import QObject, pyqtSignal
from utils.paths import resource_path


class ConfigManager(QObject):
    config_changed = pyqtSignal()
    _instance = None

    # 硬编码底层配置
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
        
        # 锁死文件的外置路径
        self.CONFIG_FILE = resource_path("config", "config.json")
        self.CONFIG_BAK = resource_path("config", "config.bak")
        self.DEFAULT_FILE = resource_path("config", "default_config.json")
        self.DEFAULT_BAK = resource_path("config", "default_config.bak")
        
        # 自动建config 文件夹
        os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
        
        self._config = {}           # 运行时内存字典
        self.DEFAULT_CONFIG = {}    # 默认配置内存字典
        
        self._bootstrap_system()
        self._initialized = True

    def _align_with_default(self, target_dict, base_dict):
        """结构对齐：确保 target_dict 包含了 base_dict 里的所有键"""
        result = base_dict.copy()
        if isinstance(target_dict, dict):
            result.update(target_dict)
        return result

    def _bootstrap_system(self):
        """自愈启动：文件异常读取备份"""
        need_repair = False  # 状态锁：只有触发了修复，最后才写盘同步

        # 加载默认配置轨道 (DEFAULT_CONFIG)
        default_loaded = False
        if os.path.exists(self.DEFAULT_FILE):
            try:
                with open(self.DEFAULT_FILE, "r", encoding="utf-8") as f:
                    self.DEFAULT_CONFIG = self._align_with_default(json.load(f), self.HARD_DEFAULT)
                    default_loaded = True
            except Exception as e:
                print(f"[提示] 默认配置文件损坏，尝试读取备份: {e}")

        if not default_loaded and os.path.exists(self.DEFAULT_BAK):
            try:
                with open(self.DEFAULT_BAK, "r", encoding="utf-8") as f:
                    self.DEFAULT_CONFIG = self._align_with_default(json.load(f), self.HARD_DEFAULT)
                    default_loaded = True
                    need_repair = True
                    print("[恢复] 成功从备份还原 default_config")
            except Exception as e:
                print(f"[警告] 默认配置备份已失效: {e}")

        if not default_loaded:
            self.DEFAULT_CONFIG = self.HARD_DEFAULT.copy()
            need_repair = True
            print("[提示] 已初始化初始配置")

        # 加载运行配置轨道 (_config)
        config_loaded = False
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = self._align_with_default(json.load(f), self.DEFAULT_CONFIG)
                    config_loaded = True
            except Exception as e:
                print(f"[提示] 运行配置文件损坏，尝试读取备份: {e}")

        if not config_loaded and os.path.exists(self.CONFIG_BAK):
            try:
                with open(self.CONFIG_BAK, "r", encoding="utf-8") as f:
                    self._config = self._align_with_default(json.load(f), self.DEFAULT_CONFIG)
                    config_loaded = True
                    need_repair = True
                    print("[恢复] 成功从备份还原 config")
            except Exception as e:
                print(f"[警告] 运行配置备份已失效: {e}")

        if not config_loaded:
            self._config = self.DEFAULT_CONFIG.copy()
            need_repair = True
            print("[提示] 自动应用当前默认配置代入运行")

        # 闭环同步：只有真正发生过修复，才重新固化本地文件
        if need_repair:
            self._save_file_atomic(self.CONFIG_FILE, self.CONFIG_BAK, self._config)
            self._save_file_atomic(self.DEFAULT_FILE, self.DEFAULT_BAK, self.DEFAULT_CONFIG)

    def _save_file_atomic(self, main_path, bak_path, data_dict):
        """使用 os.replace 替换，避免 Windows 下的删除空窗期"""
        tmp_file = main_path + ".tmp"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data_dict, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_file, main_path)  # 底层瞬间覆盖替换

            # 同步刷新备份
            tmp_bak = bak_path + ".tmp"
            with open(tmp_bak, "w", encoding="utf-8") as f:
                json.dump(data_dict, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_bak, bak_path)
        except Exception as e:
            print(f"[错误] 磁盘原子写入失败: {e}")
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

    def get(self, key, default=None):
        return self._config.get(key, default)

    def get_all(self):
        return self._config.copy()

    def set(self, key, value):
        # 防重入检查
        if key in self._config and self._config[key] == value:
            return
        self._config[key] = value
        # 仅刷新运行配置轨道
        self._save_file_atomic(self.CONFIG_FILE, self.CONFIG_BAK, self._config)
        self.config_changed.emit()

    def reset_to_default(self):
        """恢复默认"""
        self._config = self.DEFAULT_CONFIG.copy()
        self._save_file_atomic(self.CONFIG_FILE, self.CONFIG_BAK, self._config)
        self.config_changed.emit()

    def save_current_as_default(self):
        """保存当前为默认"""
        self.DEFAULT_CONFIG = self._config.copy()
        self._save_file_atomic(self.DEFAULT_FILE, self.DEFAULT_BAK, self.DEFAULT_CONFIG)