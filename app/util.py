import struct

from enum import Enum
from app.state.player.resource import Player
import app.config as config


class UDPOp(Enum):
    REGISTER_CLIENT = 0
    STATE_UPDATE = 1


PACKET_SIZE = {
    Player.RESOURCE_TYPE_BYTE: Player.RESOURCE_PACKET_SIZE
}


def prepare_update_packet(buffer, sender_id, resources):
    # buffer[0] - UDP operation
    buffer[0] = UDPOp.STATE_UPDATE.value

    # buffer[1-4] - sender id
    struct.pack_into(config.ENDIAN + 'I', buffer, 1, int(sender_id))

    # buffer[9+] - resources
    idx = 9
    for resource in resources:
        resource.write_bytes(buffer, idx)
        idx += resource.RESOURCE_PACKET_SIZE

    # buffer[5-8] - resource byte length
    struct.pack_into(config.ENDIAN + 'I', buffer, 0, idx)


def unpack_update(buffer, resource_map):
    udp_op = buffer[0]
    sender_id = struct.unpack_from(config.ENDIAN + 'I', buffer, 1)[0]
    size = struct.unpack_from(config.ENDIAN + 'I', buffer, 5)[0]

    idx = 9
    while idx < size:
        type = buffer[idx]
        resource_id = struct.unpack_from(config.ENDIAN + 'I', buffer, idx+1)[0]
        print("[{}:{}]".format(type, resource_id), end='', flush=True)
        resource_map[resource_id] = buffer[idx : idx+PACKET_SIZE[type]]

    return udp_op, sender_id, size