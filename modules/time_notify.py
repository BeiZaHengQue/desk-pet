from PyQt5.QtCore import QTimer
from datetime import datetime
from . import BaseModule


class TimeNotifyModule(BaseModule):
    keys = ["hourly", "half_hourly"]

    def __init__(self, api, config):
        super().__init__(api, config)
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_time)
        # 记录上一次触发的完整特征：(小时, 分钟)
        self.last_trigger_id = (-1, -1)

    def start(self):
        if not self.timer.isActive():
            # 检查间隔
            self.timer.start(20000)

    def stop(self):
        self.timer.stop()
        self.last_trigger_id = (-1, -1)

    def refresh(self):
        # 参数修改时，重置触发状态，确保能立即响应新的时间点
        self.last_trigger_id = (-1, -1)

    def check_time(self):
        now = datetime.now()
        hour = now.hour
        minute = now.minute

        hourly_enabled = self.config.get("hourly")
        half_hourly_enabled = self.config.get("half_hourly")

        # 判定整点
        if minute == 0 and hourly_enabled:
            self.api.show_bubble(
                text=f"现在是 {hour} 点，注意哦!",
                source="time_notif",
                priority=3  # BubblePriority.SYSTEM
            )
            self.last_trigger_id = (hour, minute)

        # 判定半点
        elif minute == 30 and half_hourly_enabled:
            self.api.show_bubble(
                text=f"现在是 {hour} 点半，注意休息哦~",
                source="time_notif",
                priority=3  # BubblePriority.SYSTEM
            )
            self.last_trigger_id = (hour, minute)