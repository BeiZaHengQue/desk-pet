import logging
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from .renderer import SpeechBubbleWidget

logger = logging.getLogger(__name__)

class SpeechManager(QObject):
    speech_finished = pyqtSignal()

    def __init__(self, pet_widget):
        super().__init__()
        self.pet_widget = pet_widget
        self.ui_widget = None
        
        self.internal_timer = QTimer()
        self.internal_timer.setSingleShot(True)
        self.internal_timer.timeout.connect(self._on_timer_timeout)

    def execute(self, text: str, duration_sec: int):
        """Speech 执行层：渲染开始与安全审计"""
        self.clear_ui()
        logger.debug("Speech 执行层 | 接收到显示指令 | 准备渲染 UI 气泡")
        try:
            self.ui_widget = SpeechBubbleWidget(text, parent=self.pet_widget)
            self.ui_widget.sync_layout(self.pet_widget)
            logger.info("Speech 执行层 | 渲染成功并开始显示 | 字符长度: %d | 计划存在时长: %ds", len(text), duration_sec)
            self.internal_timer.start(duration_sec * 1000)
        except Exception as e:
            logger.error("Speech 执行层 | 渲染失败 | 捕获底层 GUI 渲染崩溃异常: %s", e, exc_info=True)
            self.dismiss()

    def dismiss(self):
        """强制销毁（可能因为抢占打断、可能因为 cancel）"""
        if self.internal_timer.isActive():
            logger.info("Speech 执行层 | 气泡被打断或被强制 Cancel")
            self.internal_timer.stop()
        self.clear_ui()
        logger.debug("Speech 回调 | 发送 dismissed 信号")
        self.speech_finished.emit()

    def _on_timer_timeout(self):
        """定时器耗尽自然死亡"""
        logger.info("Speech 执行层 | 气泡生命周期到期自然消亡")
        self.clear_ui()
        logger.debug("Speech 回调 | 发送 speech_finished 信号")
        self.speech_finished.emit()

    def sync_position(self):
        """气泡位置同步"""
        if self.ui_widget and self.ui_widget.isVisible():
            try:
                self.ui_widget.sync_layout(self.pet_widget)
            except RuntimeError:
                # 拦截 PyQt 底层包装的 C++ 孤儿对象销毁残留，静默清理
                self.ui_widget = None

    def clear_ui(self):
        if self.ui_widget:
            try:
                self.ui_widget.close()
                self.ui_widget.deleteLater()
            except Exception:
                pass
            self.ui_widget = None