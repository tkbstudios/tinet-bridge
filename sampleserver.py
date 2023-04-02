import socket
import requests
import json
import threading
import sys


#----BEGIN CONFIG----#
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5556
DEBUG = True
#-----END CONFIG-----#


# Set up the server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(1)

print(f'Server listening on {SERVER_HOST}:{SERVER_PORT}')


def client_handler(client_socket, address):
    if DEBUG == True: print(f'Connected by {address}')
    try:
        sockresponse = ""
        while True:
            try:
                data = client_socket.recv(1024).decode().strip()
            except ConnectionAbortedError:
                print(f'{address} disconnected!')
                break
            except ConnectionRefusedError:
                print(f'Connection refused. address: {address}')
                break
            except ConnectionError:
                print(f'Connection error. address: {address}')
                break
        
            if data != "":
                if DEBUG == True: print(data)

            if data == "SERIAL_CONNECTED":
                sockresponse = "SERIAL_CONNECTED_CONFIRMED_BY_SERVER"

            elif data == "server_ping":
                sockresponse = "server_pong"

            elif data == 'SHUTDOWN':
                client_socket.close()
                server_socket.close()
                break

            elif data == "currentTime":
                time_response = requests.get("https://timeapi.io/api/Time/Current/zone?timeZone=Europe/Brussels")
                time_data = json.loads(time_response.text)
                sockresponse = f"currentTime:{str(time_data['time'])}"

            elif data != "":
                sockresponse = 'Invalid request'

            client_socket.send(sockresponse.encode())
    except socket.timeout or socket.error as e:
        print(str(e))

while True:
    try:
        # Wait for a client connection
        client_socket, address = server_socket.accept()
        new_client_thread = threading.Thread(target=client_handler(client_socket=client_socket, address=address))
        new_client_thread.name = str(address)
        new_client_thread.daemon = True
    except KeyboardInterrupt:
        server_socket.close()
        sys.exit(1)