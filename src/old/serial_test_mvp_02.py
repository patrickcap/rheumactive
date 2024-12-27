import serial.tools.list_ports
import logging
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import csv
import os
import random  # Replace with actual sensor data for testing

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

# Global Constants
TEST_TYPES = ['ankle', 'hip', 'elbow']
TOP_SCORES = {test: {'roll': [0, 0], 'pitch': [0, 0], 'yaw': [0, 0]} for test in TEST_TYPES}  # Format: {'roll': [min, max], 'pitch': [min, max], 'yaw': [min, max]}


class SerialMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Monitor GUI")

        # Tabs for test selection
        self.tab_control = ttk.Notebook(root)
        self.tabs = {}
        for test in TEST_TYPES:
            tab = ttk.Frame(self.tab_control)
            self.tab_control.add(tab, text=test.capitalize())
            self.tabs[test] = tab
            self.create_test_tab(tab, test)
        self.tab_control.pack(expand=1, fill="both")

        # Serial Connection
        self.serial_inst = None
        self.running = False

        # Store test data
        self.current_test = None
        self.start_time = None
        self.data = []

    def create_test_tab(self, tab, test_type):
        # Display top score
        ttk.Label(tab, text="Top Score", font=("Helvetica", 14)).pack(pady=5)

        self.top_score_vars = {axis: tk.StringVar(value=f"{axis.capitalize()}: Min=0, Max=0") for axis in ['roll', 'pitch', 'yaw']}
        for axis, var in self.top_score_vars.items():
            ttk.Label(tab, textvariable=var, font=("Helvetica", 12)).pack()

        # Start Test Button
        start_button = tk.Button(tab, text="Start Test", command=lambda: self.start_test(test_type))
        start_button.pack(pady=10)

    def start_test(self, test_type):
        self.current_test = test_type
        self.start_time = datetime.now()
        self.data = []
        logger.info(f"Starting {test_type} test")

        # Set the datum values (simulate with random data for now)
        self.datum = {'roll': random.uniform(-5, 5), 'pitch': random.uniform(-5, 5), 'yaw': random.uniform(-5, 5)}
        self.root.after(1000, self.record_data)  # Start data recording after 1 second

    def record_data(self):
        if len(self.data) < 150:  # Record data for 15 seconds (assuming ~10 Hz updates)
            # Simulate sensor data (replace with actual serial read)
            sensor_data = {
                'roll': self.datum['roll'] + random.uniform(-10, 10),
                'pitch': self.datum['pitch'] + random.uniform(-10, 10),
                'yaw': self.datum['yaw'] + random.uniform(-10, 10)
            }
            self.data.append(sensor_data)

            # Update top scores
            for axis in ['roll', 'pitch', 'yaw']:
                TOP_SCORES[self.current_test][axis][0] = min(TOP_SCORES[self.current_test][axis][0], sensor_data[axis])
                TOP_SCORES[self.current_test][axis][1] = max(TOP_SCORES[self.current_test][axis][1], sensor_data[axis])
                self.top_score_vars[axis].set(f"{axis.capitalize()}: Min={TOP_SCORES[self.current_test][axis][0]:.2f}, Max={TOP_SCORES[self.current_test][axis][1]:.2f}")

            self.root.after(100, self.record_data)  # Record data every 100ms
        else:
            self.save_data()

    def save_data(self):
        # Save recorded data to a CSV file
        timestamp = self.start_time.strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"{self.current_test}_test_{timestamp}.csv"

        with open(filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['timestamp', 'roll', 'pitch', 'yaw'])
            writer.writeheader()
            for entry in self.data:
                writer.writerow({'timestamp': self.start_time.strftime('%Y-%m-%d %H:%M:%S'), **entry})

        logger.info(f"Saved test data to {filename}")
        tk.messagebox.showinfo("Test Complete", f"{self.current_test.capitalize()} test completed. Data saved to {filename}")

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
