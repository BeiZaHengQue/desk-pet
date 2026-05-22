import random
import math
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
        # 获取首帧，如果失败用空图标兜底
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

        # 将桌宠右键绑定
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
        self.pet_widget.drag_finished.connect(self._reset_move_timer)
        self.pet_widget.clicked.connect(self._on_pet_clicked)
        self.pet_widget.geometry_changed.connect(self._sync_bubble_position)

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_control_panel()

    def show_control_panel(self):
        """展示控制面板并确保置于当前顶层，同步任务栏图标"""
        icon = self.pet_widget.get_first_frame()
        if not icon.isNull():
            self.control_panel.setWindowIcon(icon)
        self.control_panel.showNormal()      # 如果最小化了，恢复正常大小
        self.control_panel.raise_()           # 提到窗口堆叠最上方
        self.control_panel.activateWindow()   # 夺取活动焦点

    def close_bubble_by_source(self, source: str):
        """精准去掉特定来源的气泡"""
        # 过滤掉队列里还未弹出的同源请求
        self.bubble_queue = [msg for msg in self.bubble_queue if msg.source != source]
        
        if self.current_bubble_msg and self.current_bubble_msg.source == source:
            if self.bubble_timer.isActive():
                self.bubble_timer.stop()
            
            self.current_bubble_msg = None
            if self.current_bubble_ui:
                try:
                    # 断开原生销毁槽，防止因 close() 再次重复推进队列造成断档
                    self.current_bubble_ui.destroyed.disconnect(self._process_next_bubble)
                except TypeError:
                    pass
                self.current_bubble_ui.close()
                self.current_bubble_ui.deleteLater()
                self.current_bubble_ui = None
            
            # 释放当前后，推进下一个气泡
            self._process_next_bubble()

    def _sync_bubble_position(self):
        """气泡同步"""
        if self.current_bubble_ui and self.current_bubble_ui.isVisible():
            try:
                self.current_bubble_ui.update_position(self.pet_widget)
            except RuntimeError:
                self.current_bubble_ui = None

    def _on_pet_clicked(self):
        """响应点击事件"""
        self.pet_widget.switch_scene("interact")
        quote = self.api.get_random_quote("interact")
        
        self.api.show_bubble(
            text=quote,
            source="user_click",
            priority=BubblePriority.INTERACTIVE,
            duration=self.config.get("bubble_duration_sec")
        )

        # 通知模块管理器重置待机说话的计时器
        for module in self.module_manager.modules:
            if hasattr(module, "reset_timer_only") and self.config.get("idle_text"):
                module.reset_timer_only()
                
    def _on_config_changed(self):
        c = self.config.get_all()

        # 同步菜单状态
        self.action_top.setChecked(c["always_on_top"])
        self.action_move.setChecked(c["random_move"])

        # 只有在“桌宠置顶”状态真正改变时，才修改底层 WindowFlags
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

        # 通知扩展模块
        self.module_manager.refresh_modules()

        # 处理移动逻辑重置
        if c["random_move"]:
            self._reset_move_timer()
        else:
            self._stop_all_move()

    def handle_bubble_request(self, msg: BubbleMsg):
        """处理气泡请求入口 """
        # 当前没有气泡，直接显示
        if not self.current_bubble_ui:
            self._render_bubble(msg)
            return

        # 有气泡正在显示
        # 同触发源直接覆盖
        if msg.source == self.current_bubble_msg.source:
            self._force_close_current()
            self._render_bubble(msg)
            return

        # 优先级高于当前则直接覆盖
        if msg.priority > self.current_bubble_msg.priority:
            self._force_close_current()  # 被覆盖的气泡直接抛弃
            self._render_bubble(msg)
            return

        # 优先级小于等于当前则入队排队
        self._enqueue_bubble(msg)

    def _enqueue_bubble(self, msg: BubbleMsg):
        """入队逻辑与队列同源去重"""
        # 如果队列里已经有同源请求，替换成最新的
        for i, existing_msg in enumerate(self.bubble_queue):
            if existing_msg.source == msg.source:
                self.bubble_queue[i] = msg
                return

        self.bubble_queue.append(msg)
        # 优先级从高到低排队，同一级按时间先后
        self.bubble_queue.sort(key=lambda x: (-x.priority, x.timestamp))

    def _render_bubble(self, msg: BubbleMsg):
        """执行UI渲染与绑定"""
        self.current_bubble_msg = msg
        try:
            self.current_bubble_ui = Bubble(msg.text, parent=self.pet_widget)

            # 信号槽强绑定
            self.current_bubble_ui.destroyed.connect(self._process_next_bubble)
            self.current_bubble_ui.update_position(self.pet_widget)

            self.bubble_timer.start(msg.duration * 1000)

        except Exception as e:
            # 界面渲染崩溃，立刻启动销毁，避免幽灵气泡霸占队列
            print(f"气泡渲染遇到冲突拦截: {e}")
            self._force_close_current()
            self._process_next_bubble()  # 释放队列

    def _on_bubble_timeout(self):
        """时间到了，触发自然销毁（依赖原生 destroyed 信号推进队列）"""
        self.bubble_timer.stop()
        if self.current_bubble_ui:
            self.current_bubble_ui.close()
            self.current_bubble_ui.deleteLater()

    def _force_close_current(self):
        """强制打断（高优先级覆盖同/低优先级时使用）"""
        self.bubble_timer.stop()
        if self.current_bubble_ui:
            try:
                # 解绑原生信号，防止旧气泡死亡时带走新气泡的引用
                self.current_bubble_ui.destroyed.disconnect(self._process_next_bubble)
            except TypeError:
                pass

            self.current_bubble_ui.close()
            self.current_bubble_ui.deleteLater()

            # 主动清空当前引用，为新气泡腾出位置
            self.current_bubble_ui = None
            self.current_bubble_msg = None

    def _process_next_bubble(self):
        """由原生 destroyed 信号触发（只有自然销毁才会走到这里）"""
        self.current_bubble_ui = None
        self.current_bubble_msg = None

        if self.bubble_queue:
            next_msg = self.bubble_queue.pop(0)
            self._render_bubble(next_msg)
        else:
            # 气泡队列排空，说明当前没有话要说了，动作切回待机
            self.pet_widget.switch_scene("idle")

    def _reset_move_timer(self):
        self._stop_all_move()
        if self.config.get("random_move"):
            self.wait_timer.start(self.config.get("move_idle_sec") * 1000)

    def _stop_all_move(self):
        self.wait_timer.stop()
        self.move_timer.stop()
        self._moving = False

    def _trigger_move_cycle(self):
        self._moving = True
        self._move_total_time = random.randint(3000, 9000)  # 3到9秒
        self._move_time_passed = 0
        self._move_angle = random.uniform(0, 2 * math.pi)
        self.pet_widget.switch_scene("move")
        self.move_timer.start()

    def _update_position(self):
        self._move_time_passed += 15
        if self._move_time_passed >= self._move_total_time:
            self._reset_move_timer()
            self.pet_widget.switch_scene("idle") 
            return

        # 移动超过3秒后，每3秒有60%概率重新随机方向
        if self._move_time_passed >= 3000 and self._move_time_passed % 3000 < 15:
            if random.random() < 0.6:
                self._move_angle = random.uniform(0, 2 * math.pi)

        speed = self.config.get("move_speed")
        dx = speed * math.cos(self._move_angle)
        dy = speed * math.sin(self._move_angle)

        screen = QApplication.primaryScreen().availableGeometry()
        new_x = self.pet_widget.x() + dx
        new_y = self.pet_widget.y() + dy

        # 触边判定：根据桌宠当前尺寸判定触碰，反向弹开重设角度
        hit_edge = False
        if new_x <= screen.left() or new_x + self.pet_widget.width() >= screen.right():
            hit_edge = True
        if new_y <= screen.top() or new_y + self.pet_widget.height() >= screen.bottom():
            hit_edge = True

        if hit_edge:
            self._move_angle = random.uniform(0, 2 * math.pi)
            # 防止穿墙卡住，拉回一点
            new_x = max(screen.left(), min(new_x, screen.right() - self.pet_widget.width()))
            new_y = max(screen.top(), min(new_y, screen.bottom() - self.pet_widget.height()))

        self.pet_widget.move(int(new_x), int(new_y))

    def start(self):
        # 初始化UI并应用默认状态
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