<p align="right">
  <a href="./README_EN.md">switch English</a>
</p>

# 北子-桌宠
基于 PyQt5 开发的 Windows 桌面宠物

## 支持功能
- 可自定义桌宠形象和说话内容，在 assets 目录里对应的文件夹（具体参考下面的文件结构）内替换即可（注：桌宠形象只支持GIF文件）
- 左键点击桌宠互动/按住桌宠可拖拽
- 右键点击桌宠/系统托盘图标弹出菜单
- 控制面板可定义桌宠大小、透明度和移动设置
- 模块化扩展架构

## 下载
如果觉得过于复杂或者想直接使用现成的可直接点击下方下载：

[下载](https://github.com/BeiZaHengQue/desk-pet/releases/latest/download/BeiZi-DeskPet.zip)

下载解压后进入文件夹双击运行 BeiZa-DeskPet.exe即可

## 快速开始
Python版本只支持 3.8 ～ 3.12，建议Python 3.10
```bash
pip install -r requirements.txt
python main.py
```

## 文件结构
```text
BeiZi-DeskPet/
│
├── assets/                          # 外置资源文件夹
│   ├── host/                        # 桌宠动画形象文件夹
│   │   ├── idle/                    # 存放待机状态的 GIF 素材
│   │   ├── interact/                # 存放被鼠标点击互动状态的 GIF 素材
│   │   └── fallback/                # 存放备用/资源缺失时恢复的 GIF 素材
│   └── soul/                        # 桌宠媒体资源文件夹
│       └── text/                    # 桌宠文本库
│           ├── idle_sentences.txt          # 待机无聊说话文案（一行一句）
│           └── interaction_sentences.txt   # 点击互动说话文案（一行一句）
│
├── core/                            # 核心逻辑控制层
│   ├── config_manager.py            # 配置管理类（处理本地 JSON 读写与回滚）
│   ├── module_manager.py            # 扩展功能模块生命周期管理器
│   ├── pet_api.py                   # 核心中枢向外暴露的系统检测及词库随机抽取接口
│   ├── pet_engine.py                # 引擎主控制中枢（动作切换、移动状态机、托盘及气泡排队调度）
│   └── types.py                     # 全局数据结构定义
│
├── modules/                         # 扩展模块
│   ├── __init__.py                  # 模块基类 BaseModule 定义
│   ├── idle_bubble.py               # 待机无聊说话触发模块
│   └── time_notify.py               # 时间检测与整点/半点报时触发模块 
│
├── ui/                              # UI层
│   ├── bubble.py                    # 无边框气泡提示框 UI（动态算宽、触边反弹
│   ├── control_panel.py             # 桌宠控制面板设置界面 UI（滑块、输入框数值绑定）
│   └── pet_widget.py                # 桌宠本体窗口 UI（透明无边框、GIF渲染、处理鼠标拖拽与点击）
│
├── utils/                           # 工具集
│   ├── __init__.py                  # 工具包初始化文件
│   ├── paths.py                     # 路径解析（兼容本地开发环境与打包后的绝对路径）
│   └── resource_manager.py          # 资源文件扫描与文件过滤器（扫描合法 GIF 和文案路径）
│
├── config.json                      # 运行后自动生成的配置文件 
└── main.py                          # 程序唯一启动入口
```