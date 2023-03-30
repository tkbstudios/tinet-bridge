import serial
import socket
import sys
import time

# Define the USB device port
USB_PORT = input("Please enter COM port (COM1, COM2, etc..): ")

# Define the TCP socket connection details
TCP_HOST = '127.0.0.1'
TCP_PORT = 5556


print("\rIniting serial...", end="")
# Create the serial connection to the USB device
ser = serial.Serial(USB_PORT, baudrate=115200, timeout=1)
time.sleep(0.5)

print("\rCreating TCP socket...                      ", end="")
# Create the TCP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10)
time.sleep(0.5)

print("\rConnecting to TCP socket...                      ", end="")
# Connect to the TCP host
sock.connect((TCP_HOST, TCP_PORT))
time.sleep(0.5)

print("\rNotifying serial client he is connected to the bridge...                      ", end="")
time.sleep(0.5)
# Send to client that bridge has connected
ser.write("bridgeConnected\0".encode())
print("\rClient got notified he was connected to the bridge!                      ", end="")
time.sleep(0.5)

# Continuously stream data from the USB device to the TCP socket
print("\rStarting to read data from serial device...                      ")
try:
    while True:
        try:
            # Read data from the USB device
            data = ser.read(ser.in_waiting)

            # Send all the data recieved from serial to the TCP server
            sock.sendall(data)

            # Wait for a response from the TCP host
            response = sock.recv(4096)
            
            # If the response is OK, send "internetConnected" to the serial device
            if response.decode() == "OK":
                ser.write("internetConnected\0".encode())
                print("Sent 'internetConnected' to serial device")

            # Print the data if it isn't empty
            if data.decode() != "":
                print(f'Recieved data: {data}')

        except (serial.SerialException, OSError, IOError): 
            print('\nSerial device appears disabled. Disconnecting from remote host')
            connected = False
            try:
                sock.close()
                sys.exit(1)
            except NameError: pass
except KeyboardInterrupt:
    print("\nRecieved CTRL+C! Exiting cleanly...")
    print("Notifying client bridge got disconnected!                      ", end="")
    ser.write("bridgeDisconnected".encode())
    time.sleep(0.5)
    print("\rNotified client bridge got disconnected!                      ", end="")
    ser.close()
    sock.close()