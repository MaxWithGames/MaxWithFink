import socket
import struct
import zlib
import math

COMPRESSION_TRESHOLD = 1048576

def sendall(s: socket.socket, data):
    if len(data) > COMPRESSION_TRESHOLD:
        data = zlib.compress(data)
    msg_length = len(data)
    # print(msg_length)
    s.send(struct.pack('!i', msg_length))
    s.send(data)

def recvall(s: socket.socket):
    msg_length = s.recv(4)
    if len(msg_length) == 0:
        return None
    msg_length = struct.unpack('!i', msg_length)[0]
    buf = b''
    chunk_size = 2 ** max(16, int(math.log(msg_length, 2)))
    while len(buf) < msg_length:
        buf += s.recv(chunk_size)
        # print(len(buf))
    if msg_length > COMPRESSION_TRESHOLD:
        return zlib.decompress(buf)
    return buf