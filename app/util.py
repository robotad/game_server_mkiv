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


def prepare_update_packet(buffer, sender_id, resource_list=None, resource_byte_map=None):
    # buffer[0] - UDP operation
    buffer[0] = UDPOp.STATE_UPDATE.value

    # buffer[1-4] - sender id
    struct.pack_into(config.ENDIAN + 'I', buffer, 1, int(sender_id))

    # buffer[9+] - resources
    idx = 9
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
    struct.pack_into(config.ENDIAN + 'I', buffer, 5, idx)


def unpack_update(buffer, resource_map):
    udp_op = buffer[0]
    sender_id = struct.unpack_from(config.ENDIAN + 'I', buffer, 1)[0]
    size = struct.unpack_from(config.ENDIAN + 'I', buffer, 5)[0]

    idx = 9
    while idx < size:
        type = buffer[idx]
        size = PACKET_SIZE[type]
        resource_id = struct.unpack_from(config.ENDIAN + 'I', buffer, idx+1)[0]
        print("udp_op={}, sender_id={}, size={}, resource_id={}".format(udp_op, sender_id, size, resource_id))
        resource_map[resource_id] = buffer[idx : idx+size]
        idx += size

    return udp_op, sender_id, size