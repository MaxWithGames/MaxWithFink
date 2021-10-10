from os import read
import socket
import cloudpickle as pickle
from dataclasses import dataclass
import select
import threading
import sys

sys.path.append('../')

from common.world import World, generate_perlin_noise_2d
from common.utils import recvall, sendall
from common.player import Player

# print(generate_perlin_noise_2d((10, 10), (2, 2)))
# exit()

class Server():
    @dataclass 
    class User():
        addres: str
        socket: socket.socket
        player: Player


    def init_socket(self):
        main_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        main_socket.bind(('localhost', 1236))
        main_socket.listen()

        return main_socket

    def __init__(self):
        self.main_socket = self.init_socket()
        self.users = []
        self.is_running = False

        print('Creating world...')
        self.world = World((32, 32))
        #self.world.generate_random_wolrd()
        self.world.generate_world_from_perlin_noise()
        print('World generated!')

        self.lock = threading.Lock()

    def is_known_addres(self, addres):
        is_known = False
        for user in self.users:
            if user.addres == addres:
                is_known = True
                break
        return is_known

    def on_new_user(self, socket, addres):
        world_data = self.world.to_binary()
        sendall(socket, world_data)
        player = pickle.loads(recvall(socket))
        self.users.append(Server.User(socket=socket, addres=addres, player=player))

    def on_user_disconnect(self, socket):
        for user in self.users:
            if user.socket is socket:
                self.users.remove(user)
                break

    def handle_tcp(self):
        while self.is_running:
            read_list = [self.main_socket]
            for user in self.users:
                read_list.append(user.socket)

            r_sockets, *_ = select.select(read_list, [], [])
            for r_socket in r_sockets:
                if r_socket is self.main_socket:
                    socket, addres = self.main_socket.accept()
                    print(addres)

                    if not self.is_known_addres(addres):
                        self.on_new_user(socket, addres)
                else:
                    data = recvall(r_socket)
                    
                    if data is None:
                        self.on_user_disconnect(socket)
                        continue

                    player = pickle.loads(data)
                    
                    for user in self.users:
                        if user.player.name == player.name:
                            user.player = player
                            break

                    other_players = []
                    for user in self.users:
                        if user.player.name != player.name:
                            other_players.append(user.player)
                    sendall(r_socket, pickle.dumps(other_players))
                    

    def handle_world(self):
        pass

    def run(self):
        self.is_running = True
        tcp_thread = threading.Thread(target=self.handle_tcp)
        tcp_thread.start()
        world_thread = threading.Thread(target=self.handle_world)
        world_thread.start()


server = Server()
server.run()