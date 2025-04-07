from PyQt6.QtWidgets import QMainWindow, QTabWidget
from .serial_tab import SerialTab
from .data_tab import DataTab
from .test_tab import TestTab
import json

class IMUGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IMU Data Collection")
        self.setGeometry(100, 100, 800, 600)

        self.serial_port = None
        self.test_results = []

        self.load_test_results()  # Load any previous test results from file

        self.initUI()

    def initUI(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Serial Connection Tab
        self.serial_tab_widget = SerialTab(self)
        self.tabs.addTab(self.serial_tab_widget, "Serial Connection")

        # Data Collection Tab
        self.data_tab_widget = DataTab(self)
        self.tabs.addTab(self.data_tab_widget, "Data Collection")

        # Joint Mobility Test Tab
        self.test_tab_widget = TestTab(self)
        self.tabs.addTab(self.test_tab_widget, "Joint Mobility Test")

    def load_test_results(self):
        try:
            with open('data/test_results.json', 'r') as file:
                self.test_results = json.load(file)
        except FileNotFoundError:
            self.test_results = []

    def save_test_results(self):
        with open('data/test_results.json', 'w') as file:
            json_lines = [json.dumps(result) for result in self.test_results]
            file.write('[\n  ' + ',\n  '.join(json_lines) + '\n]')

    def closeEvent(self, event):
        # Events on close of application
        pass