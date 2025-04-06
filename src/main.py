import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import IMUGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IMUGUI()
    window.show()
    sys.exit(app.exec())