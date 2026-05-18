from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt5.QtGui import QMovie, QIcon
import time
from utils.resource_manager import ResourceManager

class PetWidget(QLabel):
    geometry_changed = pyqtSignal()
    clicked = pyqtSignal()
    drag_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.PointingHandCursor)

        self._movie = None
        self._base_size = None
        self.current_scale = 1.0
        
        # 显式初始化拖拽状态
        self._is_dragging = False
        self._press_pos = QPoint()
        self._drag_offset = QPoint()
        self._press_time = 0
        self._click_canceled = False
        
        # 启动默认场景
        self.switch_scene("idle")

    def get_first_frame(self):
        """获取当前 GIF 的第一帧作为图标"""
        if self._movie and self._movie.isValid():
            self._movie.jumpToFrame(0)
            pixmap = self._movie.currentPixmap()
            if pixmap.isNull():
                return QIcon()
            return QIcon(pixmap)
        return QIcon()

    def switch_scene(self, scene_name):
        """一键切换 GIF 场景"""
        gif_path = ResourceManager.get_host_gif(scene_name)
        if not gif_path:
            return

        if self._movie:
            self._movie.stop()

        # 加载新 GIF
        self._movie = QMovie(gif_path)
        self.setMovie(self._movie)
        
        # 预读第一帧获取原始尺寸
        self._movie.jumpToFrame(0)
        self._base_size = self._movie.currentImage().size()
 
        self.set_scale(self.current_scale)

    def set_scale(self, scale):
        """原地缩放"""
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