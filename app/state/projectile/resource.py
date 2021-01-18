import struct
import app.config as config
from app.state.resource import Resource


class Projectile(Resource):
    RESOURCE_TYPE = 'projectile'
    RESOURCE_TYPE_BYTE = 1
    RESOURCE_PACKET_SIZE = 29

    PACKET_X_INDEX = 5
    PACKET_Y_INDEX = 9
    PACKET_Z_INDEX = 13
    PACKET_VELOCITY_X_INDEX = 17
    PACKET_VELOCITY_Y_INDEX = 21
    PACKET_VELOCITY_Z_INDEX = 25

    def __init__(self, id, x, y, z, velocity_x, velocity_y, velocity_z):
        self.id = id
        self.x = x
        self.y = y
        self.z = z
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.velocity_z = velocity_z

    def write_bytes(self, packet, offset):
        packet[offset+Resource.PACKET_RESOURCE_TYPE_INDEX]= Projectile.RESOURCE_TYPE_BYTE
        struct.pack_into(config.ENDIAN + 'I', packet, offset + Resource.PACKET_ID_INDEX, int(self.id))
        struct.pack_into(config.ENDIAN + 'f', packet, offset + Projectile.PACKET_X_INDEX, float(self.x))
        struct.pack_into(config.ENDIAN + 'f', packet, offset + Projectile.PACKET_Y_INDEX, float(self.y))
        struct.pack_into(config.ENDIAN + 'f', packet, offset + Projectile.PACKET_Z_INDEX, float(self.z))
        struct.pack_into(config.ENDIAN + 'f', packet, offset + Projectile.PACKET_VELOCITY_X_INDEX, float(self.velocity_x))
        struct.pack_into(config.ENDIAN + 'f', packet, offset + Projectile.PACKET_VELOCITY_Y_INDEX, float(self.velocity_y))
        struct.pack_into(config.ENDIAN + 'f', packet, offset + Projectile.PACKET_VELOCITY_Z_INDEX, float(self.velocity_y))
        return packet
