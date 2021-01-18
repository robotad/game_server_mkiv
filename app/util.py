import struct

from enum import Enum
from app.state.player.resource import Player
from app.state.projectile.resource import Projectile
import app.config as config


class UDPOp(Enum):
    REGISTER_CLIENT = 0
    STATE_UPDATE = 1


PACKET_SIZE = {
    Player.RESOURCE_TYPE_BYTE: Player.RESOURCE_PACKET_SIZE,
    Projectile.RESOURCE_TYPE_BYTE: Projectile.RESOURCE_PACKET_SIZE
}


PACKET_UDPOP_INDEX          = 0
PACKET_SENDER_ID_INDEX      = 1
PACKET_SIZE_INDEX           = 5
PACKET_RESOURCE_START_INDEX = 9


def prepare_update_packet(buffer, sender_id, resource_list=None, resource_byte_map=None):
    # buffer[0] - UDP operation
    buffer[PACKET_UDPOP_INDEX] = UDPOp.STATE_UPDATE.value

    # buffer[1-4] - sender id
    struct.pack_into(config.ENDIAN + 'I', buffer, PACKET_SENDER_ID_INDEX, int(sender_id))

    # buffer[9+] - resources
    idx = PACKET_RESOURCE_START_INDEX
    if resource_list is not None:
        for resource in resource_list:
            resource.write_bytes(buffer, idx)
            idx += resource.RESOURCE_PACKET_SIZE
    elif resource_byte_map is not None:
        for resource_id in list(resource_byte_map.keys()):
            data = resource_byte_map[resource_id]
            buffer[idx:idx+len(data)] = data
            idx += len(data)

    # buffer[5-8] - resource byte length
    struct.pack_into(config.ENDIAN + 'I', buffer, PACKET_SIZE_INDEX, idx)
    return idx


def unpack_update(buffer, resource_map):
    udp_op = buffer[PACKET_UDPOP_INDEX]
    sender_id = struct.unpack_from(config.ENDIAN + 'I', buffer, PACKET_SENDER_ID_INDEX)[0]
    size = struct.unpack_from(config.ENDIAN + 'I', buffer, PACKET_SIZE_INDEX)[0]

    # print("[{}:".format(sender_id), end='')
    idx = PACKET_RESOURCE_START_INDEX
    while idx < size:
        type = buffer[idx]
        resource_size = PACKET_SIZE[type]
        resource_id = struct.unpack_from(config.ENDIAN + 'I', buffer, idx+1)[0]
        # print("{}".format(resource_id), end='', flush=True)
        resource_map[resource_id] = buffer[idx : idx+resource_size]
        idx += resource_size
    # print("]", end='')

    return udp_op, sender_id, size