from PyQt5.QtCore import QTimer
from datetime import datetime
from .import BaseModule


class TimeNotifyModule(BaseModule):
    keys = ["hourly", "half_hourly"]

    def __init__(self, api, config):
        super().__init__(api, config)
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_time)
        
        # 记录结构改变：[当前锁定的分钟, 这一分钟内已报时的次数]
        # 初始化为 [-1, 0] 防止干扰
        self.trigger_status = [-1, 0]

    def start(self):
        if not self.timer.isActive():
            # 每秒检测一次
            self.timer.start(1000)

    def stop(self):
        self.timer.stop()
        self.trigger_status = [-1, 0]

    def refresh(self):
        # 参数修改时重置状态
        self.trigger_status = [-1, 0]

    def check_time(self):
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        second = now.second

        hourly_enabled = self.config.get("hourly")
        half_hourly_enabled = self.config.get("half_hourly")

        # 判定当前分钟是否为目标分钟
        is_target_minute = False
        notify_text = ""

        if minute == 0 and hourly_enabled:
            is_target_minute = True
            notify_text = f"要注意哦，现在是 {hour} 点!"
        elif minute == 30 and half_hourly_enabled:
            is_target_minute = True
            notify_text = f"现在是 {hour} 点半，注意哦~"

        # 如果不是目标分钟，直接重置计数锁并退出
        if not is_target_minute:
            self.trigger_status = [-1, 0]
            return

        # 计数去重：控制在目标分钟内平均报时 3 次
        # 如果当前分钟与锁定的分钟不一致，说明是新跨入的一分钟，初始化计数
        if self.trigger_status[0] != minute:
            self.trigger_status = [minute, 0]

        # 报满 3 次不再报时
        if self.trigger_status[1] >= 3:
            return

        # 阶梯判定触发报时
        should_report = False
        current_count = self.trigger_status[1]

        if current_count == 0 and 0 <= second < 20:
            should_report = True
        elif current_count == 1 and 20 <= second < 40:
            should_report = True
        elif current_count == 2 and 40 <= second < 60:
            should_report = True
        
        # 如果在 59 秒开启，直接报时
        elif current_count < 3 and second >= 58:
            should_report = True

        if should_report:
            self.api.show_bubble(
                text=notify_text,
                source="time_notif",
                priority=3  # BubblePriority.SYSTEM
            )
            # 报时成功，计数器累加
            self.trigger_status[1] += 1