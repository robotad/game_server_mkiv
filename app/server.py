import asyncio
import socket
import struct
import time

import app.config as config
from app.util import UDPOp

log = config.log

if config.DEV_IS_LOCAL_DOCKER:
    DOCKER_HOST_IP = socket.gethostbyname('host.docker.internal')
    log.info("Docker host ip={}".format(DOCKER_HOST_IP))


class UdpReaderProtocol(asyncio.DatagramProtocol):
    def __init__(self, data_in_q, server, is_profiling):
        self._data_in_q = data_in_q
        self._server = server
        self._is_profiling = is_profiling
        log.info("[*] Server-udp: ready")

    def connection_made(self, transport):
        self._server._transport = transport

    def datagram_received(self, data, addr):
        udp_op = data[0]

        if udp_op == UDPOp.REGISTER_CLIENT.value:
            client_id = str(struct.unpack('<I', data[1:5])[0])
            port = int.from_bytes(data[5:9], byteorder='little')

            if config.DEV_IS_LOCAL_DOCKER:
                addr = (DOCKER_HOST_IP, port)
            else:
                addr = (addr[0], port)

            self._server._clients.append(addr)
            if self._is_profiling:
                print("[+1]", end='', flush=True)
            else:
                log.info("[*] Server: registered client(addr={})".format(addr))

        else:
            if self._is_profiling:
                print("-", end='', flush=True)
            self._data_in_q.put_nowait(data)


class Server:
    BROADCAST_INTERVAL = 0.010
    BUFFER_SIZE = 1024          # Note: if this is too big, client won't receive
    PROFILE_BUFFER_Y = 1
    PROFILE_SEND_Y = 2

    def __init__(self, data_in_q, is_profiling):
        self._transport = None
        self._data_in_q = data_in_q
        self._clients = []
        self._buffer = bytearray(Server.BUFFER_SIZE)
        self._buffer_view = memoryview(self._buffer)
        self._t_sent = time.process_time()
        self._d_send = 0

        self._is_profiling = is_profiling
        self._profile_log = ""

    def _process_incoming(self):
        idx = 0
        while not self._data_in_q.empty():
            if self._is_profiling:
                print("o", end='', flush=True)
            data = self._data_in_q.get_nowait()
            try:
                self._buffer_view[idx:idx+len(data)] = data
            except Exception as e:
                log.error("[x] Error: rtype={}, idx={}".format(type(data), idx), e)
            idx += len(data)

    async def process_outgoing(self):
        while True:
            await asyncio.sleep(0)
            # await asyncio.sleep(Server.BROADCAST_INTERVAL - ((time.process_time() - self._t_sent) + self._d_send))
            self._process_incoming()
            t_start = time.process_time()
            for client_addr in self._clients:
                if self._is_profiling:
                    print("#", end='', flush=True)
                self._transport.sendto(self._buffer, client_addr)
                await asyncio.sleep(0)
            self._d_send = time.process_time() - t_start
            self._t_sent = time.process_time()


loop = asyncio.get_event_loop()
data_in_q = asyncio.Queue()
server = Server(data_in_q, config.DEV_PROFILE)
coro = loop.create_datagram_endpoint(
    protocol_factory=lambda: UdpReaderProtocol(data_in_q, server, config.DEV_PROFILE),
    local_addr=(config.UDP_EXTERNAL_HOST, config.UDP_RECV_PORT),
)

# loop.create_task(server.process_incoming())
loop.create_task(server.process_outgoing())

transport, protocol = loop.run_until_complete(coro)
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    transport.close()
    loop.close()
