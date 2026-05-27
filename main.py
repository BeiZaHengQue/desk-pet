import sys
from PyQt5.QtWidgets import QApplication

from utils.logging_setup import setup_logging
setup_logging()

from core.pet_engine import PetEngine

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    engine = PetEngine()
    engine.start()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()