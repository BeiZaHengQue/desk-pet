from PyQt5.QtCore import QTimer
from . import BaseModule


class IdleBubbleModule(BaseModule):
    keys = ["idle_text"]

    def __init__(self, api, config):
        super().__init__(api, config)
        self.cycle_timer = QTimer()
        self.cycle_timer.setSingleShot(True)
        self.cycle_timer.timeout.connect(self._trigger_speech)

    def start(self):
        """开始计时：从这一刻起，等待 idle_sec 后触发"""
        if not self.cycle_timer.isActive():
            interval = self.config.get("bubble_idle_sec", 10) * 1000
            self.cycle_timer.start(interval)

    def stop(self):
        self.cycle_timer.stop()

    def refresh(self):
        """修改气泡参数，打断并重新开始计时"""
        if self.cycle_timer.isActive():
            self.cycle_timer.stop()
            self.start()

    def _trigger_speech(self):
        """执行说话，并安排下一轮计时"""
        quote = self.api.get_random_quote("idle_quotes.txt")
        duration = self.config.get("bubble_duration_sec", 3)

        # 弹出待机气泡
        self.api.show_bubble(
            text=quote,
            source="idle_speech",
            priority=1,  # BubblePriority.IDLE
            duration=duration
        )


        # 气泡彻底消失才开始计时
        next_interval = (duration + self.config.get("bubble_idle_sec", 10)) * 1000
        self.cycle_timer.start(next_interval)

        # 修改 modules/idle_bubble.py 的最后一个方法：
        def reset_timer_only(self):
            """响应外部打断操作，重置倒计时"""
            try:
                self.cycle_timer.stop()
                interval = self.config.get("bubble_idle_sec", 10) * 1000
                # 预防空值或负数
                if interval <= 0:
                    interval = 1000
                self.cycle_timer.start(interval)
            except Exception:
                pass