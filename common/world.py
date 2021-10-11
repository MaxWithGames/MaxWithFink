from abc import abstractmethod
import threading
import pygame
import random
import cloudpickle as pickle
import numpy as np

def generate_perlin_noise_2d(shape, res):
    def f(t):
        return 6*t**5 - 15*t**4 + 10*t**3

    delta = (res[0] / shape[0], res[1] / shape[1])
    d = (shape[0] // res[0], shape[1] // res[1])
    grid = np.mgrid[0:res[0]:delta[0],0:res[1]:delta[1]].transpose(1, 2, 0) % 1
    # Gradients
    angles = 2*np.pi*np.random.rand(res[0]+1, res[1]+1)
    gradients = np.dstack((np.cos(angles), np.sin(angles)))
    g00 = gradients[0:-1,0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g10 = gradients[1:,0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g01 = gradients[0:-1,1:].repeat(d[0], 0).repeat(d[1], 1)
    g11 = gradients[1:,1:].repeat(d[0], 0).repeat(d[1], 1)
    # Ramps
    n00 = np.sum(grid * g00, 2)
    n10 = np.sum(np.dstack((grid[:,:,0]-1, grid[:,:,1])) * g10, 2)
    n01 = np.sum(np.dstack((grid[:,:,0], grid[:,:,1]-1)) * g01, 2)
    n11 = np.sum(np.dstack((grid[:,:,0]-1, grid[:,:,1]-1)) * g11, 2)
    # Interpolation
    t = f(grid)
    n0 = n00*(1-t[:,:,0]) + t[:,:,0]*n10
    n1 = n01*(1-t[:,:,0]) + t[:,:,0]*n11
    return np.sqrt(2)*((1-t[:,:,1])*n0 + t[:,:,1]*n1)

class World():
    class BaseBlock():
        def __init__(self, pos, data=None) -> None:
            # pos = (chunk_x, chunk_y, x, y)
            self.pos = pos
            self.data = data
        
        @abstractmethod
        def render(self, canvas, offset, chunk_size):
            raise NotImplementedError

        def get_id(self):
            return 0

        def get_data(self):
            return self.get_id(), self.pos, self.data

        def get_speed_multiplier(self):
            return 1.

        def __repr__(self):
            return f'{self.__class__}({self.pos}, data={self.data})'

    class SimpleBlock(BaseBlock):
        # data = color
        def render(self, canvas, offset, chunk_size):
            dx, dy = offset
            px = self.pos[0] * 64 * chunk_size + self.pos[2] * 64 + dx
            py = self.pos[1] * 64 * chunk_size + self.pos[3] * 64 + dy

            pygame.draw.rect(canvas, self.data, (px, py, 64, 64))
        
        def get_id(self):
            return 1

    class Water(BaseBlock):
        'data: deepnes'
        def __init__(self, pos, data=None) -> None:
            super().__init__(pos, data=data)

            colors = (
                (142, 215, 248),
                (72, 176, 223),
                (6, 141, 206),
                (0, 74, 135)
            )

            speed_multipliers = (0.7, 0.5, 0.3, 0.1)

            self.color = colors[data]
            self.speed_multiplier = speed_multipliers[data]

        def render(self, canvas, offset, chunk_size):
            dx, dy = offset
            px = self.pos[0] * 64 * chunk_size + self.pos[2] * 64 + dx
            py = self.pos[1] * 64 * chunk_size + self.pos[3] * 64 + dy

            pygame.draw.rect(canvas, self.color, (px, py, 64, 64))

        def get_speed_multiplier(self):
            return self.speed_multiplier

        def get_id(self):
            return 2

    class Sand(BaseBlock):
        'data: height'
        def __init__(self, pos, data=None) -> None:
            super().__init__(pos, data=data)

            colors = (
                (248, 248, 223),
                (238, 236, 204)
            )

            speed_multipliers = (0.8, 0.9)

            self.color = colors[data]
            self.speed_multiplier = speed_multipliers[data]

        def render(self, canvas, offset, chunk_size):
            dx, dy = offset
            px = self.pos[0] * 64 * chunk_size + self.pos[2] * 64 + dx
            py = self.pos[1] * 64 * chunk_size + self.pos[3] * 64 + dy

            pygame.draw.rect(canvas, self.color, (px, py, 64, 64))

        def get_speed_multiplier(self):
            return self.speed_multiplier

        def get_id(self):
            return 3

    class Terrain(BaseBlock):
        'data: height'
        def __init__(self, pos, data=None) -> None:
            super().__init__(pos, data=data)

            colors = (
                (163, 209, 45),
                (124, 184, 51),
                (86, 159, 57),
                (47, 134, 62),
                (8, 109, 68)
            )

            self.color = colors[data]

        def render(self, canvas, offset, chunk_size):
            dx, dy = offset
            px = self.pos[0] * 64 * chunk_size + self.pos[2] * 64 + dx
            py = self.pos[1] * 64 * chunk_size + self.pos[3] * 64 + dy

            pygame.draw.rect(canvas, self.color, (px, py, 64, 64))

        def get_id(self):
            return 4

    class ShiningBlock(BaseBlock):
        def render(self, canvas, offset, chunk_size):
            dx, dy = offset
            px = self.pos[0] * 64 * chunk_size + self.pos[2] * 64 + dx
            py = self.pos[1] * 64 * chunk_size + self.pos[3] * 64 + dy

            # colors = [
            #     (211, 211, 211),
            #     (255, 255, 255),
            #     (230, 230, 230),
            #     (240, 240, 240)
            # ]

            colors = (
                (254, 195, 215),
                (255, 171, 213),
                (255, 150, 198),
                (255, 150, 198),
                (254, 195, 215),
                (255, 171, 213),
                (255, 255, 255)
            )

            random.seed(dx * 64 + dy)

            for i in range(32):
                for j in range(32):
                    pygame.draw.rect(
                        canvas,
                        colors[random.randint(0, len(colors) - 1)],
                        (px + i * 2, py + j * 2, 2, 2)
                    )

        def get_id(self):
            return 255

    def generate_random_wolrd(self):
        for i in range(self.chunks_count[0]):
            for j in range(self.chunks_count[1]):
                self.chunks[i][j] = [[None] * self.CHUNK_SIZE for k in range(self.CHUNK_SIZE)]

        for i in range(self.chunks_count[0]):
            for j in range(self.chunks_count[1]):
                for n in range(self.CHUNK_SIZE):
                    for m in range(self.CHUNK_SIZE):
                        self.chunks[i][j][n][m] = World.SimpleBlock(
                            (i, j, n, m), 
                            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                        )
    
    def generate_world_from_perlin_noise(self):
        for i in range(self.chunks_count[0]):
            for j in range(self.chunks_count[1]):
                self.chunks[i][j] = [[None] * self.CHUNK_SIZE for k in range(self.CHUNK_SIZE)]

        noise = generate_perlin_noise_2d(
            (self.chunks_count[0] * self.CHUNK_SIZE, self.chunks_count[1] * self.CHUNK_SIZE),
            (self.chunks_count[0] * self.CHUNK_SIZE // 32, self.chunks_count[1] * self.CHUNK_SIZE // 32)
        )

        def paint_chunk_from_noise(i, j):
            for n in range(self.CHUNK_SIZE):
                for m in range(self.CHUNK_SIZE):
                    h = noise[i * self.CHUNK_SIZE + n, j * self.CHUNK_SIZE + m]
                    if h < -0.1: # water
                        trasholds = (-0.6, -0.35, -0.2)
                        deepness = 3
                        for trashold in trasholds:
                            if h > trashold: deepness -= 1
                        block = World.Water((i, j, n, m), deepness)
                    elif h < 0.1: # sand
                        trasholds = (0.0,)
                        height = 0
                        for trashold in trasholds:
                            if h > trashold: height += 1
                        block = World.Sand((i, j, n, m), height)
                    else: # terrain
                        trasholds = (0.2, 0.35, 0.55, 0.85)
                        height = 0
                        for trashold in trasholds:
                            if h > trashold: height += 1
                        block = World.Terrain((i, j, n, m), height)

                    self.chunks[i][j][n][m] = block

        for i in range(self.chunks_count[0]):
            for j in range(self.chunks_count[1]):
                paint_chunk_from_noise(i, j)

        for i in range(self.chunks_count[0]):
            for j in range(self.chunks_count[1]):
                if random.randint(0, 10) <= 10:
                    x = random.randint(0, self.CHUNK_SIZE - 1)
                    y = random.randint(0, self.CHUNK_SIZE - 1)
                    self.chunks[i][j][x][y] = World.ShiningBlock(
                        (i, j, x, y)
                    )

    # def get_new_block_buy_id(self, id, pos, data=None):
    #     return self.id_dict[id]

    def get_block_by_pos(self, pos) -> BaseBlock:
        if pos[0] < 0 or pos[1] < 0: return None
        if pos[0] > self.chunks_count[0] * self.CHUNK_SIZE * 64: return None
        if pos[1] > self.chunks_count[1] * self.CHUNK_SIZE * 64: return None

        chunk_x = int(pos[0]) // 64 // self.CHUNK_SIZE
        block_x = (int(pos[0]) - chunk_x * self.CHUNK_SIZE * 64) // 64

        chunk_y = int(pos[1]) // 64 // self.CHUNK_SIZE
        block_y = (int(pos[1]) - chunk_y * self.CHUNK_SIZE * 64) // 64

        return self.chunks[chunk_x][chunk_y][block_x][block_y]

    def __init__(self, chunks_count=(0, 0)):
        
        self.id_dict = {
            0: World.BaseBlock,
            1: World.SimpleBlock,
            2: World.Water,
            3: World.Sand,
            4: World.Terrain,
            255: World.ShiningBlock
        }

        self.CHUNK_SIZE = 32
        self.chunks_count = chunks_count
        self.chunks = [[None] * chunks_count[0] for i in range(chunks_count[1])]

    def is_rectangles_overlap(self, R1, R2):
        if (R1[0]>=R2[2]) or (R1[2]<=R2[0]) or (R1[3]<=R2[1]) or (R1[1]>=R2[3]):
            return False
        return True

    def render(self, canvas, offset, visible_area):
        for i, chunk_row in enumerate(self.chunks):
            for j, chunk in enumerate(chunk_row):
                chunk_area = (
                    i * 64 * self.CHUNK_SIZE,
                    j * 64 * self.CHUNK_SIZE,
                    (i + 1) * 64 * self.CHUNK_SIZE,
                    (j + 1) * 64 * self.CHUNK_SIZE
                )

                if self.is_rectangles_overlap(chunk_area, visible_area):
                    for row in chunk:
                        for block in row:
                            block.render(canvas, offset, self.CHUNK_SIZE)

    def save(self):
        pass

    def load(self):
        pass

    def to_binary(self):
        binary_chanks = [[None] * self.chunks_count[0] for i in range(self.chunks_count[1])]
        for i in range(self.chunks_count[0]):
            for j in range(self.chunks_count[1]):
                binary_chanks[i][j] = [[None] * self.CHUNK_SIZE for k in range(self.CHUNK_SIZE)]

        for i in range(self.chunks_count[0]):
            for j in range(self.chunks_count[1]):
                for n in range(self.CHUNK_SIZE):
                    for m in range(self.CHUNK_SIZE):
                        binary_chanks[i][j][n][m] = self.chunks[i][j][n][m].get_data()

        return pickle.dumps((self.chunks_count, binary_chanks))
    
    def from_binary(self, data):
        self.chunks_count, binary_chunks = pickle.loads(data)
        print(self.chunks_count)

        self.chunks = [[None] * self.chunks_count[0] for i in range(self.chunks_count[1])]

        def restore_chunk(i, j):
            self.chunks[i][j] = [[None] * self.CHUNK_SIZE for k in range(self.CHUNK_SIZE)]
            for n in range(self.CHUNK_SIZE):
                    for m in range(self.CHUNK_SIZE):
                        self.chunks[i][j][n][m] = self.id_dict[binary_chunks[i][j][n][m][0]](
                            binary_chunks[i][j][n][m][1],
                            binary_chunks[i][j][n][m][2]
                        )
        
        threads = []

        for i in range(self.chunks_count[0]):
            for j in range(self.chunks_count[1]):
                threads.append(threading.Thread(target=restore_chunk, args=(i, j)))
                threads[-1].start()

        for thread in threads:
            thread.join()
