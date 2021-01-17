import asyncio
import socket
import struct
import time

import app.config as config
from app.state.resource import Resource
import app.util as util

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

        if udp_op == util.UDPOp.REGISTER_CLIENT.value:
            client_id = str(struct.unpack('<I', data[1:5])[0])
            port = int.from_bytes(data[5:9], byteorder='little')

            if config.DEV_IS_LOCAL_DOCKER:
                addr = (DOCKER_HOST_IP, port)
            else:
                addr = (addr[0], port)

            self._server._clients[client_id] = addr
            if self._is_profiling:
                print("+", end='', flush=True)
            else:
                log.info("[*] Server: registered client(addr={})".format(addr))

        else:
            if self._is_profiling:
                print("-", end='', flush=True)
            self._data_in_q.put_nowait(data)


class Server:
    BROADCAST_INTERVAL = 0.005
    BUFFER_SIZE = 1024          # Note: if this is too big, client won't receive
    PROFILE_BUFFER_Y = 1
    PROFILE_SEND_Y = 2

    def __init__(self, data_in_q, is_profiling):
        self._transport = None
        self._data_in_q = data_in_q
        self._clients = {}

        self._resource_map = {}

        self._buffer = bytearray(Server.BUFFER_SIZE)
        self._buffer_result = asyncio.Queue()
        self._buffer_view = memoryview(self._buffer)

        self._t_sent = time.process_time()
        self._d_send = 0

        self._is_profiling = is_profiling
        self._profile_log = ""

    def _data_to_buffer(self, data):
        if self._is_profiling:
            print("x", end='', flush=True)
        udp_op, sender_id, size = util.unpack_update(data, self._resource_map)
        if size > 0:
            result_size = util.prepare_update_packet(self._buffer_view, 0, resource_byte_map=self._resource_map)
            self._buffer_result.put_nowait(result_size)

    async def process_incoming(self):
        while True:
            # Wait for incoming data
            data = await self._data_in_q.get()
            if self._is_profiling:
                print(">", end='', flush=True)
            self._data_to_buffer(data)

    async def process_outgoing(self):
        while True:
            await self._buffer_result.get()
            client_ids = list(self._clients.keys())
            for client_id in client_ids:
                client_addr = self._clients[client_id]
                if self._is_profiling:
                    print(config.TEXT_GREEN + client_id + config.TEXT_ENDC, end='', flush=True)
                self._transport.sendto(self._buffer, client_addr)
                # print("[{}]".format(self._buffer[0:60]), end='')


loop = asyncio.get_event_loop()
data_in_q = asyncio.Queue()
server = Server(data_in_q, config.DEV_PROFILE)
coro = loop.create_datagram_endpoint(
    protocol_factory=lambda: UdpReaderProtocol(data_in_q, server, config.DEV_PROFILE),
    local_addr=(config.UDP_EXTERNAL_HOST, config.UDP_RECV_PORT),
)

loop.create_task(server.process_incoming())
loop.create_task(server.process_outgoing())

transport, protocol = loop.run_until_complete(coro)
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    transport.close()
    loop.close()
