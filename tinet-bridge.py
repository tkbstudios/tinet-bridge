import serial
import socket
import sys
import time
import urllib.request
import threading
import math


LATEST_VERSION_URL = "https://raw.githubusercontent.com/tkbstudios/ti84pluscenet-bridge/main/version.txt"
CURRENT_VERSION = "0.0.1"

#---BRIDGE CONFIG---#

TCP_HOST = 'our-excellent.at.ply.gg' # Server address. default: ti84pluscenethub.tkbstudios.tk
TCP_PORT = 25199 # Server port. default: 50252 for default address

DEBUG = True # ENABLE DEBUG MODE, Shows more information in console, useful if staff asks for console log. default: True

PING_SERVER = False # [DOES NOT WORK!!] Enable or disable server ping, disable to get a more clean console. default: True
PING_INTERVAL = 3 # Time between every server ping. default: 3
EXIT_IF_PING_IS_ZERO = True # If the ping is 0, then disconnect the serial device and clean exit the bridge. default: True

PREDEFINED_COM_PORT = "COM5" # Leave empty to choose which COM port to use at bridge start. default: ""

#-END BRIDGE CONFIG-#

def checkForUpdate():
    print("Checking for updates...")
    try:
        with urllib.request.urlopen(LATEST_VERSION_URL) as response:
            latest_version = response.read().decode().strip()
    except urllib.error.URLError as e: # type: ignore
        print("Error: ", str(e.reason))
        sys.exit(1)

    # Compare the versions
    if latest_version != CURRENT_VERSION:
        print("New version available! Please update!")
        print("https://github.com/tkbstudios/ti84pluscenet-bridge/blob/main/tinet-bridge.py")
        print("Shortened link: https://tinyurl.com/mr3rxx3v")
        sys.exit(1)
    else:
        print("Current version is up to date")


checkForUpdate()

# Define the USB device port
if PREDEFINED_COM_PORT == "":
    USB_PORT = input("Please enter COM port (COM1, COM2, etc..): ")
else:
    USB_PORT = PREDEFINED_COM_PORT

connected = False


def CleanExit(serial_connection, server_client_sock, reason):
    print(str(reason))
    print("Notifying client bridge got disconnected!                      ", end="")
    serial_connection.write("bridgeDisconnected".encode())
    serial_connection.write("internetDisconnected".encode())
    time.sleep(0.5)
    print("\rNotified client bridge got disconnected!                      ", end="")
    serial_connection.close()
    server_client_sock.close()


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


print("\rIniting serial...", end="")

serial_connection = serial.Serial(USB_PORT, baudrate=9600, timeout=1)
time.sleep(0.5)

print("\rCreating TCP socket...                      ", end="")

server_client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_client_sock.settimeout(10)
time.sleep(0.5)

print("\rConnecting to TCP socket...                      ", end="")

server_client_sock.connect((TCP_HOST, TCP_PORT))
time.sleep(0.5)

print("\rNotifying serial client he is connected to the bridge...                      ", end="")
time.sleep(0.5)

serial_connection.write("bridgeConnected\0".encode())
print("\rClient got notified he was connected to the bridge!                      ", end="")

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

    while True:
        try:
            # Read data from the USB device
            data = serial_connection.read(serial_connection.in_waiting)

            # Print the data if it isn't empty
            if data.decode() != "":
                decoded_data = data.decode()
                if DEBUG == True: print(f'Recieved serial encoded data: {data}')
                print(f'Recieved serial decoded data: {decoded_data}')

                # Send and wait for response from socket
                server_client_sock.send(decoded_data.encode())
                response = server_client_sock.recv(1024)
                decoded_response = response.decode()

                if DEBUG == True: print(f'Recieved socket encoded data: {data}')
                print(f'Recieved socket decoded data: {decoded_data}')

                # If the response is OK, send "internetConnected" to the serial device
                if decoded_response == "OK":
                    serial_connection.write("internetConnected\0".encode())
                    print("Sent 'internetConnected' to serial device")
                else:
                    print(decoded_response)

        except (serial.SerialException, OSError, IOError) as e:
            print('\nSerial device appears disabled. Disconnecting from remote host')
            if DEBUG == True: print(f"Full error: {str(e)}")
            connected = False
            try:
                server_client_sock.close()
                sys.exit(1)
            except NameError: pass

except KeyboardInterrupt:
    CleanExit(serial_connection=serial_connection, server_client_sock=server_client_sock, reason="\nRecieved CTRL+C! Exiting cleanly...")