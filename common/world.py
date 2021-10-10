from abc import abstractmethod
import threading
import pygame
import random
import cloudpickle as pickle

class World():
    class BaseBlock():
        def __init__(self, pos, data=None) -> None:
            # pos = (chunk_x, chunk_y, x, y)
            self.pos = pos
            self.data = data
        
        @abstractmethod
        def render(self, canvas):
            pass

        def get_id(self):
            return 0

        def get_data(self):
            return self.get_id(), self.pos, self.data

    class SimpleBlock(BaseBlock):
        # data = color
        def render(self, canvas, offset, chunk_size):
            dx, dy = offset
            px = self.pos[0] * 64 * chunk_size + self.pos[2] * 64 + dx
            py = self.pos[1] * 64 * chunk_size + self.pos[3] * 64 + dy

            pygame.draw.rect(canvas, self.data, (px, py, 64, 64))
        
        def get_id(self):
            return 1

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

    def get_new_block_buy_id(self, id, pos, data=None):
        return self.id_dict[id]

    def __init__(self, chunks_count=(0, 0)):
        
        self.id_dict = {
            0: World.BaseBlock,
            1: World.SimpleBlock 
        }

        self.CHUNK_SIZE = 32
        self.chunks_count = chunks_count
        self.chunks = [[None] * chunks_count[0] for i in range(chunks_count[1])]

    def is_rectangles_overlap(self, R1, R2):
        if (R1[0]>=R2[2]) or (R1[2]<=R2[0]) or (R1[3]<=R2[1]) or (R1[1]>=R2[3]):
            return False
        return True

    def render(self, canvas, offset, visible_area):
        for i in range(self.chunks_count[0]):
            for j in range(self.chunks_count[1]):
                chunk_area = (
                    i * 64 * self.CHUNK_SIZE,
                    j * 64 * self.CHUNK_SIZE,
                    (i + 1) * 64 * self.CHUNK_SIZE,
                    (j + 1) * 64 * self.CHUNK_SIZE
                )

                if self.is_rectangles_overlap(chunk_area, visible_area):
                    curr_chunk = self.chunks[i][j]
                    for row in curr_chunk:
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
