import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import random
import serial.tools.list_ports


class MobilityTestApp:
    TEST_TYPES = ["Ankle Left", "Ankle Right"]

    def __init__(self, root):
        self.root = root
        self.root.title("RheumActive")
        
        self.current_test = None
        self.data = []
        self.datum = {"roll": 0, "pitch": 0, "yaw": 0}

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






    # Function to connect to the selected COM port
    def connect_to_port(self, selected_port, baud_rate=9600):
        if selected_port.startswith('COM'):
            selected_port = selected_port.split(' ')[0]

        serial_inst = serial.Serial()
        serial_inst.baudrate = baud_rate
        serial_inst.port = selected_port
        serial_inst.open()
        return serial_inst

































    def read_serial_data(self):
        if self.serial_inst and self.serial_inst.in_waiting:
            try:
                packet = self.serial_inst.readline().decode('utf-8').strip()
                self.previous_results_label.config(text=packet)
            except Exception as e:
                self.previous_results_label.config(text="Error reading data")
        if self.running:
            self.root.after(100, self.read_serial_data)  # Schedule next read in 100 ms





    def create_connectivity_tab(self):
        # Connectivity tab GUI
        label = tk.Label(self.connectivity_tab, text="Select COM Port:")
        label.pack(pady=10)

        self.port_var = tk.StringVar()
        self.port_dropdown = ttk.Combobox(self.connectivity_tab, textvariable=self.port_var)
        self.port_dropdown['values'] = ["COM3", "COM4", "COM5"]  # Example COM ports
        self.port_dropdown.pack(pady=5)


        try:
            selected_port = self.port_var.get()
            if not selected_port:
                raise ValueError("No port selected")

            self.serial_inst = self.connect_to_port(selected_port)
            self.running = True
            self.read_serial_data()
        except Exception as e:
            self.previous_results_label.config(text="Error: Could not connect to port")



        connect_button = tk.Button(self.connectivity_tab, text="Connect", command=self.connect_to_serial)
        connect_button.pack(pady=10)

















    def create_test_tab(self, tab, test_type):
        # Previous results display
        self.previous_results_label = tk.Label(tab, text="", font=("Helvetica", 12), wraplength=400, justify="left")
        self.previous_results_label.pack(pady=20)
        self.display_previous_results(test_type)

        # Start test button
        start_button = tk.Button(tab, text="Start New 5s Test", command=lambda: self.start_test(test_type))
        start_button.pack(pady=10)

    def connect_to_serial(self):
        selected_port = self.port_var.get()
        if not selected_port:
            messagebox.showerror("Error", "No COM port selected!")
            return
        # Simulate a successful connection
        messagebox.showinfo("Success", f"Connected to {selected_port}")

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

if __name__ == "__main__":
    root = tk.Tk()
    app = MobilityTestApp(root)
    root.mainloop()
