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


class BufferBank:
    def __init__(self, buffer_size, count):
        self.buffer_empty_q = asyncio.Queue()
        for c in range(0, count):
            buffer = bytearray(buffer_size)
            buffer_view = memoryview(buffer)
            self.buffer_empty_q.put_nowait(buffer_view)
        self.buffer_ready_q = asyncio.Queue()

    def register_empty(self, buffer):
        self.buffer_empty_q.put_nowait(buffer)

    async def get_empty(self):
        return await self.buffer_empty_q.get()

    def register_ready(self, buffer, size):
        self.buffer_ready_q.put_nowait((buffer, size))

    async def get_ready(self):
        return await self.buffer_ready_q.get()


class Server:
    BROADCAST_INTERVAL = 0.005
    BUFFER_WARNING_SIZE = 2000
    BUFFER_SIZE = 3000          # Note: if this is too big, client won't receive
    PROFILE_BUFFER_Y = 1
    PROFILE_SEND_Y = 2

    def __init__(self, data_in_q, is_profiling):
        self._transport = None
        self._data_in_q = data_in_q
        self._clients = {}

        self._buffer_bank = BufferBank(buffer_size=Server.BUFFER_SIZE, count=4)

        self._t_sent = time.process_time()
        self._d_send = 0

        self._is_profiling = is_profiling
        self._profile_log = ""

    async def process_incoming(self):
        processed_size = 0
        resource_map = {}

        while True:
            # Wait for incoming data
            data = await self._data_in_q.get()
            if self._is_profiling:
                print(">", end='', flush=True)
            udp_op, sender_id, size = util.unpack_update(data, resource_map)
            processed_size += size

            await asyncio.sleep(0.001)

            if self._data_in_q.empty() or processed_size > Server.BUFFER_WARNING_SIZE:
                if processed_size > 0:
                    # Prepare the buffer and register as ready
                    # so process_outgoing() can use it.
                    buffer = await self._buffer_bank.get_empty()
                    packet_size = util.prepare_update_packet(buffer, 0, resource_byte_map=resource_map)
                    self._buffer_bank.register_ready(buffer, packet_size)

                    processed_size = 0
                    resource_map = {}

    async def process_outgoing(self):
        while True:
            buffer, size = await self._buffer_bank.get_ready()
            client_ids = list(self._clients.keys())
            for client_id in client_ids:
                client_addr = self._clients[client_id]
                if self._is_profiling:
                    print(config.TEXT_GREEN + "{} ".format(client_id) + config.TEXT_ENDC, end='', flush=True)
                self._transport.sendto(buffer[0:size], client_addr)
                await asyncio.sleep(0)
            self._buffer_bank.register_empty(buffer)


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
