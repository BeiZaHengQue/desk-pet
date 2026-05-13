from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics


class Bubble(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text = text
        self.font = QFont("Microsoft YaHei", 10)
        self.font_metrics = QFontMetrics(self.font)

        self.label = QLabel(text)
        self.label.setFont(self.font)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(self._get_style())

        layout.addWidget(self.label)

    def _get_style(self):
        return """
            QLabel {
                color: black;
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px;
            }
        """

    def update_position(self, target_widget):
        pet_rect = target_widget.geometry()
        screen = QApplication.primaryScreen()
        if not screen: return
        screen_rect = screen.availableGeometry()

        # 最大宽度：桌宠宽度的 2.2 倍，兜底限制最小为 10
        max_w = max(10, int(pet_rect.width() * 2.2))

        # 参数顺序：x, y, width, height, flags, text
        text_rect = self.font_metrics.boundingRect(0, 0, max_w, 10221119, Qt.TextWordWrap, self.text)

        # 加 19 为留出内边距
        actual_w = text_rect.width() + 19

        # 取模拟宽度和最大宽度中的较小值，强制锁定宽度
        final_w = max(10, min(max_w, actual_w))
        self.label.setFixedWidth(final_w)
        self.adjustSize()

        # 理想位置计算 (右上方)
        ideal_x = pet_rect.right()
        ideal_y = pet_rect.top() - self.height()

        # 碰撞与反弹处理
        if ideal_y < screen_rect.top():
            ideal_y = pet_rect.top()

        if ideal_x + self.width() > screen_rect.right():
            ideal_x = pet_rect.left() - self.width()
            if ideal_x < screen_rect.left():
                ideal_x = screen_rect.left() + 5

        self.move(ideal_x, ideal_y)
        self.show()