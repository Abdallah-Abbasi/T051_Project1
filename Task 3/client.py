
import socket
import time

udp_port = 6001
tcp_port = 6000
server_name = 'localhost'

player_patience_timeout = 60.0


player_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
player_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def init_tcp_sockets(): 
    player_tcp_socket.connect((server_name, tcp_port))


def init_udp_socket():
    player_udp_socket.connect((server_name, udp_port))
    print(f"UDP connection established")



if __name__ == "__main__":
    init_tcp_sockets()
    
    server_message = player_tcp_socket.recv(1024).decode('utf-8')

    player_name = input(server_message)
    player_tcp_socket.sendall(player_name.encode('utf-8'))

    # receive the response from the server
    response = player_tcp_socket.recv(1024).decode('utf-8')
    print(response)
    init_udp_socket()

    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > player_patience_timeout:
            print("Player patience timeout reached. Exiting...")
            break
        try:
            # receive the message from the server
            message = player_tcp_socket.recv(1024).decode('utf-8')
            if not message:
                continue
            if message == "ping":
                player_tcp_socket.sendall(b"pong")
            else:
                print(message)
                break
        except socket.error as e:
            print(f"Socket error: {e}")
            break


    player_udp_socket.sendto(player_name.encode('utf-8'), (server_name, udp_port))   
    print(f"UDP message sent to server: {player_name}")


    # game loop
    while True:
        try:
            # receive the message from the server
            message, addr = player_udp_socket.recvfrom(1024)
            message = message.decode('utf-8')
            if not message:
                continue
            if message == "ping":
                player_udp_socket.sendto(b"pong", (server_name, udp_port))
                continue
            guess = input(message)
            player_udp_socket.sendto(guess.encode('utf-8'), (server_name, udp_port))
            print(f"UDP message sent to server: {guess}")
            response = player_udp_socket.recv(1024).decode('utf-8')
            print(response)
        except Exception as e:
            print(f"Error receiving message: {e}")
            break


    player_tcp_socket.close()
    player_udp_socket.close()






    
