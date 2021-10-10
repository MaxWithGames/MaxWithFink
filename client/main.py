from sys import flags
import pygame
import socket
import cloudpickle as pickle
from pygame import key
from settings import get_settings
import sys
import threading
from select import select

sys.path.append('../')

from common.world import World
from common.utils import recvall, sendall
from common.player import Player

settings = get_settings()

main_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM,
)

main_player = Player([0, 0], settings.name)
other_players = []

print((settings.server_addres, settings.server_port))
main_socket.connect((settings.server_addres, settings.server_port))
response = recvall(main_socket)
sendall(main_socket, pickle.dumps(main_player))

world = World()
world.from_binary(response)

pygame.init()

video_info = pygame.display.Info()
print(video_info.current_w, video_info.current_h)

screen = pygame.display.set_mode(size=(settings.resolution_x, settings.resolution_y), flags=pygame.FULLSCREEN)
canvas = pygame.Surface(size=(1920, 1080))

class Camera:
    def __init__(self, function=None) -> None:
        self.function=function

    def get_offset(self, p_pos, c_size):
        if self.function is None:
            raise NotImplementedError
        return self.function(p_pos, c_size)
    
    def set_function(self, function=None):
        self.function = function

def follow_player(p_pos, c_size):
    return (c_size[0] // 2 - p_pos[0], c_size[1] // 2 - p_pos[1])

camera = Camera(follow_player)

names_font = pygame.font.Font('Deiland.ttf', 32)

is_running = True
last_update_time = pygame.time.get_ticks()
target_delay = 1000 // settings.target_fps

other_players = []
lock = threading.Lock()

def tcp():
    global other_players, main_player, is_running
    while is_running:
        sendall(main_socket, pickle.dumps(main_player))
        _ = select([main_socket], [], [])
        other_players = pickle.loads(recvall(main_socket))

tcp_thread = threading.Thread(target=tcp)
tcp_thread.start()

while is_running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            is_running = False

    lock.acquire()
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        main_player.pos[0] -= 5
    if keys[pygame.K_RIGHT]:
        main_player.pos[0] += 5
    if keys[pygame.K_UP]:
        main_player.pos[1] -= 5
    if keys[pygame.K_DOWN]:
        main_player.pos[1] += 5
    if keys[pygame.K_ESCAPE]:
        is_running = False
    lock.release()

    dx, dy = camera.get_offset(main_player.pos, canvas.get_size())

    screen.fill((0, 0, 0))
    canvas.fill((0, 0, 0))

    visible_area = (
        main_player.pos[0] - canvas.get_size()[0] // 2,
        main_player.pos[1] - canvas.get_size()[1] // 2,
        main_player.pos[0] + canvas.get_size()[0] // 2,
        main_player.pos[1] + canvas.get_size()[1] // 2
    )

    world.render(canvas, (dx, dy), visible_area)

    pygame.draw.rect(canvas, (0, 0, 255), (main_player.pos[0] + dx, main_player.pos[1] + dy, 60, 70))
    main_player_name = names_font.render(main_player.name, True, (255, 255, 255))
    canvas.blit(main_player_name, (main_player.pos[0] - 10 + dx, main_player.pos[1] - 10 + dy))

    for other_player in other_players:
        pygame.draw.rect(canvas, (0, 255, 0), (other_player.pos[0] + dx, other_player.pos[1] + dy, 60, 70))
        other_player_name = names_font.render(other_player.name, True, (255, 255, 255))
        canvas.blit(other_player_name, (other_player.pos[0] - 10 + dx, other_player.pos[1] - 10 + dy))

    screen_ratio = screen.get_size()[0] / screen.get_size()[1]

    if screen_ratio <= 16 / 9:
        scale = (int(screen.get_size()[1] * 16 / 9), screen.get_size()[1])
    else:
        scale = (screen.get_size()[0], int(screen.get_size()[0] * 9 / 16))
    
    print(scale)

    scaled_canvas = pygame.transform.smoothscale(canvas, scale)
    canvas_x_offset = (scaled_canvas.get_size()[0] - screen.get_size()[0]) // 2
    screen.blit(scaled_canvas, (-canvas_x_offset, 0))

    pygame.display.flip()

    curr_time = pygame.time.get_ticks()
    pygame.time.delay(target_delay - (curr_time - last_update_time))
    print(target_delay - (curr_time - last_update_time))
    last_update_time = pygame.time.get_ticks()

pygame.quit()