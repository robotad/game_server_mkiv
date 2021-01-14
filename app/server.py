import asyncio
import socket
import struct

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
    def __init__(self):
        self._transport = None
        self._clients = []
        self.profile_count = 0
        self.profile_interval = 500

    def broadcast(self, data):
        self.profile_count += 1
        for client_addr in self._clients:
            self._transport.sendto(data, client_addr)

loop = asyncio.get_event_loop()
data_in_q = asyncio.Queue()
server = Server()
coro = loop.create_datagram_endpoint(
    protocol_factory=lambda: UdpReaderProtocol(data_in_q, server),
    local_addr=(config.UDP_EXTERNAL_HOST, config.UDP_RECV_PORT),
)

log.info("[     ] Server: starting...")
transport, protocol = loop.run_until_complete(coro)


try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    transport.close()
    loop.close()
