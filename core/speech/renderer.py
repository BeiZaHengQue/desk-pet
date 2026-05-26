from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics
from .locator import SpeechLocator

class SpeechBubbleWidget(QWidget):
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
        self.label.setStyleSheet("""
            QLabel {
                color: black;
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.label)

    def sync_layout(self, pet_widget):
        pet_rect = pet_widget.geometry()
        max_w = max(10, int(pet_rect.width() * 1.9))
        text_rect = self.font_metrics.boundingRect(0, 0, max_w, 10221119, Qt.TextWordWrap, self.text)
        
        final_w = max(10, min(max_w, text_rect.width() + 19))
        self.label.setFixedWidth(final_w)
        self.adjustSize()
        
        x, y = SpeechLocator.calculate_position(pet_widget, self.width(), self.height())
        self.move(x, y)
        self.show()