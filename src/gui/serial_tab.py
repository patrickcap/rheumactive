from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtCore import QTimer
from utils.serial_utils import list_serial_ports, connect_serial_port

class SerialTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.main_window = parent
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial_data)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.port_label = QLabel("Select Serial Port:")
        layout.addWidget(self.port_label)

        self.port_combobox = QComboBox()
        self.update_serial_ports()
        layout.addWidget(self.port_combobox)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_button_clicked)
        layout.addWidget(self.connect_button)

        self.serial_status = QLabel("Status: Not Connected")
        layout.addWidget(self.serial_status)

        self.setLayout(layout)

    def update_serial_ports(self):
        ports = list_serial_ports()
        self.port_combobox.clear()
        self.port_combobox.addItems(ports)

    def connect_button_clicked(self):
        port_name = self.port_combobox.currentText()
        serial_port = connect_serial_port(port_name, 115200)
        if serial_port:
            self.main_window.serial_port = serial_port
            self.serial_status.setText(f"Connected to {port_name}")
            self.timer.start(10)  # Faster updates (10ms interval)
        else:
            self.main_window.serial_port = None
            self.serial_status.setText("Connection Failed")

    def read_serial_data(self):
        if self.main_window.serial_port and self.main_window.serial_port.is_open:
            try:
                bytes_to_read = self.main_window.serial_port.in_waiting
                if bytes_to_read > 0:
                    raw_data = self.main_window.serial_port.read(bytes_to_read).decode('utf-8', errors='ignore')
                    lines = raw_data.strip().split('\n')

                    for line in lines:
                        values = line.strip().split(',')

                        if len(values) == self.main_window.data_tab_widget.num_values and all(v.replace('.', '', 1).replace('-', '', 1).isdigit() for v in values):
                            values = [round(float(v), 1) for v in values]  # Limit precision to 1 decimal place

                            if self.main_window.test_tab_widget.test_active:
                                self.main_window.test_tab_widget.process_test_data(values)

                            self.main_window.data_tab_widget.update_plot(values)

            except ValueError:
                print("Invalid data format:", raw_data)