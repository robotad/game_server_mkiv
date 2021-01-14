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
    def __init__(self, data_in_q, server):
        self._data_in_q = data_in_q
        self._server = server
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
            log.info("[*    ] Server: registered client.".format(data))

        else:
            self._data_in_q.put_nowait(data)


class Server:
    BROADCAST_INTERVAL = 0.010

    def __init__(self, data_in_q):
        self._transport = None
        self._data_in_q = data_in_q
        self._clients = []
        self._buffer = bytearray(1024)
        self._buffer_view = memoryview(self._buffer)
        self._t_sent = time.process_time()
        self._d_send = 0

    async def process(self):
        log.info("[ ] Server: starting...")
        while True:
            self._process_incoming()
            if not ((time.process_time() - self._t_sent) + self._d_send) < Server.BROADCAST_INTERVAL:
                self._process_outgoing()
            await asyncio.sleep(0)

    def _process_incoming(self):
        # log.info("[ ] Server: incoming ...")
        idx = 0
        while not self._data_in_q.empty():
            data = self._data_in_q.get_nowait()
            self._buffer_view[idx:idx+len(data)] = data
            idx += len(data)

    def _process_outgoing(self):
        # log.info("[ ] Server: outgoing ...")
        t_start = time.process_time()
        for client_addr in self._clients:
            self._transport.sendto(self._buffer, client_addr)
        self._d_send = time.process_time() - t_start
        self._t_sent = time.process_time()

loop = asyncio.get_event_loop()
data_in_q = asyncio.Queue()
server = Server(data_in_q)
coro = loop.create_datagram_endpoint(
    protocol_factory=lambda: UdpReaderProtocol(data_in_q, server),
    local_addr=(config.UDP_EXTERNAL_HOST, config.UDP_RECV_PORT),
)

loop.create_task(server.process())
transport, protocol = loop.run_until_complete(coro)
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    transport.close()
    loop.close()
