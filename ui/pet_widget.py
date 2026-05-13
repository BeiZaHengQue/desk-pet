from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QMovie, QPixmap, QColor, QIcon
import os
import time
from utils.paths import resource_path



class PetWidget(QLabel):
    # 发射点击信号
    clicked = pyqtSignal()
    drag_finished = pyqtSignal()
    geometry_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 窗口基础属性控制，防止被覆盖消失
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.PointingHandCursor)

        self._is_dragging = False
        self._press_pos = None
        self._press_time = 0
        self._click_canceled = False
        self._drag_offset = None
        self._base_size = QSize(128, 128)
        self.movie = None
        self._load_gif()

    def _load_gif(self):
        gif_path = resource_path("assets", "cat.gif")

        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.setMovie(self.movie)
            self.movie.start()
            self.movie.jumpToFrame(0)

            self._base_size = self.movie.currentImage().size()
            self.resize(self._base_size)

        else:
            print("GIF不存在:", gif_path)

            pixmap = QPixmap(self._base_size)
            pixmap.fill(QColor(200, 200, 200, 150))
            self.setPixmap(pixmap)
            self.resize(self._base_size)

    def get_first_frame(self):
        if self.movie and self.movie.isValid():
            self.movie.jumpToFrame(0)
            return QIcon(self.movie.currentPixmap())
        return QIcon()  # 没加载成功返回空图标

    def set_scale(self, scale):
        new_size = QSize(int(self._base_size.width() * scale), int(self._base_size.height() * scale))
        if self.movie:
            self.movie.setScaledSize(new_size)
        self.resize(new_size)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._press_pos = event.globalPos()
            self._drag_offset = event.globalPos() - self.pos()
            self._press_time = time.time()
            self._click_canceled = False
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and event.buttons() == Qt.LeftButton:
            # 移动超过系统阈值，判定为拖拽
            move_distance = (event.globalPos() - self._press_pos).manhattanLength()
            if move_distance > QApplication.startDragDistance():
                self._click_canceled = True

            self.move(event.globalPos() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._is_dragging:
            self._is_dragging = False

            # 判断点击还是拖拽完成
            duration = time.time() - self._press_time
            if duration <= 0.3 and not self._click_canceled:
                self.clicked.emit()
            else:
                self.drag_finished.emit()

            event.accept()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.geometry_changed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.geometry_changed.emit()