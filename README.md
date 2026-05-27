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
│           ├── idle.txt          # 待机无聊说话文案（一行一句）
│           └── interact.txt   # 点击互动说话文案（一行一句）
├── config/
│
├── core/                           
│
├── modules/ 
|                
├── ui/                                           
│
├── utils/                               
│                
└── main.py  