
# generate random secret number by server (done)
# register players with TCP (done)
# players attempt to guess using UDP (done)
# server responds toi each guess with a message using UDP (e.g., "too high", "too low", "correct") (done)
# if player wins, send them a message using TCP to all players (done)

import socket, random, threading, time, collections



tcp_port = 6000
udp_port = 6001
server_name = "localhost"
min_players = 2
max_players = 4
to_enter_your_guess = 10.0
game_duration = 60.0
player_reg_timeout = 120.0
player_kick_timeout = 5.0

player_list = []
tcp_connections = {}

udp_player_addresses = {}

server_secret_number = 0 # initialized to 0

tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

player_guesses = {}






def udp_pingpong(player_name: str):
    try:
        udp_socket.sendto(b"ping", udp_player_addresses[player_name])
        udp_socket.settimeout(5)
        if udp_socket.recvfrom(1024)[0] != b"pong":
            raise Exception("No pong received")
    except Exception as e:
        udp_player_addresses[player_name].close()
        return False
    return True




def generate_secret_number() -> int:
    return random.randint(1, 100)


def register_udp_players():
    timeout = 5
    start_time = time.time()    
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            break
        try:
            udp_socket.settimeout(10)
            message, client_address = udp_socket.recvfrom(1024)
            player_name = message.decode()
            udp_player_addresses[player_name] = udp_player_addresses.get(player_name, client_address)

        except socket.timeout:
            continue
        except Exception as e:
            continue

def verify_udp_players():
    for player_name in player_list:
        if player_name not in udp_player_addresses:
            remove_player(player_name)




def check_round_over(start_time: float) -> bool:
    for player_name in player_list:
        if player_guesses[player_name] == server_secret_number:
            return True
    elapsed_time = time.time() - start_time
    if elapsed_time > game_duration:
        return True
    return False


def udp_remove_player(player_name: str):
    if player_name in udp_player_addresses:
        del udp_player_addresses[player_name]
    if player_name in player_guesses:
        del player_guesses[player_name]
    if player_name in player_list:
        player_list.remove(player_name)
    if player_name in tcp_connections:
        tcp_connections[player_name].close()
        del tcp_connections[player_name]


def udp_player_turn(player_name: str, start_time):
    while True:
        try:
            if check_round_over(start_time):
                return
            
            if not udp_pingpong(player_name):
                print(f"Player {player_name} disconnected.")
                udp_remove_player(player_name)
                return 



            udp_socket.sendto("Enter your guess (1-100): ".encode(), udp_player_addresses[player_name])
            message, client_address = udp_socket.recvfrom(1024)
            raw_guess = message.decode()
            try:
                guess = int(raw_guess)
                if guess < 1 or guess > 100:
                    udp_socket.sendto("Warning: Out of range, miss your chance.".encode(), client_address)
                    time.sleep(to_enter_your_guess)
                    continue
            except ValueError:
                udp_socket.sendto(f"Warning: invalid input. miss your chance.".encode(), client_address)
                time.sleep(to_enter_your_guess)
                continue    
            
            player_guesses[player_name] = guess

            if guess == server_secret_number:
                udp_socket.sendto(f"Feedback: CORRECT".encode(), client_address)
                broadcast_tcp_message(f"{player_name} guessed the number {server_secret_number} correctly!")
                return
            elif guess < server_secret_number:
                udp_socket.sendto(f"Feedback: Higher".encode(), client_address)
                time.sleep(to_enter_your_guess)
            else:
                udp_socket.sendto(f"Feedback: Lower".encode(), client_address)
                time.sleep(to_enter_your_guess)
        except Exception as e:
            continue


def game_round():
    start_time = time.time()
    for player_name in player_list:
        threading.Thread(target=udp_player_turn, args=(player_name,start_time)).start()
    
    while not check_round_over(start_time):
        time.sleep(1)





def broadcast_udp_message(message: str):
    for player_name in udp_player_addresses:
        try:
            udp_socket.sendto(message.encode(), udp_player_addresses[player_name])
        except Exception as e:
            continue



#####################################################################################################
#                                         TCP                                                       #
#####################################################################################################

# returns true/false if the game can start
def check_start_game() -> bool:
    if len(player_list) < min_players:
        return False
    return True


def broadcast_tcp_message(message: str):
    for player_name in tcp_connections:
        connection = tcp_connections[player_name]
        try:
            connection.send(message.encode())
        except Exception as e:
            continue
    return True


# attempt to register a player, returns true if successful, false otherwise
def register_player(player_name: str) -> tuple[str, bool]:
    if player_name in player_list:
        return "player already registered", False
    if len(player_list) > max_players:
        return "too many players", False
    if len(player_name) < 3:
        return "name too short", False
    if len(player_name) > 100:
        return "name too long", False
    player_list.append(player_name)
    waiting_room = '\n'.join(player_list)
    return f"\nConnected as {player_name}\nWaiting room:\n{waiting_room}", True 



def remove_player(player_name: str):
    if player_name in player_list:
        player_list.remove(player_name)



def check_player_connections():
    for player_name in player_list:
        try:
            tcp_connections[player_name].settimeout(player_kick_timeout)
            tcp_connections[player_name].send(b"ping")
            if tcp_connections[player_name].recv(1024) != b"pong":
                raise Exception("No pong received")
        except socket.timeout:
            print(f"Player {player_name} timed out. Removing from game.")
            tcp_connections[player_name].close()
            del tcp_connections[player_name]
            remove_player(player_name)
        except Exception as e:
            print(f"Error checking connection for player {player_name}: {e}")
            tcp_connections[player_name].close()
            del tcp_connections[player_name]
            remove_player(player_name)

def close_tcp_connections():
    for con in tcp_connections:
        try:
            connection = tcp_connections[con]
            connection.close()
        except Exception as e:
            print(f"Error closing connection: {e}")
            continue
    tcp_connections.clear()

def init_sockets():
    tcp_socket.bind((server_name, tcp_port))
    tcp_socket.listen(5)
    tcp_socket.setblocking(False)
    print(f"TCP socket listening on port {tcp_port}...")


    udp_socket.bind((server_name, udp_port))
    udp_socket.setblocking(False)
    print(f"UDP socket listening on port {udp_port}...")

def pingpong(connection_socket: socket.socket):
    try:
        connection_socket.send(b"ping")
        connection_socket.settimeout(5)
        if connection_socket.recv(1024) != b"pong":
            raise Exception("No pong received")
    except socket.timeout:
        connection_socket.close()
        return False
    except Exception as e:
        connection_socket.close()
        return False
    return True

def handle_client(connection_socket: socket.socket, addr):
    try:
        # send the welcome message
        connection_socket.send(f"Welcome to the game server! Please enter your name: ".encode())
        connection_socket.settimeout(player_reg_timeout)

        # receive the player's name
        player_name = connection_socket.recv(1024).decode()
        print(f"Received player name: {player_name}")

        if not player_name:
            print("No player name received. Closing connection.")
            connection_socket.close()
            return
        response_message, response_status = register_player(player_name)
        

        while not response_status:
            connection_socket.send(f"{response_message}".encode())
            player_name = connection_socket.recv(1024).decode()
            response_message, response_status = register_player(player_name)

        connection_socket.send(f"{response_message}".encode())
        
        connection_socket.settimeout(None)
        tcp_connections[player_name] = connection_socket

        return  

    except TimeoutError:
        print("Player registration timed out. Closing connection.")
        connection_socket.close()
        return

def accept_tcp_connections_threaded():
    while True:
        # accept a new connection
        try:
            connection_socket, addr = tcp_socket.accept()
        except BlockingIOError:
            time.sleep(2)
            check_player_connections()
            if check_start_game():
                print("Game can start...")
                return
            continue
        except Exception as e:
            print(f"Error accepting connection: {e}")
            continue

        # start a new thread for each connection
        threading.Thread(target=handle_client, args=(connection_socket,addr)).start()


def ask_users_to_play():
    for player_name in player_list:
        try:
            tcp_connections[player_name].send(b"Do you want to play? (yes/no): ")
            tcp_connections[player_name].settimeout(5)
            response = tcp_connections[player_name].recv(1024).decode()
            if response.lower() == "no":
                remove_player(player_name)
                continue
        except socket.timeout:
            print(f"Player {player_name} timed out. Removing from game.")
            tcp_connections[player_name].close()
            del tcp_connections[player_name]
            remove_player(player_name)
        except Exception as e:
            print(f"Error checking connection for player {player_name}: {e}")
            tcp_connections[player_name].close()
            del tcp_connections[player_name]
            remove_player(player_name)




###############################################################################################
#                                           MAIN                                              #
###############################################################################################

def main():
    init_sockets()

    # print start message
    print(f"Server started on {server_name}: TCP {tcp_port}, UDP {udp_port}")

    accept_tcp_connections_threaded()
    still_playing = True

    while still_playing:
        for player_name in player_list:
            player_guesses[player_name] = 0

        print(f"Game started with {len(player_list)} players...")
        broadcast_tcp_message(f"Game started with players: {', '.join(player_list)}")

        # initialize game logic
        server_secret_number = generate_secret_number()

        register_udp_players()
        time.sleep(5)
        verify_udp_players()

        broadcast_udp_message("You have 60 seconds to guess the number (1-100)!")

        print("round begin")
        game_round()

        for player_name in player_list:
            if player_guesses[player_name] == server_secret_number:
                message = """"==GAME RESULTS==
                Target number: {server_secret_number}
                Winner: {player_name}
                """
                broadcast_tcp_message(f"{player_name} guessed the number {server_secret_number} correctly!")
            else:
                message = f"==GAME RESULTS==\nTarget number: {server_secret_number}\nWinner: None"
                broadcast_tcp_message(message)
        
        ask_users_to_play()
        still_playing = check_start_game()
        
    close_tcp_connections()


main()

