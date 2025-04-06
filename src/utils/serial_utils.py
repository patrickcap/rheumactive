import serial
import serial.tools.list_ports

def list_serial_ports():
    """Lists available serial ports."""
    ports = [port.device for port in serial.tools.list_ports.comports()]
    return ports

def connect_serial_port(port_name, baudrate):
    """Connects to a serial port."""
    try:
        ser = serial.Serial(port_name, baudrate, timeout=0.01)
        return ser
    except Exception as e:
        print(f"Error connecting to {port_name}: {e}")
        return None