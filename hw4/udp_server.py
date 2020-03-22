from socket import *

server_port = 12000
# UDP: SOCK_DGRAM
server_socket = socket(AF_INET, SOCK_DGRAM)
server_socket.bind(('localhost', server_port))

print('The server is ready to receive')

while True:
	msg, client_addr = server_socket.recvfrom(2048)
	print('received from ', client_addr, ': ', msg.decode())
	modified_msg = msg.decode().upper()
	server_socket.sendto(modified_msg.encode(), client_addr)