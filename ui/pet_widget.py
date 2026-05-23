from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt5.QtGui import QMovie, QIcon
import time
from utils.resource_manager import ResourceManager

class PetWidget(QLabel):
    geometry_changed = pyqtSignal()
    clicked = pyqtSignal()
    drag_finished = pyqtSignal()
    # 方便以后通知外部当前真正进入了拖拽状态
    drag_started = pyqtSignal() 

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
        self._protected_until = 0  # 高优先级动画保护截止时间戳（毫秒）
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

    def switch_scene(self, scene_name, duration_ms=0):
        """切换 GIF 场景"""
        current_time = time.time() * 1000
        
        # 如果当前还处于高优先级动画保护期，直接无视后台发来的常规常态
        if current_time < self._protected_until and scene_name in ["idle", "move"]:
            return

        gif_path = ResourceManager.get_host_gif(scene_name)
        if not gif_path:
            return

        if self._movie:
            self._movie.stop()

        self._movie = QMovie(gif_path)
        self.setMovie(self._movie)
        
        self._movie.jumpToFrame(0)
        self._base_size = self._movie.currentImage().size()
        self.set_scale(self.current_scale)
        self._movie.start()  # 确保显式启动播放

        # 如果设定了保护时长，更新截止时间戳
        if duration_ms > 0:
            self._protected_until = current_time + duration_ms

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
            move_distance = (event.globalPos() - self._press_pos).manhattanLength()
            
            # 判定为拖拽的瞬间，切换为 drag 动画
            if move_distance > QApplication.startDragDistance():
                if not self._click_canceled: # 确保只在刚跨越阈值的瞬间切换一次
                    self._click_canceled = True
                    self.drag_started.emit()
                    self.switch_scene("drag") # 瞬间换成拖拽形象

            self.move(event.globalPos() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._is_dragging:
            self._is_dragging = False

            duration = time.time() - self._press_time
            if duration <= 0.3 and not self._click_canceled:
                # 给点击动作 1s 的绝对保护期
                self.switch_scene("click", duration_ms=1000) 
                self.clicked.emit()
            else:
                # 拖拽结束，抛出结束信号
                self.drag_finished.emit()
                
            event.accept()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.geometry_changed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.geometry_changed.emit()