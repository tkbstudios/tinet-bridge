import serial
from serial.tools import list_ports
import socket
import sys
import time
import urllib.request
import threading
import math
import os
LATEST_VERSION_URL = "https://raw.githubusercontent.com/tkbstudios/ti84pluscenet-bridge/main/version.txt"
CURRENT_VERSION = "0.0.1"

#---BRIDGE CONFIG---#

TCP_HOST = 'individual-builders.at.ply.gg' # TCP Server address. default: ti84pluscenethub.tkbstudios.tk
TCP_PORT = 50252 # Server port. default: 50252 for default address

DEBUG = True # ENABLE DEBUG MODE, Shows more information in console, useful if staff asks for console log. default: True

PING_SERVER = False # [DOES NOT WORK!!] Enable or disable server ping, disable to get a more clean console. default: True
PING_INTERVAL = 3 # Time between every server ping. default: 3
EXIT_IF_PING_IS_ZERO = True # If the ping is 0, then disconnect the serial device and clean exit the bridge. default: True

RETRY_DEFAULT_PORT_FOREVER = True # Retry the default rpi0W2 port (/dev/ttyACM0) forever if it fails. default: True

#-END BRIDGE CONFIG-#


# DO NOT TOUCH THIS CONF
packets_dictionary = {
    0x00: "USERNAME:",
    0x01: "USERTOKEN:"
}
# STOP CONF

serial_connection = serial.Serial()

def checkForUpdate():
    print("Checking for updates...")
    try:
        with urllib.request.urlopen(LATEST_VERSION_URL) as response:
            latest_version = response.read().decode().strip()
    except urllib.error.URLError as e: # type: ignore
        print("Error: ", str(e.reason))
        sys.exit(1)

    if latest_version != CURRENT_VERSION:
        print("New version available! Please update!")
        print("https://github.com/tkbstudios/ti84pluscenet-bridge/blob/main/tinet-bridge.py")
        print("Shortened link: https://tinyurl.com/mr3rxx3v")
        sys.exit(1)
    else:
        print("Current version is up to date")


def directUpdate():
    print("Pulling latest files...")
    os.system("git config pull.ff only")
    os.system("git pull")

#checkForUpdate()
directUpdate()

connected = False


def CleanExit(serial_connection, server_client_sock, reason):
    print(str(reason))
    print("Notifying client bridge got disconnected!                      ")
    serial_connection.write("bridgeDisconnected".encode())
    serial_connection.write("internetDisconnected".encode())
    print("Notified client bridge got disconnected!                      ")
    serial_connection.close()
    server_client_sock.close()
    sys.exit(0)


def server_ping(server_client_sock, serial_connection):
    while True:
        start_time = time.time()
        server_client_sock.send("server_ping".encode())

        ping_response = server_client_sock.recv(16)
        end_time = time.time()
        elapsed_time = math.floor((end_time - start_time) * 1000)
        
#        ser.write(f"ping:{elapsed_time}\0".encode())
        print(f"Ping: {elapsed_time}ms")

        if elapsed_time >= 1000:
            CleanExit(serial_connection=serial_connection, server_client_sock=server_client_sock, reason="\nPing was higher than 1000, preventing lag! Exiting cleanly...")
            break

        if EXIT_IF_PING_IS_ZERO == True:
            if elapsed_time == 0:
                CleanExit(serial_connection=serial_connection, server_client_sock=server_client_sock, reason="\nPing was 0, disconnected from server! Exiting cleanly...")
                break

        time.sleep(PING_INTERVAL)

def serial_read(serial_connection, server_client_sock):
    while True:
        data = serial_connection.read(serial_connection.in_waiting)
        if data.decode() != "":
            decoded_data = data.decode().replace("/0", "")
            if DEBUG: print(f'Received serial encoded data: {data}')
            print(f'Received serial: {decoded_data}')

            server_client_sock.send(decoded_data.encode())

def server_read(serial_connection, server_client_sock):
    while True:
        server_response = server_client_sock.recv(4096)
        decoded_server_response = server_response.decode()

        if DEBUG: print(f'Received server encoded data: {server_response}')
        print(f'Received server: {decoded_server_response}')

        serial_connection.write(server_response.decode().encode())


def list_serial_ports():
    ports = list_ports.comports()
    for i, port in enumerate(ports):
        print(f"{i + 1}. {port.device} - {port.description}")
    return ports

def select_serial_port(ports):
    selected_index = int(input("Enter the number of the serial device you want to select: ")) - 1
    if 0 <= selected_index < len(ports):
        return ports[selected_index]
    else:
        print("Invalid selection. Please try again.")
        return select_serial_port(ports)



print("\rIniting serial...\n")

try:
    # deepcode ignore PythonSameEvalBinaryExpressiontrue: This is a config made by the user
    if RETRY_DEFAULT_PORT_FOREVER == True:
        while True:
            print("Trying default netbridge port...")
            serial_connection = serial.Serial("/dev/ttyACM0", baudrate=9600, timeout=3)
            if serial_connection.is_open == True: break

except serial.SerialException:
    try:
        print("DEFAULT PORT FAILED!")
        available_ports = list_serial_ports()
        selected_port_info = select_serial_port(available_ports)
        serial_connection = serial.Serial(selected_port_info.device, baudrate=9600, timeout=3)
        print(f"Connected to: {serial_connection.portstr}")
    except serial.SerialException:
        print("FAILED CONNECTION!")
        print("Are you sure your calculator is in TINET program\nwith a valid key and connected to USB?")

print("\rCreating TCP socket...                      ", end="")

server_client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_client_sock.settimeout(10)

print("\rConnecting to TCP socket...                      ", end="")

server_client_sock.connect((TCP_HOST, TCP_PORT))

print("\rNotifying serial client he is connected to the bridge...                      ", end="")

serial_connection.write("bridgeConnected\0".encode())
print("\rClient got notified he was connected to the bridge!                      ", end="")

time.sleep(1) # Add delay to prevent the client to not see the SERIAL_CONNECTED_CONFIRMED message

print("\rReading data from serial device...                      ")
try:
    # Windows doesn't allow connection even when allowed through private and public networks firewall
    # Someone fix that lol
    # deepcode ignore PythonSameEvalBinaryExpressiontrue: Nah just ignore it
    if PING_SERVER == True:
        ping_server_thread = threading.Thread(target=server_ping(server_client_sock=server_client_sock, serial_connection=serial_connection))
        ping_server_thread.name = "ping_server"
        ping_server_thread.daemon = True
        ping_server_thread.start()

    serial_read_thread = threading.Thread(target=serial_read, args=(serial_connection, server_client_sock))
    serial_read_thread.name = "SERIAL_READ_THREAD"
    serial_read_thread.start()
    server_read_thread = threading.Thread(target=server_read, args=(serial_connection, server_client_sock))
    server_read_thread.name = "SERVER_READ_THREAD"
    server_read_thread.start()

except KeyboardInterrupt:
    CleanExit(serial_connection=serial_connection, server_client_sock=server_client_sock, reason="\nRecieved CTRL+C! Exiting cleanly...")