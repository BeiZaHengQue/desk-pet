<p align="right">
  <a href="./README.md">切换成 中文</a>
</p>

# BeiZi-DeskPet

Windows desktop pet developed with PyQt5

## Features
- Supports custom desktop pet appearances and dialogue content — simply replace or add files in the corresponding folders inside (see the project structure below for details) the assets directory.
(Note: Only GIF files are supported for desktop pet animations.)
- Left-click the desktop pet to interact / Hold and drag to move the pet
- Right-click the desktop pet or system tray icon to open the context menu
- Control panel supports desktop pet size, transparency, and movement settings
- Modular extension architecture

## Download
If the setup process feels too complicated or you simply want to use a ready-to-run version, download it directly below:

[Download](https://github.com/BeiZaHengQue/desk-pet/releases/latest/download/BeiZi-DeskPet.zip)

After downloading and extracting the archive, enter the folder and double-click `BeiZa-DeskPet.exe` to run the program.

## Quick Start
Only Python 3.8 ~ 3.12 is supported.  
Python 3.10 is recommended.

```bash
pip install -r requirements.txt
python main.py
```

## Project Structure
```text
BeiZi-DeskPet/
│
├── assets/                          # External resource folder
│   ├── host/                        # Desktop pet animation resources
│   │   ├── idle/                    # GIF assets for idle state
│   │   ├── interact/                # GIF assets for interaction state
│   │   └── fallback/                # Backup GIF assets for missing resources
│   └── soul/                        # Desktop pet media resources
│       └── text/                    # Desktop pet text database
│           ├── idle.txt         # Idle dialogue lines (one sentence per line)
│           └── interact.txt  # Interaction dialogue lines (one sentence per line)
├── config/
│
├── core/                           
│
├── modules/                         

├── ui/                                           
│
├── utils/                               
│                
└── main.py                         
```