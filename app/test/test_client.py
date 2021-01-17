import multiprocessing
import socket
import struct
import threading
import time

import app.util as util
import app.config as config
from app.state.player.resource import Player

UDP_ADDRESS=("127.0.0.1", 5002)

# Test that all clients receive updates in approximately
# TEST_RECEIVE_TOLERANCE (the time in seconds). Failures here
# mean clients would *not* get timeley updates from the server

TEST_RECEIVE_PAUSE=1.0          # Seconds to wait after send to check
                                # how long it took to receive. It is long enough
                                # to receive all data, the clients themselves will factor
                                # out data that came in too late
TEST_RATE_TOLERANCE=0.015       # The test will fail if a client did not
                                # receive an update in *approximately* this
                                # rate in seconds per update
TEST_MISS_TOLERANCE=2.5/100     # Number of rounds where clients do not receive
                                # before we fail per test iteration
TEST_ITERATIONS=2

clients = []
START_CLIENT_COUNT = 30
MAX_CLIENTS = 30

LOG_VISUAL=True


class TestClient:
    def __init__(self, id, port):
        self._id = id
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port = port
        self.sock.bind(('0.0.0.0', self.port))

        self._t_send = None
        self._recv_q = multiprocessing.Queue()

        self.sample_packet = bytearray(1 + 4 + 4 + Player.RESOURCE_PACKET_SIZE)
        player = Player(id=self._id,
                        health=0,
                        x=1,y=2,z=3)
        util.prepare_update_packet(self.sample_packet, self._id, resource_list=[player])

    def register_client(self):
        packet = bytearray(9)
        packet[0] = util.UDPOp.REGISTER_CLIENT.value
        struct.pack_into('<i', packet, 1, int(self._id))
        struct.pack_into('<i', packet, 5, int(self.port))
        self.sock.sendto(packet, UDP_ADDRESS)
        print("[*] client({}) sent register data(size='{}') to address='{}'".format(self._id, len(packet), UDP_ADDRESS))

    def send_state_update(self, iteration):
        # Put iteration into the player health field
        struct.pack_into(config.ENDIAN + 'I', self.sample_packet, util.PACKET_RESOURCE_START_INDEX + Player.PACKET_HEALTH_INDEX, int(iteration))
        if LOG_VISUAL:
            print("{} ".format(self._id), end='', flush=True)
        self.sock.sendto(self.sample_packet, UDP_ADDRESS)
        self._t_send = time.process_time()

    def start_receive(self):
        th = threading.Thread(target=self._start_receive)
        th.daemon = True
        th.start()

    def _start_receive(self):
        """
        Begin receiving UDP packets
        :return:
        """
        try:
            while True:
                if LOG_VISUAL:
                    print(config.TEXT_CYAN + "{} ".format(self._id) + config.TEXT_ENDC, end='', flush=True)
                data, client_address = self.sock.recvfrom(4096)
                self._recv_q.put_nowait((data, time.process_time()))
        except Exception as ex:
            print("[x] UDP: Error receiving from client:", ex)

    def is_received(self, n_clients, iteration):
        resource_map = {}
        if not self._recv_q.empty():
            # Start unpacking the update and putting the
            # results into the resource map for analysis
            while not self._recv_q.empty():
                data, t_recv = self._recv_q.get_nowait()
                if (t_recv - self._t_send) > TEST_RATE_TOLERANCE:
                    break
                util.unpack_update(data, resource_map)

            # Check how many successes we have. A success means
            # that every client has received every other client's
            # update for this iteration
            n_successes = 0
            for client_id in resource_map.keys():
                # Check the 'health' field for every client. The value should
                # equal the value of the current iteration
                health = struct.unpack_from(config.ENDIAN + 'I', resource_map[client_id], Player.PACKET_HEALTH_INDEX)[0]
                if health == iteration:
                    n_successes += 1

            print(str(self._id) + config.TEXT_BLUE + ":{:.2f}".format(n_successes/n_clients) + config.TEXT_ENDC, end='', flush=True)

            if n_successes == n_clients:
                return True

        return False


def add_clients(count):
    for i in range(0, count):
        # Add another client
        client = TestClient(len(clients), 8000 + len(clients))
        client.start_receive()

        # Double attempt to register client, just
        # in case.
        client.register_client()
        time.sleep(.01)
        client.register_client()

        clients.append(client)
        time.sleep(.2)


def test_iterations(n_iterations, pause_time, n_allowed_misses, allowed_rate):
    # Test that all clients receive updates at a reasonable
    # time.
    misses = 0
    for i in range(0, n_iterations):
        print("[{}]".format(i), end='')
        for client in clients:
            client.send_state_update(i)

        time.sleep(pause_time)
        for client in clients:
            if not client.is_received(len(clients), i):
                misses += 1
        print(config.TEXT_RED + str(misses) + config.TEXT_ENDC)


def normal_test():
    while True:
        # Run this test until we have successfully
        # added up to the max number of clients and
        # updates are st
        if len(clients) > MAX_CLIENTS:
            break

        add_clients(1)
        if len(clients) >= START_CLIENT_COUNT:
            test_iterations(TEST_ITERATIONS, TEST_RECEIVE_PAUSE, TEST_MISS_TOLERANCE, TEST_RATE_TOLERANCE)


def perf_test():
    while True:
        test_iterations(10000, .010, 10000, 0.015)


add_clients(START_CLIENT_COUNT)
normal_test()
# perf_test()