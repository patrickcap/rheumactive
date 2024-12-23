import serial
import threading
import customtkinter as ctk

# Bluetooth Configuration
BLUETOOTH_PORT = 'COM4'  # Replace with your Bluetooth COM port
BAUD_RATE = 115200

# Global variable to store sensor data
sensor_data = "Waiting for data..."

# Function to read data from Bluetooth
def read_bluetooth_data():
    global sensor_data
    try:
        with serial.Serial(BLUETOOTH_PORT, BAUD_RATE, timeout=1) as bt:
            while True:
                if bt.in_waiting:
                    sensor_data = bt.readline().decode('utf-8').strip()
    except Exception as e:
        sensor_data = f"Error: {e}"

# GUI Setup
def create_gui():
    def update_label():
        label.configure(text=sensor_data)
        root.after(100, update_label)

    root = ctk.CTk()
    root.title("RheumActive Data")
    root.geometry("500x300")

    label = ctk.CTkLabel(root, text=sensor_data, font=("Arial", 14))
    label.pack(pady=20)

    update_label()
    root.mainloop()

# Start Bluetooth Thread
bluetooth_thread = threading.Thread(target=read_bluetooth_data, daemon=True)
bluetooth_thread.start()

# Start GUI
create_gui()
