from enum import IntEnum
from dataclasses import dataclass, field
import time

class SpeechPriority(IntEnum):
    IDLE = 1         # 待机级
    INTERACTIVE = 2  # 互动级
    SYSTEM = 3       # 系统级

@dataclass
class SpeechRequest:
    text: str
    duration: int
    source: str
    priority: SpeechPriority
    timestamp: float = field(default_factory=time.time)