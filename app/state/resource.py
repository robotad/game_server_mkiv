import struct
from app.config import ENDIAN

class Resource:
    @staticmethod
    def id_from_bytes(resource_bytes):
        """
        bytes 0-3 identify the resource
        :param resource_bytes:
        :return:
        """
        return struct.unpack(ENDIAN + 'I', resource_bytes[0:4])[0]

    @staticmethod
    def byte_size(resource_bytes):
        """
        bytes 4-5 is the size
        :param resource_bytes:
        :return:
        """
        return struct.unpack(ENDIAN + 'H', resource_bytes[4:6])[0]