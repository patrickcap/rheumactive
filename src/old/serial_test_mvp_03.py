import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import csv
import os
import random  # Replace with actual serial data for testing

# Global constants for test types and storing high scores
TEST_TYPES = ['Ankle Left', 'Ankle Right', 'Hip Left', 'Hip Right']
PREVIOUS_RESULTS = {test: {'date': 'N/A', 'scores': {'roll': 0, 'pitch': 0, 'yaw': 0}} for test in TEST_TYPES}

# Function to find available COM ports
def find_com_ports():
    ports = serial.tools.list_ports.comports()
    return [str(port) for port in ports]

# GUI Application
class MobilityTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title('RheumActive')

        # Create notebook (tabs)
        self.tab_control = ttk.Notebook(root)
        self.tabs = {}

        # Connectivity tab
        self.create_connectivity_tab()

        # Test tabs for TEST_TYPES
        for test in TEST_TYPES:
            self.create_test_tab(test)

        self.tab_control.pack(expand=1, fill='both')

        # Initialize serial connection
        self.serial_inst = None
        self.running = False
        self.current_test = None
        self.start_time = None
        self.data = []

    def create_connectivity_tab(self):
        tab = ttk.Frame(self.tab_control)
        self.tab_control.add(tab, text='Connectivity')

        # Dropdown for COM port selection
        ttk.Label(tab, text='Select COM Port:').pack(pady=5)
        self.port_var = tk.StringVar()
        self.port_dropdown = ttk.Combobox(tab, textvariable=self.port_var)
        self.port_dropdown['values'] = find_com_ports()
        self.port_dropdown.pack(pady=5)

        # Connect button
        connect_button = tk.Button(tab, text='Connect', command=self.connect_to_serial)
        connect_button.pack(pady=10)

        self.tabs['Connectivity'] = tab

    def create_test_tab(self, test_type):
        tab = ttk.Frame(self.tab_control)
        self.tab_control.add(tab, text=test_type)

        # Previous test result
        self.previous_result_var = tk.StringVar()
        self.previous_result_var.set(
            f"Your previous test for {test_type} was on {PREVIOUS_RESULTS[test_type]['date']} "
            f'and had the following scores: '
            f"roll: {PREVIOUS_RESULTS[test_type]['scores']['roll']}°, "
            f"pitch: {PREVIOUS_RESULTS[test_type]['scores']['pitch']}°, "
            f"yaw: {PREVIOUS_RESULTS[test_type]['scores']['yaw']}°."
        )
        ttk.Label(tab, textvariable=self.previous_result_var, wraplength=400).pack(pady=10)

        # Start new test button
        start_button = tk.Button(tab, text='Start New 15s Test', command=lambda: self.start_new_test(test_type))
        start_button.pack(pady=10)

        self.tabs[test_type] = tab

    def connect_to_serial(self):
        try:
            selected_port = self.port_var.get()
            if not selected_port:
                raise ValueError('No port selected')

            self.serial_inst = serial.Serial(port=selected_port.split(' ')[0], baudrate=9600)
            messagebox.showinfo('Connection Success', f'Connected to {selected_port}.')
        except Exception as e:
            messagebox.showerror('Connection Failed', str(e))

    def start_new_test(self, test_type):
        if not self.serial_inst:
            messagebox.showerror('Error', 'Please connect to a COM port first.')
            return

        self.current_test = test_type
        self.start_time = datetime.now()
        self.data = []

        # Set datum (simulated here, replace with actual sensor calibration)
        self.datum = {'roll': random.uniform(-5, 5),
                      'pitch': random.uniform(-5, 5),
                      'yaw': random.uniform(-5, 5)}

        messagebox.showinfo('Test Started', f'{test_type} test will run for 15 seconds.')
        self.root.after(1000, self.record_data)

    def record_data(self):
        if len(self.data) < 150:  # Record data for 15 seconds at ~10 Hz
            # Simulate sensor data (replace with actual serial read)
            sensor_data = {
                'roll': self.datum['roll'] + random.uniform(-10, 10),
                'pitch': self.datum['pitch'] + random.uniform(-10, 10),
                'yaw': self.datum['yaw'] + random.uniform(-10, 10)
            }
            self.data.append(sensor_data)
            self.root.after(100, self.record_data)  # Continue recording
        else:
            self.save_test_results()

    def save_test_results(self):
        # Save data to CSV
        timestamp = self.start_time.strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'{self.current_test}_{timestamp}.csv'
        with open(filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['timestamp', 'roll', 'pitch', 'yaw'])
            writer.writeheader()
            for entry in self.data:
                writer.writerow({'timestamp': self.start_time.strftime('%Y-%m-%d %H:%M:%S'), **entry})

        # Calculate highest absolute differences
        results = {'roll': 0, 'pitch': 0, 'yaw': 0}
        for axis in results.keys():
            values = [entry[axis] for entry in self.data]
            results[axis] = max(values) - min(values)

        # Update previous results
        PREVIOUS_RESULTS[self.current_test]['date'] = self.start_time.strftime('%d %b %Y')
        PREVIOUS_RESULTS[self.current_test]['scores'] = results

        # Update GUI text
        self.previous_result_var.set(
            f"Your previous test for {self.current_test} was on {PREVIOUS_RESULTS[self.current_test]['date']} "
            f'and had the following scores: '
            f"roll: {results['roll']:.2f}°, pitch: {results['pitch']:.2f}°, yaw: {results['yaw']:.2f}°."
        )

        messagebox.showinfo('Test Complete', f'{self.current_test} test completed. Data saved to {filename}.')

    def on_close(self):
        if self.serial_inst and self.serial_inst.is_open:
            self.serial_inst.close()
        self.root.destroy()


# Main Execution
if __name__ == '__main__':
    root = tk.Tk()
    app = MobilityTestApp(root)
    root.protocol('WM_DELETE_WINDOW', app.on_close)
    root.mainloop()
