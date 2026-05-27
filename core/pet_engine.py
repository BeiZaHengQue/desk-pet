import random
import math
import logging
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon
from ui.pet_widget import PetWidget
from ui.control_panel import ControlPanel
from core.config_manager import ConfigManager
from core.pet_api import PetAPI
from core.module_manager import ModuleManager
from core.speech.manager import SpeechManager
from core.speech.types import SpeechPriority, SpeechRequest

logger = logging.getLogger(__name__)

class PetEngine:
    def __init__(self):
        logger.info("核心引擎 | 桌宠中央决策大脑正在初始化")
        self.config = ConfigManager()
        self.pet_widget = PetWidget()
        self.control_panel = ControlPanel(self.config)
        self.api = PetAPI(self, self.config)
        self.module_manager = ModuleManager(self.api, self.config)

        self.speech_queue = []  
        self.current_speech_req = None

        self.speech_manager = SpeechManager(self.pet_widget)
        self.speech_manager.speech_finished.connect(self._on_speech_finished)

        self.wait_timer = QTimer()
        self.wait_timer.setSingleShot(True)
        self.wait_timer.timeout.connect(self._trigger_move_cycle)

        self.move_timer = QTimer()
        self.move_timer.setInterval(15)
        self.move_timer.timeout.connect(self._update_position)

        self._moving = False
        self._move_angle = 0.0
        self._move_time_passed = 0
        self._move_total_time = 0
        
        self._last_random_move_state = None 

        self._init_tray_and_menu()
        self._bind_signals()
        logger.info("核心引擎 | 中央决策大脑初始化完成")

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

        self.action_top.triggered.connect(lambda v: self.config.set("always_on_top", v, source="tray_menu"))
        self.action_move.triggered.connect(lambda v: self.config.set("random_move", v, source="tray_menu"))
        self.action_panel.triggered.connect(self.show_control_panel)
        self.action_quit.triggered.connect(self.stop)

    def _bind_signals(self):
        self.config.config_changed.connect(self._on_config_changed)
        self.pet_widget.drag_started.connect(self._on_drag_started)
        self.pet_widget.drag_finished.connect(self._reset_move_timer)
        self.pet_widget.clicked.connect(self._on_pet_clicked)
        self.pet_widget.geometry_changed.connect(self.speech_manager.sync_position)

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

    def handle_speech_request(self, req: SpeechRequest):
        """Speech 仲裁"""
        logger.info("收到 Speech 请求 | 来源=[%s] | 优先级=[%s] | 文本概要=[%s...]", 
                    req.source, SpeechPriority(req.priority).name, req.text[:15].replace("\n", " "))
        
        # 仲裁决策树
        if not self.current_speech_req:
            logger.info("Speech 仲裁层 | 决策=[直接执行] | 原因=当前播放通道处于空闲态")
            self._awaken_speech_subsystem(req)
            return

        if req.source == self.current_speech_req.source:
            logger.info("Speech 仲裁层 | 决策=[同源覆盖] | 原因=来自同一上层模块 [%s] 的连发覆盖请求", req.source)
            self.speech_manager.dismiss()
            self._awaken_speech_subsystem(req)
            return

        if req.priority > self.current_speech_req.priority:
            logger.info("Speech 仲裁层 | 决策=[优先级抢占] | 原因=[%s] 高优先级强行打断当前低优先级 [%s]", 
                        SpeechPriority(req.priority).name, SpeechPriority(self.current_speech_req.priority).name)
            self.speech_manager.dismiss()
            self._awaken_speech_subsystem(req)
            return

        logger.info("Speech 仲裁层 | 决策=[压入排队] | 原因=优先级较低，按规则挂起等待")
        self._enqueue_speech(req)

    def _enqueue_speech(self, req: SpeechRequest):
        for i, existing in enumerate(self.speech_queue):
            if existing.source == req.source:
                self.speech_queue[i] = req
                logger.debug("Speech 仲裁层 | 队列重排 | 同源替换排队请求 | 来源=%s", req.source)
                return
        self.speech_queue.append(req)
        self.speech_queue.sort(key=lambda x: (-x.priority, x.timestamp))

    def _awaken_speech_subsystem(self, req: SpeechRequest):
        self.current_speech_req = req
        self.speech_manager.execute(req.text, req.duration)

    def _on_speech_finished(self):
        """接收完成播报的回调，驱动队列"""
        self.current_speech_req = None
        if self.speech_queue:
            next_req = self.speech_queue.pop(0)
            logger.debug("Speech 队列消耗 | 旧气泡自然消亡，自动提取并分发下一轮挂载请求 | 剩余队长: %d", len(self.speech_queue))
            self._awaken_speech_subsystem(next_req)
        else:
            self._reset_move_timer()

    def cancel_speech_request(self, source: str):
        old_len = len(self.speech_queue)
        self.speech_queue = [r for r in self.speech_queue if r.source != source]
        if len(self.speech_queue) != old_len:
            logger.debug("Speech 仲裁层 | 队列清理 | 外部强制 Cancel 挂起请求 | 来源=%s", source)
            
        if self.current_speech_req and self.current_speech_req.source == source:
            logger.info("Speech 仲裁层 | 执行强拆 | 正在播放的气泡已被上层模块强令 Cancel")
            self.speech_manager.dismiss()

    def change_state_packet(self, packet: dict):
        if "animation" in packet:
            self.pet_widget.switch_scene(packet["animation"])
        if "speak" in packet:
            self._proc_state_speak(packet["speak"])

    def _proc_state_speak(self, speak_config: dict):
        text_type = speak_config.get("text_type")
        priority = speak_config.get("priority", SpeechPriority.IDLE)
        duration = speak_config.get("duration", self.config.get("bubble_duration_sec", 3))
        source = speak_config.get("source", "state_speech")
        
        from utils.resource_manager import ResourceManager
        file_path = ResourceManager.get_soul_text(text_type)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                quotes = [line.strip() for line in f if line.strip()]
            text = random.choice(quotes) if quotes else "（脑子一片空白，发呆中...(文件内容为空)）"
        except FileNotFoundError:
            text = "（核心配置文件缺失）"
        except Exception as e:
            text = "（文本读取异常）"
            logger.error("核心引擎 | 读取语言包失败 | 异常: %s", e)
            
        self.handle_speech_request(SpeechRequest(text=text, duration=duration, source=source, priority=priority))

    def _on_pet_clicked(self):
        logger.info("状态切换 | 进入 interact 交互态 | 原因=用户点击桌宠主体")
        self.wait_timer.stop()
        self.move_timer.stop()
        self._moving = False

        self.change_state_packet({
            "animation": "interact",
            "speak": {
                "text_type": "interact",
                "priority": SpeechPriority.INTERACTIVE,
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

        new_move_config = c["random_move"]
        if self._last_random_move_state != new_move_config:
            logger.info("状态切换 | 移动状态改变 | random_move 旧状态=[%s] 切换为 新状态=[%s]", 
                        self._last_random_move_state, new_move_config)
            self._last_random_move_state = new_move_config
            if new_move_config:
                self._reset_move_timer()
            else:
                self._stop_all_move()

    def _on_drag_started(self):
        logger.info("状态切换 | 进入 drag 拖拽态 | 原因=鼠标强制抓取")
        self.wait_timer.stop()
        self.move_timer.stop()
        self._moving = False

    def _reset_move_timer(self):
        self.wait_timer.stop()
        self.move_timer.stop()
        self._moving = False

        if not self.config.get("random_move"):
            logger.info("状态切换 | 进入 idle 静止态 | 原因=自主走动未开启")
            self.change_state_packet({"animation": "idle"})
            return

        idle_sec = self.config.get("move_idle_sec")
        if idle_sec <= 0:
            self._trigger_move_cycle()
        else:
            logger.info("状态切换 | 进入 idle 冷却态 | 预估静息等待时长: %ds", idle_sec)
            self.change_state_packet({"animation": "idle"})
            self.wait_timer.start(idle_sec * 1000)

    def _stop_all_move(self):
        logger.info("状态切换 | 退出 move 体系 | 原因=自主走动功能被禁用")
        self.wait_timer.stop()
        self.move_timer.stop()
        self._moving = False
        self.change_state_packet({"animation": "idle"})

    def _trigger_move_cycle(self):
        self._moving = True
        self._move_total_time = random.randint(3000, 9000)
        self._move_time_passed = 0
        self._move_angle = random.uniform(0, 2 * math.pi)
        
        logger.info("状态切换 | 进入 move 漫步态 | 预计移动时长: %dms | 基础航向角: %.2f rad", 
                    self._move_total_time, self._move_angle)
        self.change_state_packet({"animation": "move"})
        self.move_timer.start()

    def _update_position(self):
        self._move_time_passed += 15
        if self._move_time_passed >= self._move_total_time:
            self._reset_move_timer()
            return

        # 移动航向自我修正
        if self._move_time_passed >= 3000 and self._move_time_passed % 3000 < 15:
            if random.random() < 0.6:
                self._move_angle = random.uniform(0, 2 * math.pi)
                logger.info("状态切换 | move 航向修正发生 | 新航向角: %.2f rad", self._move_angle)

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
            logger.info("系统交互 | 触边事件触发 | 反弹重定向新航向角: %.2f rad", self._move_angle)

        self.pet_widget.move(int(new_x), int(new_y))

    def start(self):
        logger.info("核心引擎 | 主服务启动")
        self._on_config_changed()
        screen = QApplication.primaryScreen().availableGeometry()
        self.pet_widget.move(
            (screen.width() - self.pet_widget.width()) // 2,
            (screen.height() - self.pet_widget.height()) // 2
        )
        self.pet_widget.show()
        self.module_manager.start_all()

    def stop(self):
        logger.warning("核心引擎 | 收到终结指令，正在剥离常驻服务")
        self.module_manager.stop_all()
        self._stop_all_move()
        self.speech_manager.dismiss()
        self.pet_widget.close()
        self.control_panel.close()
        self.tray_icon.hide()
        logger.info("核心引擎 | 成功解绑卸载，进程退出。")
        QApplication.quit()