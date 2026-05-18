import random
from PyQt5.QtCore import QTimer
from . import BaseModule


class IdleBubbleModule(BaseModule):
    keys = ["idle_text"]

    def __init__(self, api, config):
        super().__init__(api, config)
        self.cycle_timer = QTimer()
        self.cycle_timer.setSingleShot(True)
        self.cycle_timer.timeout.connect(self._trigger_speech)

    def _get_weighted_random_sec(self):
        """权重计算下一个随机触发时间点"""
        rand_percent = random.randint(1, 100)
        if rand_percent <= 29:
            return random.randint(0, 60)
        elif rand_percent <= 29 + 32:
            return random.randint(61, 120)
        else:
            return random.randint(121, 180)

    def start(self):
        """开了就立即重置旧计时，并重新摇号启动新计时"""
        self.cycle_timer.stop()
        if self.config.get("idle_text"):
            interval = self._get_weighted_random_sec() * 1000
            # 锁定保护 
            self.cycle_timer.start(max(3000, interval))

    def stop(self):
        """关了就立即停止计时，同时强行销毁无聊说话的气泡"""
        self.cycle_timer.stop()
        self.api.close_bubble_by_source("idle_speech")

    def refresh(self):
        """总控开关：根据布尔值决定开启或关闭释放"""
        if self.config.get("idle_text"):
            self.start()
        else:
            self.stop()

    def reset_timer_only(self):
        """当触发交互时，直接重置计时器"""
        self.start()

    def _trigger_speech(self):
        """时间到，执行说话逻辑，并自动滚入下一轮加权摇号"""
        quote = self.api.get_random_quote("idle") 
        duration = self.config.get("bubble_duration_sec", 3)

        self.api.show_bubble(
            text=quote,
            source="idle_speech",
            priority=1,  # BubblePriority.IDLE
            duration=duration
        )
        
        # 触发后重新启动下一轮随机摇号计时
        self.start()