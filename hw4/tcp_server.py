from socket import *

server_port = 12000
# UDP: SOCK_DGRAM
server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(('localhost', server_port))
server_socket.listen(1)

print('The server is ready to receive')

while True:
	conn_socket, client_addr = server_socket.accept()
	
	msg = conn_socket.recv(1024).decode()
	print('received from ', client_addr, ': ', msg)
	
	modified_msg = msg.upper()
	conn_socket.send(modified_msg.encode())
	
	# simply process, actually can be saved for management
	conn_socket.close()