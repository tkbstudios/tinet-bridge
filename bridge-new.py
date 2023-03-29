import serial
import socket
import sys

# Define the USB device port
USB_PORT = 'COM5'

# Define the TCP socket connection details
TCP_HOST = '127.0.0.1'
TCP_PORT = 5556


# Create the serial connection to the USB device
ser = serial.Serial(USB_PORT, baudrate=9600, timeout=1)

# Create the TCP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the TCP host
sock.connect((TCP_HOST, TCP_PORT))

# Send to client that bridge has connected
ser.write("bridgeConnected\0".encode())
print("Sent bridgeConnected!")

# Continuously stream data from the USB device to the TCP socket
while True:
    try:
        # Read data from the USB device
        data = ser.read(ser.in_waiting)

        # Send the data over the TCP socket
        sock.sendall(data)

        # Print the data
        if data.decode() != "":
            print(data)

    except (serial.SerialException, OSError, IOError): 
        print('Serial device appears disabled. Disconnecting from remote host\n')
        connected = False
        try:
            sock.close()
            sys.exit(1)
        except NameError: pass

# Close the serial connection and TCP socket
ser.close()
sock.close()