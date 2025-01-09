import os
import csv
import serial
import serial.tools.list_ports
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

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

        self.highest_scores = {test_type: {"roll": 0, "pitch": 0, "yaw": 0, "datetime": "None"} for test_type in self.TEST_TYPES}

        # Read highest scores from CSV files
        self.initialize_highest_scores()

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

    def initialize_highest_scores(self):
        for test_type in self.TEST_TYPES:
            file_name = f"previous_results_{test_type.replace(' ', '_').lower()}.csv"
            if not os.path.exists(file_name):
                continue

            try:
                with open(file_name, mode="r") as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        roll = abs(float(row["roll"]))
                        pitch = abs(float(row["pitch"]))
                        yaw = abs(float(row["yaw"]))

                        # Check if this row is the highest score
                        current_total = roll + pitch + yaw
                        stored_total = sum(abs(self.highest_scores[test_type][axis]) for axis in ["roll", "pitch", "yaw"])

                        if current_total > stored_total:
                            self.highest_scores[test_type] = {
                                "roll": roll,
                                "pitch": pitch,
                                "yaw": yaw,
                                "datetime": row["datetime"]
                            }
            except Exception as e:
                logger.error(f"Error reading highest scores from {file_name}: {e}")


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

        # Highest score display
        self.highest_score_label = tk.Label(tab, text="", font=("Helvetica", 12))
        self.highest_score_label.pack(pady=10)
        self.update_highest_score_display(test_type)


    def connect_to_serial(self):
        try:
            selected_port = self.port_var.get()
            if not selected_port:
                raise ValueError("No port selected")

            self.serial_inst = connect_to_port(selected_port)
            logger.info(f"Connected to {selected_port}.")
            self.running = True
            self.read_serial_data()
            messagebox.showinfo("Success", f"Connected to {selected_port}")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.data_var.set("Error: Could not connect to port")
            messagebox.showerror("Error", f"Failed to connect to {selected_port}: {e}")

    def read_serial_data(self):
        if self.serial_inst:
            try:
                # Flush only if there is excessive data waiting
                if self.serial_inst.in_waiting > 1024:  # Arbitrary threshold for buffer overflow
                    logger.warning("Serial buffer overflow detected. Resetting input buffer.")
                    self.serial_inst.reset_input_buffer()

                # Read a line from the serial buffer
                packet = self.serial_inst.readline().decode('utf-8').strip()

                # Skip processing if the packet is empty
                if not packet:
                    logger.warning("Received empty line from serial.")

                # Split the data into a list of floats
                data_list = packet.split(",")
                if len(data_list) < 6:  # Ensure there are enough values
                    logger.warning(f"Malformed data received: {packet}")

                # Convert to floats
                data_list = [float(value) for value in data_list]

                # Calculate averages and round to one decimal place
                roll = round((data_list[0] + data_list[3]) / 2, 1)
                pitch = round((data_list[1] + data_list[4]) / 2, 1)
                yaw = round((data_list[2] + data_list[5]) / 2, 1)

                # Create a labeled dictionary
                labeled_data = f"Pitch: {pitch}°, Roll: {roll}°, Yaw: {yaw}°"
                logger.info(f"Processed data: {labeled_data}")
                self.data_var.set(labeled_data)

            except ValueError as ve:
                logger.error(f"Error converting data to float: {ve}")
                self.data_var.set("Error: Malformed data")

            except IndexError as ie:
                logger.error(f"Error processing data: {ie}")
                self.data_var.set("Error: Incomplete data")

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.data_var.set("Error reading data")

        if self.running:
            self.root.after(100, self.read_serial_data)

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
        
        # Use current readings as the datum
        if self.serial_inst and self.serial_inst.in_waiting:
            try:
                packet = self.serial_inst.readline().decode('utf-8').strip()
                data_list = [float(value) for value in packet.split(",")]

                roll = round((data_list[0] + data_list[3]) / 2, 1)
                pitch = round((data_list[1] + data_list[4]) / 2, 1)
                yaw = round((data_list[2] + data_list[5]) / 2, 1)

                self.datum = {"roll": roll, "pitch": pitch, "yaw": yaw}
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize datum: {e}")
                return
        else:
            messagebox.showerror("Error", "No serial data available for initializing datum.")
            return

        messagebox.showinfo("Test Started", f"Starting 5-second {test_type} test.")
        self.root.after(100, self.record_data, 0)

    def record_data(self, count):
        if count >= 50:  # 5 seconds at 100ms intervals
            self.save_test_results()
            return

        if self.serial_inst and self.serial_inst.in_waiting:
            try:
                # Read current serial data
                packet = self.serial_inst.readline().decode('utf-8').strip()
                data_list = [float(value) for value in packet.split(",")]

                roll = (data_list[0] + data_list[3]) / 2
                pitch = (data_list[1] + data_list[4]) / 2
                yaw = (data_list[2] + data_list[5]) / 2

                # Calculate differences from the datum
                roll_diff = abs(round(roll - self.datum["roll"], 1))
                pitch_diff = abs(round(pitch - self.datum["pitch"], 1))
                yaw_diff = abs(round(yaw - self.datum["yaw"], 1))

                logger.info(f"RollDatum={self.datum['roll']}, PitchDiff={self.datum['pitch']}, YawDiff={self.datum['yaw']}, Roll1={data_list[0]}, Pitch1={data_list[1]}, Yaw1={data_list[2]}, Roll2={data_list[3]}, Pitch2={data_list[4]}, Yaw2={data_list[5]}, PitchDiff={pitch_diff}, RollDiff={roll_diff}, YawDiff={yaw_diff}")

                # Append differences to the data list
                self.data.append({"roll": roll_diff, "pitch": pitch_diff, "yaw": yaw_diff})

            except Exception as e:
                logger.error(f"Error reading serial data during test: {e}")

        self.root.after(100, self.record_data, count + 1)

    def save_test_results(self):
        file_name = f"previous_results_{self.current_test.replace(' ', '_').lower()}.csv"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate maximum values for roll, pitch, and yaw
        roll_max = max(self.data, key=lambda x: abs(x["roll"]))["roll"]
        pitch_max = max(self.data, key=lambda x: abs(x["pitch"]))["pitch"]
        yaw_max = max(self.data, key=lambda x: abs(x["yaw"]))["yaw"]

        # Check if this test has the highest score
        current_max_total = abs(roll_max) + abs(pitch_max) + abs(yaw_max)
        stored_max_total = sum(abs(self.highest_scores[self.current_test][axis]) for axis in ["roll", "pitch", "yaw"])

        if current_max_total > stored_max_total:
            self.highest_scores[self.current_test] = {
                "roll": roll_max,
                "pitch": pitch_max,
                "yaw": yaw_max,
                "datetime": now
            }
            self.update_highest_score_display(self.current_test)

        # Append results to file
        is_new_file = not os.path.exists(file_name)
        with open(file_name, mode="a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["datetime", "roll", "pitch", "yaw"])
            if is_new_file:
                writer.writeheader()
            writer.writerow({
                "datetime": now,
                "roll": roll_max,
                "pitch": pitch_max,
                "yaw": yaw_max
            })

        # Update previous results
        self.display_previous_results(self.current_test)
        messagebox.showinfo("Test Complete", f"{self.current_test} test complete. Data saved to {file_name}.")

    def update_highest_score_display(self, test_type):
        highest = self.highest_scores[test_type]
        self.highest_score_label.config(
            text=f"Highest Score:\n"
                f"Date: {highest['datetime']}\n"
                f"Roll: {highest['roll']}°\n"
                f"Pitch: {highest['pitch']}°\n"
                f"Yaw: {highest['yaw']}°"
        )

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
