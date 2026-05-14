🐱 简易互动桌宠 (Desktop Pet)
这是一款基于 PyQt5 开发的Windows轻量级桌面萌宠。它不仅能安安静静地陪你写代码，还会定时报时、待机吐槽，并且支持高度自定义——你可以轻松更换你喜欢的 GIF 形象和对话文案。

✨ 项目亮点
🎨 形象自定义：只需替换 assets 目录下的 cat.gif，即可拥有专属桌宠形象。

💬 话痨模式：支持点击互动、整点/半点报时、长时间待机（可自定义）自动吐槽。

🛠️ 控制面板：实时调节透明度、缩放大小、置顶开关及随机移动。

💾 配置记忆：所有设置自动保存至本地 config.json，下次启动依然如初。

🚀 快速开始
如果想快速使用，在
https://github.com/BeiZaHengQue/desk-pet/releases/tag/v0.1.0
内双击desk-pet-windows-v0.1.0.zip下载，解压后打开文件夹运行exe程序
1. 环境准备
确保你的电脑已有 Python 3.11环境，然后安装依赖：
Bash
pip install PyQt5
2. 运行程序
在文件夹内打开cmd
Bash
python main.py
3. 快捷操作
桌宠：
左键按住：拖动桌宠到屏幕任意位置。
左键单击：触发随机互动对话。
右键菜单：打开控制面板、设置置顶、开启/关闭移动或退出程序。

系统托盘：
右键菜单：与桌宠一致
左键双击：打开控制面板

换皮肤：准备一张透明背景的 GIF，重命名为 cat.gif 替换 assets/cat.gif。

改文案：用记事本打开 assets/ 下的 .txt 文件（click_quotes.txt 点击互动文案 idle_quotes.txt 待机吐槽文案），每行写一句你想让它说的话，保存即可。
