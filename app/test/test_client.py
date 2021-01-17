import socket
import struct
import threading
import time

from app.util import UDPOp
from app.state.player.resource import Player

UDP_ADDRESS=("127.0.0.1", 5002)


class TestClient:
    def __init__(self, id, port):
        self.id = id
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port = port
        self.sock.bind(('0.0.0.0', self.port))

        self.stat_lock = threading.Lock()
        self.send_time = None
        self.receive_time = None
        self.receive_count = 0
        self.receive_size = 0

        self.sample_packet = bytearray(1 + 4 + Player.RESOURCE_PACKET_SIZE)
        self.sample_packet[0] = UDPOp.STATE_UPDATE.value
        struct.pack_into('<i', self.sample_packet, 1, int(self.id))

    def register_client(self):
        packet = bytearray(9)
        packet[0] = UDPOp.REGISTER_CLIENT.value
        struct.pack_into('<i', packet, 1, int(self.id))
        struct.pack_into('<i', packet, 5, int(self.port))
        self.sock.sendto(packet, UDP_ADDRESS)
        print("[*] client({}) sent register data(size='{}') to address='{}'".format(self.id, len(packet), UDP_ADDRESS))

    def send_state_update(self):
        self.sock.sendto(self.sample_packet, UDP_ADDRESS)
        self.send_time = time.process_time()

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
            # print("[*] client({}), waiting".format(self.id))
            while True:
                data, client_address = self.sock.recvfrom(4096)
                with self.stat_lock:
                    self.receive_time = time.process_time()
                    self.receive_count += 1
                    self.receive_size += (len(data))
                    # print("[*] client({}), received size='{}'".format(self.id, len(data)))
        except Exception as ex:
            print("[x] UDP: Error receiving from client:", ex)

    def pop_stats(self):
        with self.stat_lock:
            stats = None
            if self.receive_count > 0:
                stats = (
                    self.receive_count,
                    self.receive_size/self.receive_count,
                    self.receive_time - self.send_time
                )
            self.receive_count = 0
            self.receive_size = 0
            self.receive_time = 0
            return stats


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
start_client_count = 50
max_clients = 80


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
    total_rate = 0
    total_size = 0
    total_count = 0
    stat_count = 0
    misses = 0

    for i in range(0, n_iterations):
        for client in clients:
            client.send_state_update()

        time.sleep(pause_time)

        for client in clients:
            stats = client.pop_stats()
            if stats is not None:
                total_count += stats[0]
                total_size += stats[1]
                total_rate += stats[2]
                stat_count += 1
            else:
                misses += 1

    if stat_count > 0:
        assert (total_rate / stat_count) < allowed_rate

    if (misses/total_count) >= n_allowed_misses:
        print("[x] Error,  clients missed too many packets, misses={}/{} ({}%)!".format(
            misses, total_count, ((misses/total_count)*100)))
        exit(1)

    if stat_count > 0:
        print("[ ] client count='{}', ave_count={}, ave_size={}, average rate={} sec/update | miss_rate={}%"
              .format(len(clients), (total_count / stat_count), (total_size / stat_count),
                      (total_rate / stat_count), (misses/total_count)*100))
    else:
        print("[ ] client count='{}', all missed!"
              .format(len(clients)))


def normal_test():
    while True:
        # Run this test until we have successfully
        # added up to the max number of clients and
        # updates are st
        if len(clients) > max_clients:
            break

        add_clients(1)
        if len(clients) >= start_client_count:
            test_iterations(TEST_ITERATIONS, TEST_RECEIVE_PAUSE, TEST_MISS_TOLERANCE, TEST_RATE_TOLERANCE)


def perf_test():
    while True:
        test_iterations(10000, .010, 10000, 0.015)


add_clients(start_client_count)
normal_test()
# perf_test()