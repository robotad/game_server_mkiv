import asyncio
import struct
import time

from app.util import UDPOp
from app.state.player.resource import Player

UDP_ADDRESS=("127.0.0.1", 5002)
OKGREEN = '\033[92m'
ENDC = '\033[0m'


class ClientReaderProtocol(asyncio.DatagramProtocol):
    def __init__(self, client):
        self._client = client
        print("[*] client({}) ready ...".format(self._client._id))

    def connection_made(self, transport):
        self._client._transport = transport

    def datagram_received(self, data, addr):
        self._client.receive()


class Client:
    def __init__(self, id, port):
        self._id = id
        self._port = port
        self._transport = None
        self._receive_count = 0

        self.sample_packet = bytearray(1 + 4 + Player.RESOURCE_PACKET_SIZE)
        self.sample_packet[0] = UDPOp.STATE_UPDATE.value
        struct.pack_into('<i', self.sample_packet, 1, int(self._id))

    def register_client(self):
        packet = bytearray(9)
        packet[0] = UDPOp.REGISTER_CLIENT.value
        struct.pack_into('<i', packet, 1, int(self._id))
        struct.pack_into('<i', packet, 5, int(self._port))
        self._transport.sendto(packet, UDP_ADDRESS)
        print("[*] client({}) sent register data(size='{}') to address='{}'".format(self._id, len(packet), UDP_ADDRESS))

    def send_state_update(self):
        print(self._id, end='', flush=True)
        self._transport.sendto(self.sample_packet, UDP_ADDRESS)

    def receive(self):
        print(OKGREEN + str(self._id) + ENDC, end='', flush=True)
        self._receive_count += 1

    def pop_stats(self):
        count = self._receive_count
        self._receive_count = 0
        return count


loop = asyncio.get_event_loop()


# Test that all clients receive updates in approximately
# TEST_RECEIVE_TOLERANCE (the time in seconds). Failures here
# mean clients would *not* get timeley updates from the server

TEST_RECEIVE_PAUSE=0.010        # Seconds to wait after send to check
                                # how long it took to receive. It is low, to
                                # simulate getting constant updates from clients
TEST_RATE_TOLERANCE=0.015       # The test will fail if a client did not
                                # receive an update in *approximately* this
                                # rate in seconds per update
TEST_MISS_TOLERANCE=2.5/100     # Number of rounds where clients do not receive
                                # before we fail per test iteration
TEST_ITERATIONS=500

clients = []
start_client_count = 10
max_clients = 80


def add_clients(count):
    n = len(clients)
    for i in range(n, n+count):
        # Add another client
        port = 8000 + len(clients)
        client = Client(i, port)
        coro = loop.create_datagram_endpoint(
                protocol_factory=lambda: ClientReaderProtocol(client),
                local_addr=('0.0.0.0', port))
        loop.run_until_complete(coro)

        # Double attempt to register client, just
        # in case.
        client.register_client()
        client.register_client()

        clients.append(client)
        time.sleep(.2)


async def send_updates():
    for client in clients:
        client.send_state_update()
        await asyncio.sleep(0)
    return True


def test_iterations(n_iterations, pause_time):
    # Test that all clients receive updates at a reasonable
    # time.
    for i in range(0, n_iterations):
        loop.run_until_complete(send_updates())
        time.sleep(pause_time)

        results = []
        for client in clients:
            count = client.pop_stats()
            results.append(count)

        print("{}".format(results), flush=True)


def normal_test():
    while True:
        # Run this test until we have successfully
        # added up to the max number of clients and
        # updates are st
        if len(clients) > max_clients:
            break

        add_clients(1)
        if len(clients) >= start_client_count:
            test_iterations(TEST_ITERATIONS, TEST_RECEIVE_PAUSE)


# def perf_test():
#     while True:
#         test_iterations(10000, .010, 10000, 0.015)
#
#
add_clients(start_client_count)
normal_test()
# # perf_test()
loop.run_forever()
