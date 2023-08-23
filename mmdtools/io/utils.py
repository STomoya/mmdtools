
import struct



class FileStream:
    def __init__(self, path, mode) -> None:
        assert 'b' in mode, f'Only binary read/write mode is supported.'
        self._path = path
        self._mode = mode
        self._fp = None


    @property
    def path(self) -> str:
        return self._path


    def __enter__(self) -> 'FileStream':
        self._fp = open(self._path, self._mode)
        return self


    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


    def close(self):
        if self._fp is not None:
            self._fp.close()
            self._fp = None


class FileReadStream(FileStream):
    def __init__(self, path) -> None:
        super().__init__(path=path, mode='rb')


    """reading methods"""

    def read_int(self):
        """read signed integer"""
        return struct.unpack('<i', self._fp.read(4))[0]

    def read_uint(self):
        """read unsigned integer"""
        return struct.unpack('<I', self._fp.read(4))[0]

    def read_short(self):
        """read signed short"""
        return struct.unpack('<h', self._fp.read(2))[0]

    def read_ushort(self):
        """read unsigned short"""
        return struct.unpack('<H', self._fp.read(2))[0]

    def read_long(self):
        """read long"""
        return struct.unpack('<l', self._fp.read(4))[0]

    def read_ulong(self):
        """read long"""
        return struct.unpack('<L', self._fp.read(4))[0]

    def read_chars(self, length: int=1):
        return struct.unpack(f'<{length}s', self._fp.read(length))[0]

    def read_float(self):
        """read signed float"""
        return struct.unpack('<f', self._fp.read(4))[0]

    def read_vector(self, size):
        """read multiple floats and return as tuple"""
        return struct.unpack('<' + 'f' * size, self._fp.read(4 * size))

    def read_vector_3d(self):
        """read three floats"""
        return self.read_vector(3)

    def read_vector_4d(self):
        """read four floats"""
        return self.read_vector(4)

    def read_byte(self):
        """read signed byte"""
        return struct.unpack('<b', self._fp.read(1))[0]

    def read_ubyte(self):
        """read unsigned byte"""
        return struct.unpack('<B', self._fp.read(1))[0]

    def read_bytes(self, size):
        """read mutiple bytes"""
        return self._fp.read(size)

    def read_rest(self):
        return self._fp.read()


def crop_byte_string(string: bytes, pattern: bytes):
    return string.split(pattern)[0]


def parse_flags(flag, max_flags):
    parsed_flags = []
    for shift in range(max_flags):
        parsed_flags.append(bool(flag & (1 << shift)))
    return parsed_flags
