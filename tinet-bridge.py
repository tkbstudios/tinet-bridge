import serial
import socket
import sys
import time
import wget


LATEST_VERSION_URL = ""
CURRENT_VERSION = "0.0.1"

def checkForUpdate():
    print("Checking for updates...")
    

# Define the USB device port
USB_PORT = input("Please enter COM port (COM1, COM2, etc..): ")

# Define the TCP socket connection details
TCP_HOST = '127.0.0.1'
TCP_PORT = 5556

DEBUG = True

connected = False


def CleanExit(ser, sock):
    print("Notifying client bridge got disconnected!                      ", end="")
    ser.write("bridgeDisconnected".encode())
    ser.write("internetDisconnected".encode())
    time.sleep(0.5)
    print("\rNotified client bridge got disconnected!                      ", end="")
    ser.close()
    sock.close()

print("\rIniting serial...", end="")

ser = serial.Serial(USB_PORT, baudrate=9600, timeout=1)
time.sleep(0.5)

print("\rCreating TCP socket...                      ", end="")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10)
time.sleep(0.5)

print("\rConnecting to TCP socket...                      ", end="")

sock.connect((TCP_HOST, TCP_PORT))
time.sleep(0.5)

print("\rNotifying serial client he is connected to the bridge...                      ", end="")
time.sleep(0.5)

ser.write("bridgeConnected\0".encode())
print("\rClient got notified he was connected to the bridge!                      ", end="")

print("\rReading data from serial device...                      ")
try:
    while True:
        try:
            # Read data from the USB device
            data = ser.read(ser.in_waiting)

            # Print the data if it isn't empty
            if data.decode() != "":
                decoded_data = data.decode()
                if DEBUG == True: print(f'Recieved serial encoded data: {data}')
                print(f'Recieved serial decoded data: {decoded_data}')

                # Send and wait for response from socket
                sock.send(decoded_data.encode())
                response = sock.recv(1024)
                decoded_response = response.decode()

                if DEBUG == True: print(f'Recieved socket encoded data: {data}')
                print(f'Recieved socket decoded data: {decoded_data}')
                
                # If the response is OK, send "internetConnected" to the serial device
                if decoded_response == "OK":
                    ser.write("internetConnected\0".encode())
                    print("Sent 'internetConnected' to serial device")
                else:
                    print(decoded_response)

        except (serial.SerialException, OSError, IOError) as e: 
            print('\nSerial device appears disabled. Disconnecting from remote host')
            if DEBUG == True: print(f"Full error: {str(e)}")
            connected = False
            try:
                sock.close()
                sys.exit(1)
            except NameError: pass

except KeyboardInterrupt:
    print("\nRecieved CTRL+C! Exiting cleanly...")
    CleanExit(ser, sock)