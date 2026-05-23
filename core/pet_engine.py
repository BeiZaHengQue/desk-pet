import random
import math
import os
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon
from ui.pet_widget import PetWidget
from ui.control_panel import ControlPanel
from ui.bubble import Bubble
from core.config_manager import ConfigManager
from core.types import BubblePriority, BubbleMsg
from core.pet_api import PetAPI
from core.module_manager import ModuleManager


class PetEngine:
    def __init__(self):
        self.config = ConfigManager()
        self.pet_widget = PetWidget()
        self.control_panel = ControlPanel(self.config)
        self.api = PetAPI(self, self.config)
        self.module_manager = ModuleManager(self.api, self.config)

        self.bubble_queue = []  # 待显示气泡队列
        self.current_bubble_ui = None
        self.current_bubble_msg = None

        self.bubble_timer = QTimer()
        self.bubble_timer.setSingleShot(True)
        self.bubble_timer.timeout.connect(self._on_bubble_timeout)

        # 移动状态机定时器
        self.wait_timer = QTimer()
        self.wait_timer.setSingleShot(True)
        self.wait_timer.timeout.connect(self._trigger_move_cycle)

        self.move_timer = QTimer()
        self.move_timer.setInterval(15)  # 固定15ms帧率
        self.move_timer.timeout.connect(self._update_position)

        self._moving = False
        self._move_angle = 0.0
        self._move_time_passed = 0
        self._move_total_time = 0

        self._init_tray_and_menu()
        self._bind_signals()

    def _init_tray_and_menu(self):
        self.tray_icon = QSystemTrayIcon(self.pet_widget)
        icon = self.pet_widget.get_first_frame()
        self.tray_icon.setIcon(icon if not icon.isNull() else QIcon())
        self.tray_icon.show()

        self.tray_menu = QMenu()
        self.pet_menu = QMenu()

        self.action_top = QAction("桌宠置顶", self.tray_menu, checkable=True)
        self.action_move = QAction("自主走动", self.tray_menu, checkable=True)
        self.action_panel = QAction("打开控制面板", self.tray_menu)
        self.action_quit = QAction("退出程序", self.tray_menu)

        self.tray_menu.addActions([self.action_top, self.action_move, self.action_panel, self.action_quit])
        self.pet_menu.addActions([self.action_top, self.action_move, self.action_panel, self.action_quit])

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)

        self.pet_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pet_widget.customContextMenuRequested.connect(
            lambda pos: self.pet_menu.exec_(self.pet_widget.mapToGlobal(pos))
        )

        self.action_top.triggered.connect(lambda v: self.config.set("always_on_top", v))
        self.action_move.triggered.connect(lambda v: self.config.set("random_move", v))
        self.action_panel.triggered.connect(self.show_control_panel)
        self.action_quit.triggered.connect(self.stop)

    def _bind_signals(self):
        self.config.config_changed.connect(self._on_config_changed)
        self.pet_widget.drag_started.connect(self._on_drag_started)
        self.pet_widget.drag_finished.connect(self._reset_move_timer)
        self.pet_widget.clicked.connect(self._on_pet_clicked)
        self.pet_widget.geometry_changed.connect(self._sync_bubble_position)

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_control_panel()

    def show_control_panel(self):
        icon = self.pet_widget.get_first_frame()
        if not icon.isNull():
            self.control_panel.setWindowIcon(icon)
        self.control_panel.showNormal()
        self.control_panel.raise_()
        self.control_panel.activateWindow()

    def close_bubble_by_source(self, source: str):
        self.bubble_queue = [msg for msg in self.bubble_queue if msg.source != source]
        
        if self.current_bubble_msg and self.current_bubble_msg.source == source:
            if self.bubble_timer.isActive():
                self.bubble_timer.stop()
            
            self.current_bubble_msg = None
            if self.current_bubble_ui:
                try:
                    self.current_bubble_ui.destroyed.disconnect(self._process_next_bubble)
                except TypeError:
                    pass
                self.current_bubble_ui.close()
                self.current_bubble_ui.deleteLater()
                self.current_bubble_ui = None
            
            self._process_next_bubble()

    def _sync_bubble_position(self):
        if self.current_bubble_ui and self.current_bubble_ui.isVisible():
            try:
                self.current_bubble_ui.update_position(self.pet_widget)
            except RuntimeError:
                self.current_bubble_ui = None

    def change_state_packet(self, packet: dict):
        if "animation" in packet:
            self.pet_widget.switch_scene(packet["animation"])
            
        if "speak" in packet:
            self._proc_state_speak(packet["speak"])

    def _proc_state_speak(self, speak_config: dict):
        text_type = speak_config.get("text_type")
        priority = speak_config.get("priority", BubblePriority.IDLE)
        duration = speak_config.get("duration", self.config.get("bubble_duration_sec", 3))
        source = speak_config.get("source", "state_speech")
        
        from utils.resource_manager import ResourceManager
        file_path = ResourceManager.get_soul_text(text_type)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                quotes = [line.strip() for line in f if line.strip()]
            text = random.choice(quotes) if quotes else "（脑子一片空白，发呆中...）"
        except FileNotFoundError:
            text = f"【文本文件缺失】\n具体异常: FileNotFoundError\n找不到标签 [{text_type}] 对应的配置文件。\n查找路径:\n{file_path}"
        except Exception as e:
            text = f"【读取未知异常】\n类型: {type(e).__name__}\n提示: {str(e)}\n路径: {file_path}"
            
        self.handle_bubble_request(BubbleMsg(text=text, duration=duration, source=source, priority=priority))

    def _on_pet_clicked(self):
        self.wait_timer.stop()
        self.move_timer.stop()
        self._moving = False

        self.change_state_packet({
            "animation": "interact",
            "speak": {
                "text_type": "interact",
                "priority": BubblePriority.INTERACTIVE,
                "source": "user_click",
                "duration": self.config.get("bubble_duration_sec", 3)
            }
        })

        for module in self.module_manager.modules:
            if hasattr(module, "reset_timer_only") and self.config.get("idle_text"):
                module.reset_timer_only()
                
    def _on_config_changed(self):
        c = self.config.get_all()
        self.action_top.setChecked(c["always_on_top"])
        self.action_move.setChecked(c["random_move"])

        current_flags = self.pet_widget.windowFlags()
        is_top = bool(current_flags & Qt.WindowStaysOnTopHint)

        if c["always_on_top"] != is_top:
            if c["always_on_top"]:
                current_flags |= Qt.WindowStaysOnTopHint
            else:
                current_flags &= ~Qt.WindowStaysOnTopHint
            self.pet_widget.setWindowFlags(current_flags)
            self.pet_widget.show()

        self.pet_widget.setWindowOpacity(c["opacity"])
        self.pet_widget.set_scale(c["scale"])

        self.module_manager.refresh_modules()

        if c["random_move"]:
            self._reset_move_timer()
        else:
            self._stop_all_move()

    def handle_bubble_request(self, msg: BubbleMsg):
        if not self.current_bubble_ui:
            self._render_bubble(msg)
            return

        if msg.source == self.current_bubble_msg.source:
            self._force_close_current()
            self._render_bubble(msg)
            return

        if msg.priority > self.current_bubble_msg.priority:
            self._force_close_current()
            self._render_bubble(msg)
            return

        self._enqueue_bubble(msg)

    def _enqueue_bubble(self, msg: BubbleMsg):
        for i, existing_msg in enumerate(self.bubble_queue):
            if existing_msg.source == msg.source:
                self.bubble_queue[i] = msg
                return

        self.bubble_queue.append(msg)
        self.bubble_queue.sort(key=lambda x: (-x.priority, x.timestamp))

    def _render_bubble(self, msg: BubbleMsg):
        self.current_bubble_msg = msg
        try:
            self.current_bubble_ui = Bubble(msg.text, parent=self.pet_widget)
            self.current_bubble_ui.destroyed.connect(self._process_next_bubble)
            self.current_bubble_ui.update_position(self.pet_widget)
            self.bubble_timer.start(msg.duration * 1000)
        except Exception as e:
            print(f"气泡渲染遇到冲突拦截: {e}")
            self._force_close_current()
            self._process_next_bubble()

    def _on_bubble_timeout(self):
        self.bubble_timer.stop()
        if self.current_bubble_ui:
            self.current_bubble_ui.close()
            self.current_bubble_ui.deleteLater()

    def _force_close_current(self):
        self.bubble_timer.stop()
        if self.current_bubble_ui:
            try:
                self.current_bubble_ui.destroyed.disconnect(self._process_next_bubble)
            except TypeError:
                pass
            self.current_bubble_ui.close()
            self.current_bubble_ui.deleteLater()

            self.current_bubble_ui = None
            self.current_bubble_msg = None

    def _process_next_bubble(self):
        self.current_bubble_ui = None
        self.current_bubble_msg = None

        if self.bubble_queue:
            next_msg = self.bubble_queue.pop(0)
            self._render_bubble(next_msg)
        else:
            # 气泡播放完毕后，交由状态恢复器来决定回 idle 还是继续 move
            self._reset_move_timer()
            
    def _on_drag_started(self):
        """当进入拖拽状态时，立即停止自主移动的所有计时器，防止后台位移覆盖拖拽"""
        self.wait_timer.stop()
        self.move_timer.stop()
        self._moving = False

    def _reset_move_timer(self):
        """
        行为状态恢复器，根据配置智能回归主状态
        """
        self.wait_timer.stop()
        self.move_timer.stop()
        self._moving = False

        # 如果关闭了移动，直接回归静止待机
        if not self.config.get("random_move"):
            self.change_state_packet({"animation": "idle"})
            return

        idle_sec = self.config.get("move_idle_sec")
        
        # 当间隔设为 0 时，直接跨过待机，拉起下一轮走动循环
        if idle_sec <= 0:
            self._trigger_move_cycle()
        else:
            # 只有大于 0 时，才允许进待机冷却队列
            self.change_state_packet({"animation": "idle"})
            self.wait_timer.start(idle_sec * 1000)

    def _stop_all_move(self):
        """
        统一拦截并清理位移控制。
        """
        self.wait_timer.stop()
        self.move_timer.stop()
        self._moving = False
        self.change_state_packet({"animation": "idle"})

    def _trigger_move_cycle(self):
        self._moving = True
        self._move_total_time = random.randint(3000, 9000)
        self._move_time_passed = 0
        self._move_angle = random.uniform(0, 2 * math.pi)
        
        self.change_state_packet({"animation": "move"})
        self.move_timer.start()

    def _update_position(self):
        self._move_time_passed += 15
        if self._move_time_passed >= self._move_total_time:
            self._reset_move_timer()
            return

        if self._move_time_passed >= 3000 and self._move_time_passed % 3000 < 15:
            if random.random() < 0.6:
                self._move_angle = random.uniform(0, 2 * math.pi)

        speed = self.config.get("move_speed")
        dx = speed * math.cos(self._move_angle)
        dy = speed * math.sin(self._move_angle)

        screen = QApplication.primaryScreen().availableGeometry()
        new_x = self.pet_widget.x() + dx
        new_y = self.pet_widget.y() + dy

        hit_edge = False
        if new_x <= screen.left() or new_x + self.pet_widget.width() >= screen.right():
            hit_edge = True
        if new_y <= screen.top() or new_y + self.pet_widget.height() >= screen.bottom():
            hit_edge = True

        if hit_edge:
            self._move_angle = random.uniform(0, 2 * math.pi)
            new_x = max(screen.left(), min(new_x, screen.right() - self.pet_widget.width()))
            new_y = max(screen.top(), min(new_y, screen.bottom() - self.pet_widget.height()))

        self.pet_widget.move(int(new_x), int(new_y))

    def start(self):
        self._on_config_changed()
        screen = QApplication.primaryScreen().availableGeometry()
        self.pet_widget.move(
            (screen.width() - self.pet_widget.width()) // 2,
            (screen.height() - self.pet_widget.height()) // 2
        )
        self.pet_widget.show()
        self.module_manager.start_all()

    def stop(self):
        self.module_manager.stop_all()
        self._stop_all_move()
        self._force_close_current()
        self.pet_widget.close()
        self.control_panel.close()
        self.tray_icon.hide()
        QApplication.quit()