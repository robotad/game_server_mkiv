import struct
from app.config import ENDIAN

class Resource:
    PACKET_RESOURCE_TYPE_INDEX  = 0
    PACKET_ID_INDEX             = 1

    @staticmethod
    def id_from_bytes(resource_bytes):
        """
        bytes 0-3 identify the resource
        :param resource_bytes:
        :return:
        """
        return struct.unpack_from(ENDIAN + 'I', resource_bytes, Resource.PACKET_ID_INDEX)[0]

    @staticmethod
    def byte_size(resource_bytes):
        """
        bytes 4-5 is the size
        :param resource_bytes:
        :return:
        """
        return struct.unpack(ENDIAN + 'H', resource_bytes[4:6])[0]