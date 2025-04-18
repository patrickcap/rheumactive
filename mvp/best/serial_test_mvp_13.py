import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QTabWidget, QTextEdit
)
from PyQt6.QtCore import QTimer, QDateTime
import pyqtgraph as pg
import json

class IMUGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IMU Data Collection")
        self.setGeometry(100, 100, 800, 600)

        self.serial_port = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial_data)
        
        self.datum = None
        self.test_results = []
        self.test_active = False
        self.test_start_time = None
        
        self.load_test_results()  # Load any previous test results from file
        
        self.initUI()

    def initUI(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Serial Connection Tab
        self.serial_tab = QWidget()
        self.tabs.addTab(self.serial_tab, "Serial Connection")
        self.initSerialTab()
        
        # Data Collection Tab
        self.data_tab = QWidget()
        self.tabs.addTab(self.data_tab, "Data Collection")
        self.initDataTab()

        # Joint Mobility Test Tab
        self.test_tab = QWidget()
        self.tabs.addTab(self.test_tab, "Joint Mobility Test")
        self.initTestTab()
    
    def initSerialTab(self):
        layout = QVBoxLayout()
        
        self.port_label = QLabel("Select Serial Port:")
        layout.addWidget(self.port_label)
        
        self.port_combobox = QComboBox()
        self.update_serial_ports()
        layout.addWidget(self.port_combobox)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_serial)
        layout.addWidget(self.connect_button)
        
        self.serial_status = QLabel("Status: Not Connected")
        layout.addWidget(self.serial_status)
        
        self.serial_tab.setLayout(layout)

    def initDataTab(self):
        layout = QVBoxLayout()
        
        self.graph = pg.PlotWidget()
        layout.addWidget(self.graph)
        
        self.num_values = 6  # Assuming 6 values from the IMU
        self.curves = []  # Store multiple lines for each value
        self.data_buffers = [[] for _ in range(self.num_values)]  # Moving window for each value
        self.max_points = 200  # ~20 seconds of data if sampling every 100ms

        colors = ['r', 'g', 'b', 'c', 'm', 'y']  # Different colors for each line
        for i in range(self.num_values):
            curve = self.graph.plot(pen=colors[i % len(colors)])
            self.curves.append(curve)
        
        self.data_tab.setLayout(layout)
    
    def initTestTab(self):
        layout = QVBoxLayout()
        
        self.test_label = QLabel("Select Joint for Mobility Test:")
        layout.addWidget(self.test_label)
        
        self.test_combobox = QComboBox()
        self.test_combobox.addItems(["Left Ankle", "Right Ankle", "Left Elbow", "Right Elbow"])
        self.test_combobox.currentIndexChanged.connect(self.load_test_page)
        layout.addWidget(self.test_combobox)
        
        self.test_info = QTextEdit()
        self.test_info.setReadOnly(True)
        layout.addWidget(self.test_info)
        
        self.start_test_button = QPushButton("Start 10s Test")
        self.start_test_button.clicked.connect(self.start_test)
        layout.addWidget(self.start_test_button)

        # Previous Results Section
        self.previous_results_label = QLabel("Previous Results:")
        layout.addWidget(self.previous_results_label)
        
        self.previous_results_text = QTextEdit()
        self.previous_results_text.setReadOnly(True)
        layout.addWidget(self.previous_results_text)
        
        # Highest Score Section
        self.highest_score_label = QLabel("Highest Score:")
        layout.addWidget(self.highest_score_label)
        
        self.highest_score_text = QLabel("No results yet")
        layout.addWidget(self.highest_score_text)
        
        self.test_tab.setLayout(layout)
        self.load_test_page()

    def load_test_page(self):
        joint = self.test_combobox.currentText()
        test_descriptions = {
            "Left Ankle": "This test measures the range of motion of the left ankle.",
            "Right Ankle": "This test measures the range of motion of the right ankle.",
            "Left Elbow": "This test measures the flexibility and strength of the left elbow.",
            "Right Elbow": "This test measures the flexibility and strength of the right elbow."
        }
        self.test_info.setText(test_descriptions.get(joint, "Select a test to see details."))
        self.update_previous_results()

    def update_previous_results(self):
        joint = self.test_combobox.currentText()
        results_for_joint = [result for result in self.test_results if result[0] == joint]
        
        if results_for_joint:
            # Display the results
            results_text = "\n".join([f"Date: {result[2]}, Max Differences: {result[1]}" for result in results_for_joint])
            self.previous_results_text.setText(results_text)
            
            # Calculate and display the highest score
            highest_score = max(
                results_for_joint,
                key=lambda result: sum(abs(value) for value in result[1]),
                default=None
            )
            if highest_score:
                self.highest_score_text.setText(f"Date: {highest_score[2]}, Max Differences: {highest_score[1]}")
            else:
                self.highest_score_text.setText("No results yet")
        else:
            self.previous_results_text.setText("No previous results")
            self.highest_score_text.setText("No results yet")

    def start_test(self):
        self.datum = None
        self.test_active = True
        self.test_start_time = QDateTime.currentDateTime().toSecsSinceEpoch()
        self.max_diff = [0] * self.num_values
        self.start_test_button.setEnabled(False)
        self.test_info.setText("Test in progress... Please move the joint.")

    def update_serial_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combobox.clear()
        self.port_combobox.addItems(ports)
    
    def connect_serial(self):
        port_name = self.port_combobox.currentText()
        try:
            self.serial_port = serial.Serial(port_name, 115200, timeout=0.01)
            self.serial_status.setText(f"Connected to {port_name}")
            self.timer.start(10)  # Faster updates (10ms interval)
        except Exception as e:
            self.serial_status.setText("Connection Failed")
            print("Error:", e)
    
    def read_serial_data(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                bytes_to_read = self.serial_port.in_waiting
                if bytes_to_read > 0:
                    raw_data = self.serial_port.read(bytes_to_read).decode('utf-8', errors='ignore')
                    lines = raw_data.strip().split('\n')
                    
                    for line in lines:
                        values = line.strip().split(',')
                        
                        if len(values) == self.num_values and all(v.replace('.', '', 1).replace('-', '', 1).isdigit() for v in values):
                            values = [round(float(v), 1) for v in values]  # Limit precision to 1 decimal place
                            
                            if self.test_active:
                                current_time = QDateTime.currentDateTime().toSecsSinceEpoch()
                                elapsed_time = current_time - self.test_start_time
                                
                                if self.datum is None:
                                    self.datum = values[:]
                                
                                diffs = [abs(values[i] - self.datum[i]) for i in range(self.num_values)]
                                self.max_diff = [max(self.max_diff[i], diffs[i]) for i in range(self.num_values)]
                                
                                if elapsed_time >= 10:
                                    self.test_results.append((self.test_combobox.currentText(), self.max_diff, QDateTime.currentDateTime().toString()))
                                    self.test_active = False
                                    self.start_test_button.setEnabled(True)
                                    self.test_info.setText(f"Test complete! Max differences: {self.max_diff}")
                            
                            for i in range(self.num_values):
                                self.data_buffers[i].append(values[i])
                                if len(self.data_buffers[i]) > self.max_points:
                                    self.data_buffers[i].pop(0)
                                self.curves[i].setData(self.data_buffers[i])
            
            except ValueError:
                print("Invalid data format:", raw_data)
    
    def load_test_results(self):
        try:
            with open('test_results.json', 'r') as file:
                self.test_results = json.load(file)
        except FileNotFoundError:
            self.test_results = []
    
    def save_test_results(self):
        with open('test_results.json', 'w') as file:
            json.dump(self.test_results, file)
        
    def closeEvent(self, event):
        # Save test results when the app is closed
        self.save_test_results()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IMUGUI()
    window.show()
    sys.exit(app.exec())
