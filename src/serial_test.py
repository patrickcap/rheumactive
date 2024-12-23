import serial.tools.list_ports
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='serial_test.log', level=logging.INFO)
logger.info('+++ Launched serial_test.py')

ports = serial.tools.list_ports.comports()
serial_inst = serial.Serial()

port_list = []

for one_port in ports:
    port_list.append(str(one_port))
    logger.info(str(one_port))

val = input('Select Port: COM')

for port in port_list:
    port_var = 'COM' + str(val)
    if port.startswith('COM' + str(val)):
        logger.info(f'Found {port_var}.')
    else:
        raise NameError(f'Could not find the port {port_var}.')

serial_inst.baudrate = 9600
serial_inst.port = port_var
serial_inst.open()

logger.info(f'Found {port_var} and now listening...')
while True:
    # If data is in the buffer, want to read that data in
    if serial_inst.in_waiting:
        packet = serial_inst.readline()
        logger.info(packet.decode('utf'))



logger.info('--- Landed serial_test.py')
