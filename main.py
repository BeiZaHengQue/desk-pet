import sys
from PyQt5.QtWidgets import QApplication
from core.pet_engine import PetEngine


def main():
    app = QApplication(sys.argv)
    # 关闭最后一个窗口时不退出，依赖托盘右键退出
    app.setQuitOnLastWindowClosed(False)

    engine = PetEngine()
    engine.start()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()