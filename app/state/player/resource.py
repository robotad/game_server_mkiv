import struct
import app.config as config
from app.state.resource import Resource


class Player(Resource):
    RESOURCE_TYPE = 'player'
    RESOURCE_TYPE_BYTE = 0
    RESOURCE_PACKET_SIZE = 21

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
        health = struct.unpack(config.ENDIAN + 'I', bytes_data[5:9])[0]
        x = struct.unpack(config.ENDIAN + 'f', bytes_data[9:13])[0]
        y = struct.unpack(config.ENDIAN + 'f', bytes_data[13:17])[0]
        z = struct.unpack(config.ENDIAN + 'f', bytes_data[17:21])[0]
        return Player(id, health, x, y, z)

    def write_bytes(self, packet, offset):
        packet[offset]= Player.RESOURCE_TYPE_BYTE
        struct.pack_into(config.ENDIAN + 'I', packet, offset + 1, int(self.id))
        struct.pack_into(config.ENDIAN + 'I', packet, offset + 5, int(self.heath))
        struct.pack_into(config.ENDIAN + 'f', packet, offset + 9, float(self.x))
        struct.pack_into(config.ENDIAN + 'f', packet, offset + 13, float(self.y))
        struct.pack_into(config.ENDIAN + 'f', packet, offset + 17, float(self.z))
        return packet
