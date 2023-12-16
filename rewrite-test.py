import time
import serial
import serial.tools.list_ports


def find_serial_port():
    while True:
        time.sleep(0.2)
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if "USB Serial Device" in port.description or "TI-84" in port.description:
                return port


if __name__ == "__main__":
    serial_port = find_serial_port()
    serial_connection = serial.Serial(serial_port.device, 115200, timeout=0.2)
    serial_connection.write(b"BRIDGE_CONNECTED\0")
    while True:
        data = serial_connection.read(1024)
        if data:
            decoded_data = data.decode()
            if decoded_data == "CONNECT_TCP":
                print("Connect to TCP server")
                serial_connection.write(b"TCP_CONNECTED\0")
            elif decoded_data.startswith("LOGIN:"):
                login_data = decoded_data.replace("LOGIN:", "").split(":", 2)
                # hides the key from the console
                login_data[2] = login_data[2][:4] + ("*" * 50) + login_data[2][-4:]
                print(f"Login data: {login_data}")
                serial_connection.write(b"LOGIN_SUCCESS\0")
            elif decoded_data == "BRIDGE_PING":
                serial_connection.write(b"BRIDGE_PONG\0")
            else:
                print(decoded_data)
