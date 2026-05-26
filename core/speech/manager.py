from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from .renderer import SpeechBubbleWidget

class SpeechManager(QObject):
    speech_finished = pyqtSignal()

    def __init__(self, pet_widget):
        super().__init__()
        self.pet_widget = pet_widget
        self.ui_widget = None
        
        # 独立的 Loop 定时器控制说话时长驱动
        self.internal_timer = QTimer()
        self.internal_timer.setSingleShot(True)
        self.internal_timer.timeout.connect(self.dismiss)

    def execute(self, text: str, duration_sec: int):
        self.clear_ui()
        try:
            self.ui_widget = SpeechBubbleWidget(text, parent=self.pet_widget)
            self.ui_widget.sync_layout(self.pet_widget)
            self.internal_timer.start(duration_sec * 1000)
        except Exception as e:
            print(f"[Speech系统异常] 渲染冲突拦截: {e}")
            self.dismiss()

    def dismiss(self):
        self.internal_timer.stop()
        self.clear_ui()
        self.speech_finished.emit()

    def sync_position(self):
        if self.ui_widget and self.ui_widget.isVisible():
            try:
                self.ui_widget.sync_layout(self.pet_widget)
            except RuntimeError:
                self.ui_widget = None

    def clear_ui(self):
        if self.ui_widget:
            self.ui_widget.close()
            self.ui_widget.deleteLater()
            self.ui_widget = None