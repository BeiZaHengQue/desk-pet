from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,
                             QSlider, QSpinBox, QPushButton, QGroupBox,
                             QMessageBox, QLabel, QTabWidget)
from PyQt5.QtCore import Qt


class ControlPanel(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.setWindowTitle("桌宠控制面板")
        self.setFixedSize(380, 520)
        self.setup_ui()
        self.sync_from_config()

        # 监听全局配置变更以更新界面
        self.config.config_changed.connect(self.sync_from_config)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # 基础设置区
        group_basic = QGroupBox("基础设置")
        group_basic.setStyleSheet("QGroupBox { font-weight: bold; font-family: 'Microsoft YaHei'; }")
        layout_basic = QHBoxLayout(group_basic)
        layout_basic.setContentsMargins(10, 15, 10, 15)
        layout_basic.setSpacing(15)

        self.chk_top = QCheckBox("桌宠置顶")
        self.chk_move = QCheckBox("自主走动")
        self.chk_idle_text = QCheckBox("无聊说话")

        #复选框移到文字右边
        self.chk_top.setLayoutDirection(Qt.RightToLeft)
        self.chk_move.setLayoutDirection(Qt.RightToLeft)
        self.chk_idle_text.setLayoutDirection(Qt.RightToLeft)

        layout_basic.addWidget(self.chk_top)
        layout_basic.addWidget(self.chk_move)
        layout_basic.addWidget(self.chk_idle_text)
        main_layout.addWidget(group_basic)

        # 参数设置区
        group_param = QGroupBox("参数设置")
        group_param.setStyleSheet("QGroupBox { font-weight: bold; font-family: 'Microsoft YaHei'; }")
        layout_param = QVBoxLayout(group_param)
        layout_param.setContentsMargins(10, 15, 10, 15)
        layout_param.setSpacing(12)

        # 移动间隔/速度
        row_move = QHBoxLayout()
        lbl_move_idle = QLabel("移动间隔(秒):")
        self.spin_move_idle = QSpinBox()
        self.spin_move_idle.setRange(0, 86400)
        
        lbl_move_speed = QLabel("移动速度:")
        self.spin_move_speed = QSpinBox()
        self.spin_move_speed.setRange(0, 1920)
        
        row_move.addWidget(lbl_move_idle)
        row_move.addWidget(self.spin_move_idle)
        row_move.addSpacing(15)
        row_move.addWidget(lbl_move_speed)
        row_move.addWidget(self.spin_move_speed)
        layout_param.addLayout(row_move)

        # 气泡显示时长
        row_dur = QHBoxLayout()
        lbl_bubble_dur = QLabel("气泡显示时长(秒):")
        self.spin_bubble_dur = QSpinBox()
        self.spin_bubble_dur.setRange(1, 180)
        row_dur.addWidget(lbl_bubble_dur)
        row_dur.addWidget(self.spin_bubble_dur)
        row_dur.addStretch()
        layout_param.addLayout(row_dur)

        # 滑块造型的 QSS 样式表
        slider_qss = """
            QSlider::groove:horizontal {
                height: 6px;
                background: #e4e7ed;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #409eff;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #409eff;
                width: 14px;
                height: 14px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #409eff;
            }
        """

        # 透明度布局
        row_op = QHBoxLayout()
        lbl_opacity = QLabel("透明度:")
        lbl_opacity.setFixedWidth(60)
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setStyleSheet(slider_qss)
        self.spin_opacity = QSpinBox()
        self.spin_opacity.setRange(0, 100)
        self.spin_opacity.setSuffix("%")
        row_op.addWidget(lbl_opacity)
        row_op.addWidget(self.slider_opacity)
        row_op.addWidget(self.spin_opacity)
        layout_param.addLayout(row_op)

        # 大小缩放布局
        row_sc = QHBoxLayout()
        lbl_scale = QLabel("大小缩放:")
        lbl_scale.setFixedWidth(60)
        self.slider_scale = QSlider(Qt.Horizontal)
        self.slider_scale.setRange(0, 500)
        self.slider_scale.setStyleSheet(slider_qss)
        self.spin_scale = QSpinBox()
        self.spin_scale.setRange(0, 500)
        self.spin_scale.setSuffix("%")
        row_sc.addWidget(lbl_scale)
        row_sc.addWidget(self.slider_scale)
        row_sc.addWidget(self.spin_scale)
        layout_param.addLayout(row_sc)

        main_layout.addWidget(group_param)

        # 绑定滑块与微调框的 bidirection 双向数值同步
        self.slider_opacity.valueChanged.connect(self.spin_opacity.setValue)
        self.spin_opacity.valueChanged.connect(self.slider_opacity.setValue)
        self.slider_scale.valueChanged.connect(self.spin_scale.setValue)
        self.spin_scale.valueChanged.connect(self.slider_scale.setValue)

        # 页签
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabBar::tab { font-family: 'Microsoft YaHei'; }")
        
        # 第一页签：功能设置
        tab_func_page = QWidget()
        layout_tab_func = QHBoxLayout(tab_func_page)
        layout_tab_func.setContentsMargins(15, 15, 15, 15)
        layout_tab_func.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout_tab_func.setSpacing(25)

        self.chk_hourly = QCheckBox("整点报时")
        self.chk_half_hourly = QCheckBox("半点报时")
        layout_tab_func.addWidget(self.chk_hourly)
        layout_tab_func.addWidget(self.chk_half_hourly)
        
        self.tab_widget.addTab(tab_func_page, "功能设置")
        main_layout.addWidget(self.tab_widget)

        # 底部按钮区
        layout_btn = QHBoxLayout()
        layout_btn.addStretch(1)

        self.btn_save_default = QPushButton("保存配置")
        self.btn_save_default.setFixedSize(100,30)
        self.btn_save_default.setStyleSheet("background-color: #1890ff; color: white; border-radius: 4px; border-radius: 4px; font-family: 'Microsoft YaHei';")

        self.btn_reset = QPushButton("恢复默认配置")
        self.btn_reset.setFixedSize(100, 30)
        self.btn_reset.setStyleSheet("background-color: #f56c6c; color: white; border-radius: 4px; font-family: 'Microsoft YaHei';")

        self.btn_close = QPushButton("关闭面板")
        self.btn_close.setFixedSize(100, 30)
        self.btn_close.setStyleSheet("background-color: #409eff; color: white; border-radius: 4px; font-family: 'Microsoft YaHei';")

        layout_btn.addWidget(self.btn_save_default)
        layout_btn.addWidget(self.btn_reset)
        layout_btn.addWidget(self.btn_close)
        main_layout.addLayout(layout_btn)

        # 统一信号事件绑定
        self.chk_top.toggled.connect(lambda v: self.config.set("always_on_top", v))
        self.chk_move.toggled.connect(lambda v: self.config.set("random_move", v))
        self.chk_idle_text.toggled.connect(lambda v: self.config.set("idle_text", v))
        
        self.slider_opacity.valueChanged.connect(lambda v: self.config.set("opacity", v / 100.0))
        self.slider_scale.valueChanged.connect(lambda v: self.config.set("scale", v / 100.0))

        self.spin_move_idle.editingFinished.connect(
            lambda: self.config.set("move_idle_sec", self.spin_move_idle.value()))
        self.spin_move_speed.editingFinished.connect(
            lambda: self.config.set("move_speed", self.spin_move_speed.value()))
        self.spin_bubble_dur.editingFinished.connect(
            lambda: self.config.set("bubble_duration_sec", self.spin_bubble_dur.value()))

        self.chk_hourly.toggled.connect(lambda v: self.config.set("hourly", v))
        self.chk_half_hourly.toggled.connect(lambda v: self.config.set("half_hourly", v))

        self.btn_save_default.clicked.connect(self.save_default)
        self.btn_close.clicked.connect(self.hide)
        self.btn_reset.clicked.connect(self.handle_reset)

    def sync_from_config(self):
        c = self.config.get_all()
        self.blockSignals(True)

        # 同步滑块与微调器数值
        op_val = int(c["opacity"] * 100)
        sc_val = int(c["scale"] * 100)
        self.slider_opacity.setValue(op_val)
        self.spin_opacity.setValue(op_val)
        self.slider_scale.setValue(sc_val)
        self.spin_scale.setValue(sc_val)

        self.chk_top.setChecked(c["always_on_top"])
        self.chk_move.setChecked(c["random_move"])
        self.chk_idle_text.setChecked(c["idle_text"])
        
        self.spin_move_idle.setValue(c["move_idle_sec"])
        self.spin_move_speed.setValue(c["move_speed"])
        self.spin_bubble_dur.setValue(c["bubble_duration_sec"])
        
        self.chk_hourly.setChecked(c["hourly"])
        self.chk_half_hourly.setChecked(c["half_hourly"])

        self.blockSignals(False)

    def handle_reset(self):
        reply = QMessageBox.question(self, "确认", "是否确认恢复为默认配置?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.config.reset_to_default()

    def save_default(self):
        reply = QMessageBox.question(
            self, "确认", "是否将当前配置保存为默认配置?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config.save_current_as_default()

    def closeEvent(self, event):
        self.hide()
        event.ignore()