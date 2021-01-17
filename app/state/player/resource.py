import struct
import app.config as config
from app.state.resource import Resource


class Player(Resource):
    RESOURCE_TYPE = 'player'
    RESOURCE_TYPE_BYTE = 0
    RESOURCE_PACKET_SIZE = 21

    PACKET_HEALTH_INDEX         = 5
    PACKET_X_INDEX              = 9
    PACKET_Y_INDEX              = 13
    PACKET_Z_INDEX              = 17

    def __init__(self, id, health, x, y, z):
        self.id = id    # should match client_id
        self.heath = health
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        player_dict = {
            "type": Player.RESOURCE_TYPE_BYTE,
            "id": self.id,
            "health": self.heath,
            "x": self.x,
            "y": self.y,
            "z": self.z
        }
        return player_dict

    @staticmethod
    def from_bytes(bytes_data):
        id = Player.id_from_bytes(bytes_data)
        health = struct.unpack_from(config.ENDIAN + 'I', bytes_data, Player.PACKET_HEALTH_INDEX)[0]
        x = struct.unpack_from(config.ENDIAN + 'f', bytes_data, Player.PACKET_X_INDEX)[0]
        y = struct.unpack_from(config.ENDIAN + 'f', bytes_data, Player.PACKET_Y_INDEX)[0]
        z = struct.unpack_from(config.ENDIAN + 'f', bytes_data, Player.PACKET_Z_INDEX)[0]
        return Player(id, health, x, y, z)

    def write_bytes(self, packet, offset):
        packet[offset+Resource.PACKET_RESOURCE_TYPE_INDEX]= Player.RESOURCE_TYPE_BYTE
        struct.pack_into(config.ENDIAN + 'I', packet, offset + Resource.PACKET_ID_INDEX, int(self.id))
        struct.pack_into(config.ENDIAN + 'I', packet, offset + Player.PACKET_HEALTH_INDEX, int(self.heath))
        struct.pack_into(config.ENDIAN + 'f', packet, offset + Player.PACKET_X_INDEX, float(self.x))
        struct.pack_into(config.ENDIAN + 'f', packet, offset + Player.PACKET_Y_INDEX, float(self.y))
        struct.pack_into(config.ENDIAN + 'f', packet, offset + Player.PACKET_Z_INDEX, float(self.z))
        return packet
