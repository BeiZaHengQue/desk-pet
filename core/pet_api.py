import os
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

    def close_bubble_by_source(self, source):
        """通知引擎定点清除特定来源的气泡"""
        self._engine.close_bubble_by_source(source)

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

    def dispatch_state_packet(self, packet: dict):
        """
        、外部模块/拓展插件接入底层核心状态机的安全状态包分发出口
        """
        self._engine.change_state_packet(packet)