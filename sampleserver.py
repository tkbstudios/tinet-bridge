import socket
import requests
import json

# Set up the server socket
host = '127.0.0.1'
port = 5556
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(1)

print(f'Server listening on {host}:{port}')


while True:
    # Wait for a client connection
    client_socket, address = server_socket.accept()
    print(f'Connected by {address}')

    # Receive data from the client
    data = client_socket.recv(1024).decode().strip()

    if data == "SERIAL_CONNECTED":
        response = "OK"
    elif data == 'SHUTDOWN':
        server_socket.close()
    elif data == "currentTime":
        time_response = requests.get("https://timeapi.io/api/Time/Current/zone?timeZone=Europe/Brussels")
        time_data = json.loads(time_response.text)
        response = f"currentTime:{time_data['time']}"
    else:
        # Send a different response if the received data is something else
        response = 'Invalid request'

    # Send the response back to the client
    client_socket.send(response.encode())

    # Close the client connection
    client_socket.close()