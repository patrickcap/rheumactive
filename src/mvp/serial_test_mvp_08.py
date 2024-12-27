import os
import csv
import serial
import serial.tools.list_ports
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import random

# Configure logging
current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_filename = f'serial_test_gui_{current_datetime}.log'

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.info('+++ Launched mobility_test_gui.py')


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


class MobilityTestApp:
    TEST_TYPES = ["Ankle Left", "Ankle Right"]

    def __init__(self, root):
        self.root = root
        self.root.title("RheumActive")

        self.current_test = None
        self.data = []
        self.datum = {"roll": 0, "pitch": 0, "yaw": 0}
        self.serial_inst = None
        self.running = False

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.connectivity_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.connectivity_tab, text="Connectivity")
        self.create_connectivity_tab()

        self.test_tabs = {}
        for test_type in self.TEST_TYPES:
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=test_type)
            self.test_tabs[test_type] = tab
            self.create_test_tab(tab, test_type)

    def create_connectivity_tab(self):
        # Connectivity tab GUI
        label = tk.Label(self.connectivity_tab, text="Select COM Port:")
        label.pack(pady=10)

        self.port_var = tk.StringVar()
        self.port_dropdown = ttk.Combobox(self.connectivity_tab, textvariable=self.port_var)
        self.port_dropdown['values'] = find_com_ports()
        self.port_dropdown.pack(pady=5)

        connect_button = tk.Button(self.connectivity_tab, text="Connect", command=self.connect_to_serial)
        connect_button.pack(pady=10)

        self.data_label = tk.Label(self.connectivity_tab, text="Latest Data:", font=("Helvetica", 14))
        self.data_label.pack(pady=10)

        self.data_var = tk.StringVar(value="No data yet")
        self.data_display = tk.Label(self.connectivity_tab, textvariable=self.data_var, font=("Helvetica", 12))
        self.data_display.pack()

    def create_test_tab(self, tab, test_type):
        # Previous results display
        self.previous_results_label = tk.Label(tab, text="", font=("Helvetica", 12), wraplength=400, justify="left")
        self.previous_results_label.pack(pady=20)
        self.display_previous_results(test_type)

        # Start test button
        start_button = tk.Button(tab, text="Start New 5s Test", command=lambda: self.start_test(test_type))
        start_button.pack(pady=10)

    def connect_to_serial(self):
        try:
            selected_port = self.port_var.get()
            if not selected_port:
                raise ValueError("No port selected")

            self.serial_inst = connect_to_port(selected_port)
            logger.info(f"Connected to {selected_port}.")
            self.running = True
            self.start_reading()
            messagebox.showinfo("Success", f"Connected to {selected_port}")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.data_var.set("Error: Could not connect to port")
            messagebox.showerror("Error", f"Failed to connect to {selected_port}: {e}")

    def start_reading(self):
        self.read_serial_data()

    def read_serial_data(self):
        if self.serial_inst and self.serial_inst.in_waiting:
            try:
                packet = self.serial_inst.readline().decode('utf-8').strip()
                # Split the data into a list of floats
                data_list = [float(value) for value in packet.split(",")]

                # Calculate averages
                pitch = (data_list[0] + data_list[3]) / 2
                roll = (data_list[1] + data_list[4]) / 2
                yaw = (data_list[2] + data_list[5]) / 2

                # Limit decimal places to 1
                pitch = round(pitch, 1)
                roll = round(roll, 1)
                yaw = round(yaw, 1)

                # Create a dictionary with average values
                labeled_data = {
                    "pitch": pitch,
                    "roll": roll,
                    "yaw": yaw,
                }

                # Log the labeled data
                logger.info(labeled_data)
                self.data_var.set(labeled_data)

            except Exception as e:
                logger.error(f"Error reading data: {e}")
                self.data_var.set("Error reading data")
                
        if self.running:
            self.root.after(100, self.read_serial_data)  # Schedule next read in 100 ms

    def display_previous_results(self, test_type):
        file_name = f"previous_results_{test_type.replace(' ', '_').lower()}.csv"
        if not os.path.exists(file_name):
            self.previous_results_label.config(
                text=f"No previous results for {test_type}. Start a new test to record data."
            )
            return

        # Read the last row of the file
        with open(file_name, mode="r") as file:
            reader = list(csv.DictReader(file))
            if reader:
                last_result = reader[-1]
                self.previous_results_label.config(
                    text=f"Your previous test for {test_type} was on {last_result['datetime']} "
                         f"with the following scores:\n"
                         f"Roll: {last_result['roll']}°\n"
                         f"Pitch: {last_result['pitch']}°\n"
                         f"Yaw: {last_result['yaw']}°"
                )
            else:
                self.previous_results_label.config(
                    text=f"No previous results for {test_type}. Start a new test to record data."
                )

    def start_test(self, test_type):
        self.current_test = test_type
        self.data = []
        self.datum = {"roll": random.uniform(-5, 5), "pitch": random.uniform(-5, 5), "yaw": random.uniform(-5, 5)}

        messagebox.showinfo("Test Started", f"Starting 5-second {test_type} test.")
        self.root.after(100, self.record_data, 0)

    def record_data(self, count):
        if count >= 50:  # 5 seconds at 100ms intervals
            self.save_test_results()
            return

        # Simulated data
        roll = self.datum["roll"] + random.uniform(-10, 10)
        pitch = self.datum["pitch"] + random.uniform(-10, 10)
        yaw = self.datum["yaw"] + random.uniform(-10, 10)

        self.data.append({"roll": roll, "pitch": pitch, "yaw": yaw})
        self.root.after(100, self.record_data, count + 1)

    def save_test_results(self):
        file_name = f"previous_results_{self.current_test.replace(' ', '_').lower()}.csv"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate max absolute differences
        roll_diff = max(self.data, key=lambda x: abs(x["roll"]))["roll"]
        pitch_diff = max(self.data, key=lambda x: abs(x["pitch"]))["pitch"]
        yaw_diff = max(self.data, key=lambda x: abs(x["yaw"]))["yaw"]

        # Append results to file
        is_new_file = not os.path.exists(file_name)
        with open(file_name, mode="a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["datetime", "roll", "pitch", "yaw"])
            if is_new_file:
                writer.writeheader()
            writer.writerow({
                "datetime": now,
                "roll": roll_diff,
                "pitch": pitch_diff,
                "yaw": yaw_diff
            })

        # Update previous results
        self.display_previous_results(self.current_test)
        messagebox.showinfo("Test Complete", f"{self.current_test} test complete. Data saved to {file_name}.")

    def on_close(self):
        self.running = False
        if self.serial_inst and self.serial_inst.is_open:
            self.serial_inst.close()
        logger.info("--- Exiting mobility_test_gui.py")
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MobilityTestApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
