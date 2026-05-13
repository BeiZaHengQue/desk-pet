from modules.idle_bubble import IdleBubbleModule
from modules.time_notify import TimeNotifyModule


class ModuleManager:
    def __init__(self, api, config):
        self.api = api
        self.config = config
        self.modules = []
        self._register_modules()

    def _register_modules(self):
        # 显式把模块加进列表
        self.modules.append(IdleBubbleModule(self.api, self.config))
        self.modules.append(TimeNotifyModule(self.api, self.config))

    def start_all(self):
        self.refresh_modules()

    def stop_all(self):
        for module in self.modules:
            try:
                module.stop()
            except Exception as e:
                print(f"Error stopping module {module}: {e}")

    def refresh_modules(self):
        for module in self.modules:
            try:
                # 不允许模块自己决定启停，只由管理器决定
                if any(self.config.get(key) for key in getattr(module, "keys", [])):
                    module.refresh() # 刷新可能需要的配置
                    module.start()
                else:
                    module.stop()
            except Exception as e:
                print(f"Error refreshing module {module}: {e}")