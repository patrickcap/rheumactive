import serial.tools.list_ports
import serial
import logging
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import csv
import threading
import time

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
def connect_to_port(selected_port, baud_rate=115200):
    if selected_port.startswith('COM'):
        selected_port = selected_port.split(' ')[0]

    serial_inst = serial.Serial()
    serial_inst.baudrate = baud_rate
    serial_inst.port = selected_port
    serial_inst.timeout = 1
    serial_inst.open()
    return serial_inst

# GUI application
class SerialMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Joint Mobility Test")

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

        # Test type selection
        self.test_label = tk.Label(root, text="Select Test Type:")
        self.test_label.pack()

        self.test_var = tk.StringVar(value="Select a test")
        self.test_dropdown = ttk.Combobox(root, textvariable=self.test_var, values=["ankle", "hip", "elbow"])
        self.test_dropdown.pack()

        # Start Test button
        self.start_test_button = tk.Button(root, text="Start Test", command=self.start_test, state=tk.DISABLED)
        self.start_test_button.pack(pady=10)

        # Results display
        self.results_label = tk.Label(root, text="Results:", font=("Helvetica", 14))
        self.results_label.pack(pady=10)

        self.results_var = tk.StringVar(value="No test completed yet")
        self.results_display = tk.Label(root, textvariable=self.results_var, font=("Helvetica", 12))
        self.results_display.pack()

        # Initialize serial instance and other variables
        self.serial_inst = None
        self.running = False
        self.calibration_data = {'roll1': 0, 'pitch1': 0, 'yaw1': 0, 'roll2': 0, 'pitch2': 0, 'yaw2': 0}
        self.recorded_data = []
        self.high_scores = {'roll': (0, 0), 'pitch': (0, 0), 'yaw': (0, 0)}  # Max positive and negative

    def connect_to_serial(self):
        try:
            selected_port = self.port_var.get()
            if not selected_port:
                raise ValueError("No port selected")

            self.serial_inst = connect_to_port(selected_port)
            logger.info(f"Connected to {selected_port}.")
            self.start_test_button.config(state=tk.NORMAL)
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.results_var.set("Error: Could not connect to port")

    def start_test(self):
        test_type = self.test_var.get()
        if test_type not in ["ankle", "hip", "elbow"]:
            self.results_var.set("Error: Invalid test type selected")
            return

        self.recorded_data = []
        self.results_var.set("Calibrating...")
        self.calibrate_sensors()
        self.results_var.set(f"Running {test_type} test...")

        threading.Thread(target=self.run_test, daemon=True).start()

    def calibrate_sensors(self):
        # Read initial sensor values and set as calibration data
        try:
            if self.serial_inst and self.serial_inst.in_waiting:
                line = self.serial_inst.readline().decode('utf-8').strip()
                roll1, pitch1, yaw1, roll2, pitch2, yaw2 = map(float, line.split(','))
                self.calibration_data = {
                    'roll1': roll1, 'pitch1': pitch1, 'yaw1': yaw1,
                    'roll2': roll2, 'pitch2': pitch2, 'yaw2': yaw2
                }
                logger.info("Calibration complete.")
        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            self.results_var.set("Error during calibration")

    def run_test(self):
        try:
            start_time = time.time()
            while time.time() - start_time < 15:
                if self.serial_inst and self.serial_inst.in_waiting:
                    line = self.serial_inst.readline().decode('utf-8').strip()
                    roll1, pitch1, yaw1, roll2, pitch2, yaw2 = map(float, line.split(','))
                    roll_avg = (roll1 - self.calibration_data['roll1'] + roll2 - self.calibration_data['roll2']) / 2
                    pitch_avg = (pitch1 - self.calibration_data['pitch1'] + pitch2 - self.calibration_data['pitch2']) / 2
                    yaw_avg = (yaw1 - self.calibration_data['yaw1'] + yaw2 - self.calibration_data['yaw2']) / 2
                    self.recorded_data.append({'roll': roll_avg, 'pitch': pitch_avg, 'yaw': yaw_avg})

                    # Update high scores
                    self.update_high_scores(roll_avg, pitch_avg, yaw_avg)

            self.save_data_to_csv()
            self.display_results()
        except Exception as e:
            logger.error(f"Test failed: {e}")
            self.results_var.set("Error during test")

    def update_high_scores(self, roll, pitch, yaw):
        self.high_scores['roll'] = (max(self.high_scores['roll'][0], roll), min(self.high_scores['roll'][1], roll))
        self.high_scores['pitch'] = (max(self.high_scores['pitch'][0], pitch), min(self.high_scores['pitch'][1], pitch))
        self.high_scores['yaw'] = (max(self.high_scores['yaw'][0], yaw), min(self.high_scores['yaw'][1], yaw))

    def save_data_to_csv(self):
        filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['roll', 'pitch', 'yaw'])
            writer.writeheader()
            writer.writerows(self.recorded_data)
        logger.info(f"Data saved to {filename}")

    def display_results(self):
        high_scores = self.high_scores
        results_text = (
            f"Roll: Max={high_scores['roll'][0]:.2f}, Min={high_scores['roll'][1]:.2f}\n"
            f"Pitch: Max={high_scores['pitch'][0]:.2f}, Min={high_scores['pitch'][1]:.2f}\n"
            f"Yaw: Max={high_scores['yaw'][0]:.2f}, Min={high_scores['yaw'][1]:.2f}"
        )
        self.results_var.set(results_text)

    def on_close(self):
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
