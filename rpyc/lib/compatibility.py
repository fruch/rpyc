"""
library with compatibility with Python 2.4
"""

try:
    from struct import Struct
except ImportError:
    import struct
    class Struct(object):
        __slots__ = ["format", "size"]

        def __init__(self, format):
            self.format = format
            self.size = struct.calcsize(format)

        def pack(self, *args):
            return struct.pack(self.format, *args)

        def unpack(self, data):
            return struct.unpack(self.format, data)

try:
    all = all
except NameError:
    def all(seq):
        for elem in seq:
            if not elem:
                return False
        return True

class MissingModule(object):
    __slots__ = ["__name"]

    def __init__(self, name):
        self.__name = name

    def __getattr__(self, name):
        raise ImportError("module %r not found" % (self.__name,))

def safe_import(name):
    try:
        mod = __import__(name, None, None, "*")
    except ImportError:
        mod = MissingModule(name)
    return mod
