import asyncio
import time
import serial.tools.list_ports
import serial.serialutil
from serial_asyncio import open_serial_connection


def find_serial_port():
    while True:
        time.sleep(0.2)
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if "USB Serial Device" in port.description or "TI-84" in port.description:
                return port


async def bridge(serial_device):
    serial_reader, serial_writer = await open_serial_connection(url=serial_device, baudrate=115200)

    serial_writer.write("BRIDGE_CONNECTED\0".encode())
    await serial_writer.drain()
    print("sent BRIDGE_CONNECTED")

    while True:
        line = await serial_reader.read(1024)
        message = str(line, 'utf-8').strip()
        print(message)
        if message == "CONNECT_TCP":
            print("received CONNECT_TCP")
            break

    tcp_reader, tcp_writer = await asyncio.open_connection('127.0.0.1', 2052)

    serial_writer.write("TCP_CONNECTED\0".encode())
    await serial_writer.drain()
    print("sent TCP_CONNECTED")

    while True:
        try:
            serial_data = await serial_reader.read(1024)
        except serial.serialutil.SerialException:
            print("Calculator disconnected")
            break
        serial_message = str(serial_data, 'utf-8')
        print(f"RXSRL: {serial_message}")

        tcp_writer.write(serial_message.encode())
        await tcp_writer.drain()
        print(f"TXTCP: {serial_message}")

        tcp_data = await tcp_reader.read(1024)
        tcp_message = tcp_data.decode()
        print(f"RXTCP: {tcp_message}")

        serial_writer.write(tcp_message.encode())
        await serial_writer.drain()
        print(f"TXSRL: {tcp_message}")
    print("Exiting bridge..")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    print("Waiting for a calculator..")
    serial_port = find_serial_port()
    print(serial_port)
    time.sleep(2)
    loop.run_until_complete(bridge(serial_port.device))
