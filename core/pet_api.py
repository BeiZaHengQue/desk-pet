import os
from utils.paths import resource_path
import random
import ctypes
from core.types import BubblePriority, BubbleMsg


class PetAPI:
    def __init__(self, engine, config):
        self._engine = engine
        self._config = config

    def show_bubble(self, text, source="unknown", priority=BubblePriority.IDLE, duration=None):
        if duration is None:
            duration = self._config.get("bubble_duration_sec")

        msg = BubbleMsg(text=text, duration=duration, source=source, priority=priority)
        self._engine.handle_bubble_request(msg)

    def start_random_move(self):
        self._engine.start_move()

    def stop_random_move(self):
        self._engine.stop_move()

    def get_config(self, key):
        return self._config.get(key)

    def get_idle_time(self):
        """只支持Windows，统一出口检测系统空闲时长"""
        try:
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
            lastInputInfo = LASTINPUTINFO()
            lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))
            millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
            return millis / 1000.0
        except Exception:
            return 0

    def get_random_quote(self, filename):
        try:
            file_path = resource_path("assets", filename)

            if not os.path.exists(file_path):
                return f"文件不存在: {file_path}"

            with open(file_path, "r", encoding="utf-8") as f:
                quotes = [line.strip() for line in f if line.strip()]

            return random.choice(quotes) if quotes else "突然忘记我要说啥了"

        except Exception as e:
            print(f"读取文案失败: {e}")
            return "（别吵，我在烧烤...）"