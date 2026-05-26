import os
import ctypes
from core.speech.types import SpeechPriority, SpeechRequest


class PetAPI:
    def __init__(self, engine, config):
        self._engine = engine
        self._config = config

    def speech_request(self, text, source="unknown", priority=SpeechPriority.IDLE, duration=None):
        """讲话请求入口"""
        if duration is None:
            duration = self._config.get("bubble_duration_sec", 3)
        req = SpeechRequest(text=text, duration=duration, source=source, priority=priority)
        self._engine.handle_speech_request(req)

    def cancel_speech_request(self, source):
        """定点销毁指定来源的讲话"""
        self._engine.cancel_speech_request(source)

    def get_config(self, key):
        return self._config.get(key)

    def get_idle_time(self):
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
        self._engine.change_state_packet(packet)