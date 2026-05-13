from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,
                             QSlider, QSpinBox, QPushButton, QGroupBox,
                             QMessageBox, QFormLayout, QLabel)
from PyQt5.QtCore import Qt


class ControlPanel(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.setWindowTitle("桌宠控制面板")
        self.setFixedSize(360, 480)
        self.setup_ui()
        self.sync_from_config()

        # 监听全局配置变更以更新界面
        self.config.config_changed.connect(self.sync_from_config)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # --- 基础设置区 ---
        group_basic = QGroupBox("基础设置")
        group_basic.setStyleSheet("QGroupBox { font-weight: bold; font-family: 'Microsoft YaHei'; }")
        layout_basic = QFormLayout(group_basic)

        self.chk_top = QCheckBox("桌宠置顶")
        self.chk_move = QCheckBox("待机移动")
        self.chk_idle_text = QCheckBox("待机说话")

        # 透明度布局
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.lbl_opacity_val = QLabel("100%")
        h_layout_op = QHBoxLayout()
        h_layout_op.addWidget(self.slider_opacity)
        h_layout_op.addWidget(self.lbl_opacity_val)

        # 缩放布局
        self.slider_scale = QSlider(Qt.Horizontal)
        self.slider_scale.setRange(0, 500)
        self.lbl_scale_val = QLabel("100%")
        h_layout_sc = QHBoxLayout()
        h_layout_sc.addWidget(self.slider_scale)
        h_layout_sc.addWidget(self.lbl_scale_val)

        # 数值标签布局
        layout_basic.addRow("透明度:", h_layout_op)
        layout_basic.addRow("大小缩放:", h_layout_sc)
        layout_basic.addRow("置顶:", self.chk_top)
        layout_basic.addRow("移动:", self.chk_move)
        layout_basic.addRow("说话:", self.chk_idle_text)
        main_layout.addWidget(group_basic)

        # --- 参数设置区 ---
        group_param = QGroupBox("参数设置")
        layout_param = QFormLayout(group_param)

        self.spin_move_idle = QSpinBox()
        self.spin_move_idle.setRange(0, 86400)
        self.spin_move_speed = QSpinBox()
        self.spin_move_speed.setRange(0, 1920)
        self.spin_bubble_idle = QSpinBox()
        self.spin_bubble_idle.setRange(0, 3600)
        self.spin_bubble_dur = QSpinBox()
        self.spin_bubble_dur.setRange(1, 180)

        layout_param.addRow("移动间隔(秒):", self.spin_move_idle)
        layout_param.addRow("移动速度(像素/帧):", self.spin_move_speed)
        layout_param.addRow("气泡显示间隔(秒):", self.spin_bubble_idle)
        layout_param.addRow("气泡显示时长(秒):", self.spin_bubble_dur)
        main_layout.addWidget(group_param)

        # 绑定滑块数值回显信号
        self.slider_opacity.valueChanged.connect(lambda v: self.lbl_opacity_val.setText(f"{v}%"))
        self.slider_scale.valueChanged.connect(lambda v: self.lbl_scale_val.setText(f"{v}%"))

        # --- 功能设置区 ---
        group_func = QGroupBox("功能设置")
        group_func.setStyleSheet("QGroupBox { font-weight: bold; font-family: 'Microsoft YaHei'; }")
        layout_func = QHBoxLayout(group_func)

        self.chk_hourly = QCheckBox("整点报时")
        self.chk_half_hourly = QCheckBox("半点报时")
        layout_func.addWidget(self.chk_hourly)
        layout_func.addWidget(self.chk_half_hourly)
        main_layout.addWidget(group_func)

        # --- 底部按钮区 ---
        layout_btn = QHBoxLayout()
        layout_btn.addStretch(1)

        self.btn_reset = QPushButton("恢复默认配置")
        self.btn_reset.setFixedSize(100, 30)
        self.btn_reset.setStyleSheet("background-color: #f56c6c; color: white; border-radius: 4px;")

        self.btn_close = QPushButton("关闭面板")
        self.btn_close.setFixedSize(100, 30)
        self.btn_close.setStyleSheet("background-color: #409eff; color: white; border-radius: 4px;")

        layout_btn.addWidget(self.btn_reset)
        layout_btn.addWidget(self.btn_close)
        main_layout.addLayout(layout_btn)

        # 绑定事件
        self.slider_opacity.valueChanged.connect(lambda v: self.lbl_opacity_val.setText(f"{v}%"))
        self.slider_scale.valueChanged.connect(lambda v: self.lbl_scale_val.setText(f"{v}%"))

        self.chk_top.toggled.connect(lambda v: self.config.set("always_on_top", v))
        self.chk_move.toggled.connect(lambda v: self.config.set("random_move", v))
        self.chk_idle_text.toggled.connect(lambda v: self.config.set("idle_text", v))
        self.slider_opacity.valueChanged.connect(lambda v: self.config.set("opacity", v / 100.0))
        self.slider_scale.valueChanged.connect(lambda v: self.config.set("scale", v / 100.0))

        self.spin_move_idle.editingFinished.connect(
            lambda: self.config.set("move_idle_sec", self.spin_move_idle.value()))
        self.spin_move_speed.editingFinished.connect(
            lambda: self.config.set("move_speed", self.spin_move_speed.value()))
        self.spin_bubble_idle.editingFinished.connect(
            lambda: self.config.set("bubble_idle_sec", self.spin_bubble_idle.value()))
        self.spin_bubble_dur.editingFinished.connect(
            lambda: self.config.set("bubble_duration_sec", self.spin_bubble_dur.value()))

        self.chk_hourly.toggled.connect(lambda v: self.config.set("hourly", v))
        self.chk_half_hourly.toggled.connect(lambda v: self.config.set("half_hourly", v))

        self.btn_close.clicked.connect(self.hide)
        self.btn_reset.clicked.connect(self.handle_reset)

    def sync_from_config(self):
        c = self.config.get_all()
        self.blockSignals(True)

        # 同步数值与标签
        op_val = int(c["opacity"] * 100)
        sc_val = int(c["scale"] * 100)
        self.slider_opacity.setValue(op_val)
        self.lbl_opacity_val.setText(f"{op_val}%")
        self.slider_scale.setValue(sc_val)
        self.lbl_scale_val.setText(f"{sc_val}%")

        self.chk_top.setChecked(c["always_on_top"])
        self.chk_move.setChecked(c["random_move"])
        self.chk_idle_text.setChecked(c["idle_text"])
        self.spin_move_idle.setValue(c["move_idle_sec"])
        self.spin_move_speed.setValue(c["move_speed"])
        self.spin_bubble_idle.setValue(c["bubble_idle_sec"])
        self.spin_bubble_dur.setValue(c["bubble_duration_sec"])
        self.chk_hourly.setChecked(c["hourly"])
        self.chk_half_hourly.setChecked(c["half_hourly"])

        self.blockSignals(False)

    def handle_reset(self):
        reply = QMessageBox.question(self, "确认", "是否确认恢复所有配置为默认值？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.config.reset_to_default()

    def closeEvent(self, event):
        self.hide()
        event.ignore()