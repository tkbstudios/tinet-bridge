import socket

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
    print(data)

    if data == 'Hello':
        # Send the response "OK" if the received data is "Hello"
        response = 'OK'
    elif data == 'SHUTDOWN':
        server_socket.close()
    else:
        # Send a different response if the received data is something else
        response = 'Invalid request'

    # Send the response back to the client
    client_socket.sendall(response.encode())

    # Close the client connection
    client_socket.close()