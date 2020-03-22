from socket import *

server_name = 'localhost'
server_port = 12000

quit_cmd = 'quit'

while True:
	msg = input('input lowercase sentence: ')
	
	if msg == quit_cmd:
		break

	client_socket = socket(AF_INET, SOCK_STREAM)
	client_socket.connect((server_name, server_port))
		
	client_socket.send(msg.encode())
	modified_msg = client_socket.recv(1024)
	
	print('From Server: ', modified_msg.decode())
	client_socket.close()