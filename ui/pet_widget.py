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
        self.current_scale = 1.0  # 初始化缩放比例

        self._movie = None
        self._load_gif()

    def _load_gif(self):
        gif_path = resource_path("assets", "cat.gif")

        if os.path.exists(gif_path):
            self._movie = QMovie(gif_path)
            self.setMovie(self._movie)
            self._movie.start()
            self._movie.jumpToFrame(0)

            self._base_size = self._movie.currentImage().size()
            self.resize(self._base_size)
        else:
            print("GIF不存在:", gif_path)
            pixmap = QPixmap(self._base_size)
            pixmap.fill(QColor(200, 200, 200, 150))
            self.setPixmap(pixmap)
            self.resize(self._base_size)

    def get_first_frame(self):
        if self._movie and self._movie.isValid():
            self._movie.jumpToFrame(0)
            return QIcon(self._movie.currentPixmap())
        return QIcon()

    def set_scale(self, scale):
        """原地缩放"""
        # 如果 _base_size 不存在才 return
        if not self._base_size:
            return

        # 记录缩放前的锚点 (当前窗口的底边中点)
        rect = self.geometry()
        anchor_x = rect.x() + rect.width() // 2
        anchor_y = rect.y() + rect.height()

        # 计算新尺寸
        self.current_scale = scale
        new_w = int(self._base_size.width() * scale)
        new_h = int(self._base_size.height() * scale)

        # 逆推新左上角坐标
        new_x = anchor_x - (new_w // 2)
        new_y = anchor_y - new_h

        # 设置新坐标和尺寸
        self.setGeometry(new_x, new_y, new_w, new_h)

        # 更新 GIF 尺寸
        if self._movie:
            self._movie.setScaledSize(self.size())
            # 防止缩放导致 GIF 停顿，强行恢复播放状态
            if self._movie.state() != QMovie.Running:
                self._movie.start()

        self.geometry_changed.emit()

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