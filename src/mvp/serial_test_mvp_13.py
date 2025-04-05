import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QTabWidget
)
from PyQt6.QtCore import QTimer
import pyqtgraph as pg

class IMUGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IMU Data Collection")
        self.setGeometry(100, 100, 800, 600)

        self.serial_port = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial_data)
        
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
                            values = [float(v) for v in values]
                            
                            # Update data buffers
                            for i in range(self.num_values):
                                self.data_buffers[i].append(values[i])
                                if len(self.data_buffers[i]) > self.max_points:
                                    self.data_buffers[i].pop(0)  # Remove oldest data
                                self.curves[i].setData(self.data_buffers[i])
            
            except ValueError:
                print("Invalid data format:", raw_data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IMUGUI()
    window.show()
    sys.exit(app.exec())
