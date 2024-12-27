import serial.tools.list_ports
import logging
import tkinter as tk
from tkinter import ttk
from datetime import datetime

# Configure logging
current_date = datetime.now().strftime('%Y-%m-%d')
log_filename = f'serial_test_gui_{current_date}.log'

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.info('+++ Launched serial_test_gui.py')

# Function to find available COM ports
def find_com_ports():
    ports = serial.tools.list_ports.comports()
    port_list = [str(port) for port in ports]
    return port_list

# Function to connect to the selected COM port
def connect_to_port(selected_port, baud_rate=9600):
    if selected_port.startswith('COM'):
        selected_port = selected_port.split(' ')[0]

    serial_inst = serial.Serial()
    serial_inst.baudrate = baud_rate
    serial_inst.port = selected_port
    serial_inst.open()
    return serial_inst

# GUI application
class SerialMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Monitor GUI")

        # Dropdown for selecting COM port
        self.port_label = tk.Label(root, text="Select COM Port:")
        self.port_label.pack()

        self.port_var = tk.StringVar()
        self.port_dropdown = ttk.Combobox(root, textvariable=self.port_var)
        self.port_dropdown['values'] = find_com_ports()
        self.port_dropdown.pack()

        # Connect button
        self.connect_button = tk.Button(root, text="Connect", command=self.connect_to_serial)
        self.connect_button.pack()

        # Display for latest readings
        self.data_label = tk.Label(root, text="Latest Data:", font=("Helvetica", 14))
        self.data_label.pack(pady=10)

        self.data_var = tk.StringVar(value="No data yet")
        self.data_display = tk.Label(root, textvariable=self.data_var, font=("Helvetica", 12))
        self.data_display.pack()

        # Initialize serial instance
        self.serial_inst = None
        self.running = False

    def connect_to_serial(self):
        try:
            selected_port = self.port_var.get()
            if not selected_port:
                raise ValueError("No port selected")

            self.serial_inst = connect_to_port(selected_port)
            logger.info(f"Connected to {selected_port}.")
            self.running = True
            self.start_reading()
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.data_var.set("Error: Could not connect to port")

    def start_reading(self):
        self.read_serial_data()

    def read_serial_data(self):
        if self.serial_inst and self.serial_inst.in_waiting:
            try:
                packet = self.serial_inst.readline().decode('utf-8').strip()
                self.data_var.set(packet)
                logger.info(packet)
            except Exception as e:
                logger.error(f"Error reading data: {e}")
                self.data_var.set("Error reading data")
        if self.running:
            self.root.after(100, self.read_serial_data)  # Schedule next read in 100 ms

    def on_close(self):
        self.running = False
        if self.serial_inst and self.serial_inst.is_open:
            self.serial_inst.close()
        logger.info("--- Exiting serial_test_gui.py")
        self.root.destroy()

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = SerialMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
