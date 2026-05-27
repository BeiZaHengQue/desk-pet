import logging
from modules.idle_bubble import IdleBubbleModule
from modules.time_notify import TimeNotifyModule

logger = logging.getLogger(__name__)

class ModuleManager:
    def __init__(self, api, config):
        self.api = api
        self.config = config
        self.modules = []
        self._register_modules()

    def _register_modules(self):
        logger.info("插件管束 | 开始注册服务挂载点...")
        
        idle_mod = IdleBubbleModule(self.api, self.config)
        self.modules.append(idle_mod)
        logger.info("插件管束 | 模块注册成功: 名字=[%s]", idle_mod.__class__.__name__)

        time_mod = TimeNotifyModule(self.api, self.config)
        self.modules.append(time_mod)
        logger.info("插件管束 | 模块注册成功: 名字=[%s]", time_mod.__class__.__name__)
        
        logger.info("插件管束 | 基础架构注册完毕。当前共托管插件数: %d", len(self.modules))

    def start_all(self):
        logger.debug("插件管束 | 批量拉起托管插件集群")
        self.refresh_modules()

    def stop_all(self):
        for module in self.modules:
            name = module.__class__.__name__
            try:
                logger.debug("插件管束 | 强令模块停机 -> %s", name)
                module.stop()
            except Exception as e:
                logger.error("插件管束异常 | 模块 [%s] 释放资源遇到异常阻碍 | 异常: %s", name, e, exc_info=True)

    def refresh_modules(self):
        """记录具体的启停依据"""
        for module in self.modules:
            name = module.__class__.__name__
            try:
                # 获取该插件绑定的核心配置 key
                binding_keys = getattr(module, "keys", [])
                is_allowed = any(self.config.get(key) for key in binding_keys)
                
                if is_allowed:
                    logger.info("插件管束 | 状态变更: 激活 [%s] | 依据配置项=%s", name, binding_keys)
                    module.refresh() 
                    module.start()
                else:
                    logger.info("插件管束 | 状态变更: 挂起并静默 [%s] | 依据配置项=%s 状态均为关闭", name, binding_keys)
                    module.stop()
            except Exception as e:
                logger.error("插件管束异常 | 动态调整模块行为时遭遇逻辑崩溃 | 模块=%s | 异常=%s", 
                             name, e, exc_info=True)