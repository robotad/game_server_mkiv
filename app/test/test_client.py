import asyncio
import struct
import time

import app.config as config
import app.util as util
from app.state.resource import Resource
from app.state.player.resource import Player

UDP_ADDRESS=("127.0.0.1", 5002)

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
TEST_ITERATIONS=1

LOG_VISUAL=True


class ClientReaderProtocol(asyncio.DatagramProtocol):
    def __init__(self, client):
        self._client = client
        print("[*] client({}) ready ...".format(self._client._id))

    def connection_made(self, transport):
        self._client._transport = transport

    def datagram_received(self, data, addr):
        self._client.receive(data)


class Client:
    def __init__(self, id, port):
        self._id = id
        self._port = port
        self._transport = None

        self._t_send = None
        self._t_recv = None

        self.sample_packet = bytearray(1 + 4 + 4 + Player.RESOURCE_PACKET_SIZE)
        player = Player(id=self._id,
                        health=0,
                        x=1,y=2,z=3)
        util.prepare_update_packet(self.sample_packet, self._id, resource_list=[player])
        self._recv_q = asyncio.Queue()

    def register_client(self):
        packet = bytearray(9)
        packet[0] = util.UDPOp.REGISTER_CLIENT.value
        struct.pack_into('<i', packet, 1, int(self._id))
        struct.pack_into('<i', packet, 5, int(self._port))
        self._transport.sendto(packet, UDP_ADDRESS)
        print("[*] client({}) sent register data(size='{}') to address='{}'".format(self._id, len(packet), UDP_ADDRESS))

    def send_state_update(self, iteration):
        # Put iteration into the player health field
        struct.pack_into(config.ENDIAN + 'I', self.sample_packet, util.PACKET_RESOURCE_START_INDEX + Player.PACKET_HEALTH_INDEX, int(iteration))
        print("{} ".format(self._id))

        if LOG_VISUAL:
            print(self._id, end='', flush=True)
        self._transport.sendto(self.sample_packet, UDP_ADDRESS)
        self._t_send = time.process_time()

    def receive(self, data):
        if LOG_VISUAL:
            print(config.TEXT_CYAN + str(self._id) + config.TEXT_ENDC + " ", end='', flush=True)
        self._recv_q.put_nowait(data)

    def is_received(self, iteration):
        resource_map = {}
        if not self._recv_q.empty():
            idx = 0
            while not self._recv_q.empty():
                data = self._recv_q.get_nowait()
                util.unpack_update(data, resource_map)
                idx += 1

                if self._id in resource_map:
                    health = struct.unpack_from(config.ENDIAN + 'I', resource_map[self._id], Player.PACKET_HEALTH_INDEX)[0]
                    if health == iteration:
                        print(config.TEXT_BLUE + "{}[{}]".format(self._id, idx) + config.TEXT_ENDC + " ", end='', flush=True)
                        return True
        return False


loop = asyncio.get_event_loop()


clients = []
start_client_count = 0
max_clients = 1


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
        clients.append(client)
        time.sleep(.2)


async def send_updates(iteration):
    for client in clients:
        client.send_state_update(iteration)
        await asyncio.sleep(0)


async def test_iterations(n_iterations):
    # Test that all clients receive updates at a reasonable
    # time.
    total_misses = 0
    for i in range(0, n_iterations):
        await send_updates(i)
        await asyncio.sleep(0.010)

        for client in clients:
            if not client.is_received(i):
                total_misses += 1

        if total_misses > 0:
            print((config.TEXT_RED + "{} miss(es)." + config.TEXT_ENDC).format(total_misses), flush=True)
        else:
            print("")

    if total_misses/n_iterations > TEST_MISS_TOLERANCE:
        print((config.TEXT_RED + "{}% missed." + config.TEXT_ENDC).format((total_misses/n_iterations)*100), flush=True)
        return False
    else:
        print("{}% missed, OK.".format((total_misses/n_iterations)*100), flush=True)
        return True


def normal_test():
    while True:
        # Run this test until we have successfully
        # added up to the max number of clients and
        # updates are st
        if len(clients) > max_clients:
            break

        add_clients(1)
        if len(clients) >= start_client_count:
            if not loop.run_until_complete(test_iterations(TEST_ITERATIONS)):
                print("[x] Error: test failed.")
                return


# def perf_test():
#     while True:
#         test_iterations(10000, .010, 10000, 0.015)
#
#
add_clients(start_client_count)
normal_test()
# # perf_test()
