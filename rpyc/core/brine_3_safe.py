"""
Orginial Version modified to python3

brine - a simple, fast and secure object serializer for immutable objects,
optimized for small integers [-48..160).
the following types are supported: int, long, bool, str, float, unicode, 
slice, complex, tuple(of simple types), forzenset(of simple types)
as well as the following singletons: None, NotImplemented, Ellipsis
"""

#ToDo, 
#
# convert to python3 
# python 3 does not support longs out, unicode standard, bytes in.

from cStringIO import StringIO

from rpyc.lib.compatibility import Struct, all

# singletons                               # Why no empty set
TAG_NONE = b"\x00"
TAG_EMPTY_STR = b"\x01"                     # Blank string
TAG_EMPTY_TUPLE = b"\x02"
TAG_TRUE = b"\x03"
TAG_FALSE = b"\x04"
TAG_NOT_IMPLEMENTED = b"\x05"
TAG_ELLIPSIS = b"\x06"

# types
TAG_UNICODE = b"\x08"
TAG_LONG = b"\x09"
TAG_STR1 = b"\x0a"                         # String length 1
TAG_STR2 = b"\x0b"                         # String length 2
TAG_STR3 = b"\x0c"                         # String length 3
TAG_STR4 = b"\x0d"                         # Sting length 4
TAG_STR_L1 = b"\x0e"                       # String length less than 256, uses I1 (byte)
TAG_STR_L4 = b"\x0f"                       # String length greater than 256, uses I4 (long)
TAG_TUP1 = b"\x10"
TAG_TUP2 = b"\x11"
TAG_TUP3 = b"\x12"
TAG_TUP4 = b"\x13"
TAG_TUP_L1 = b"\x14"
TAG_TUP_L4 = b"\x15"
TAG_INT_L1 = b"\x16"
TAG_INT_L4 = b"\x17"
TAG_FLOAT = b"\x18"
TAG_SLICE = b"\x19"
TAG_FSET = b"\x1a"
TAG_COMPLEX = b"\x1b"
IMM_INTS = dict((i, chr(i + 0x50)) for i in range(-0x30, 0xa0))       #0x20 to 239  (80-48=32), (80+159=239) ??????????

I1 = Struct("!B")            #What is this
I4 = Struct("!L")            #What is this
F8 = Struct("!d")            #What is this
C16 = Struct("!dd")          #What is this


_dump_registry = {}                                             # tag dump reg
_load_registry = {}                                             # tag load ref
IMM_INTS_LOADER = dict((v, k) for k, v in IMM_INTS.iteritems()) # int to tag translation map


def register(coll, key):
    """
    Function storer
    
    This decorator stores the function to be decorated 
    in a dictionary, under the specfied key.
    args, coll is a dictionay, and key is the key. :)
    """
    def deco(func):
        coll[key] = func
        return func
    return deco


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
class register2(object):
    """Equivalnet decorator to above in my way of thinking"""
    
    def __init__(self, store, key):
        self.store = store
        self.key = key
        self.func = None
        
    def __call__(self, func):
        self.store[self.key] = func    #Here we store the function
        
        #self.func = func    #Don't need this wrapper
        #def wrapper():
        #    return self.func()
        return func
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


#Registry, and type => obj and stream => stream append tag

############################################
# These only need tags, only stream arg and no _dump _load
############################################

# None ------------------

@register(_dump_registry, type(None))
def _dump_none(obj, stream):
    stream.append(TAG_NONE)

@register(_load_registry, TAG_NONE)
def _load_none(stream):
    return None


# NotImplemented ---------

@register(_dump_registry, type(NotImplemented))      # Need to look this up
def _dump_notimplemeted(obj, stream):
    stream.append(TAG_NOT_IMPLEMENTED)
    
@register(_load_registry, TAG_NOT_IMPLEMENTED)
def _load_nonimp(stream):
    return NotImplemented


# Ellipsis --------------

@register(_dump_registry, type(Ellipsis))             # Meed to look this up
def _dump_ellipsis(obj, stream):
    stream.append(TAG_ELLIPSIS)

@register(_load_registry, TAG_ELLIPSIS)
def _load_elipsis(stream):
    return Ellipsis


# Bool ------------------

@register(_dump_registry, bool)
def _dump_bool(obj, stream):
    if obj:
        stream.append(TAG_TRUE)
    else:
        stream.append(TAG_FALSE)

@register(_load_registry, TAG_TRUE)
def _load_true(stream):
    return True

@register(_load_registry, TAG_FALSE)
def _load_false(stream):
    return False


###############################################
#These need data, hence have a _dump method
###############################################

# Slice ---------------------

@register(_dump_registry, slice)
def _dump_slice(obj, stream):
    stream.append(TAG_SLICE)
    _dump((obj.start, obj.stop, obj.step), stream)

@register(_load_registry, TAG_SLICE)
def _load_slice(stream):
    start, stop, step = _load(stream)
    return slice(start, stop, step)


# TAG_COMPLEX ---------------

@register(_dump_registry, complex)
def _dump_complex(obj, stream):
    stream.append(TAG_COMPLEX + C16.pack(obj.real, obj.imag))

@register(_load_registry, TAG_COMPLEX)
def _load_complex(stream):
    real, imag = C16.unpack(stream.read(16))
    return complex(real, imag)


# frozen set ---------------

@register(_dump_registry, frozenset)
def _dump_frozenset(obj, stream):
    stream.append(TAG_FSET)
    _dump(tuple(obj), stream)

@register(_load_registry, TAG_FSET)
def _load_frozenset(stream):
    return frozenset(_load(stream))


# Long --------------------

@register(_dump_registry, long)
def _dump_long(obj, stream):
    stream.append(TAG_LONG)
    _dump_int(obj, stream)

@register(_load_registry, TAG_LONG)
def _load_long(stream):
    obj = _load(stream)
    return long(obj)


# Strings -----------------

@register(_dump_registry, str)
def _dump_str(obj, stream):
    l = len(obj)
    if l == 0:
        stream.append(TAG_EMPTY_STR)
    elif l == 1:
        stream.append(TAG_STR1 + obj)
    elif l == 2:
        stream.append(TAG_STR2 + obj)
    elif l == 3:
        stream.append(TAG_STR3 + obj)
    elif l == 4:
        stream.append(TAG_STR4 + obj)
    elif l < 256:
        stream.append(TAG_STR_L1 + I1.pack(l) + obj)
    else:
        stream.append(TAG_STR_L4 + I4.pack(l) + obj)

@register(_load_registry, TAG_EMPTY_STR)
def _load_empty_str(stream):
    return ""

@register(_load_registry, TAG_STR1)
def _load_str1(stream):
    return stream.read(1)

@register(_load_registry, TAG_STR2)
def _load_str2(stream):
    return stream.read(2)

@register(_load_registry, TAG_STR3)
def _load_str3(stream):
    return stream.read(3)

@register(_load_registry, TAG_STR4)
def _load_str4(stream):
    return stream.read(4)

@register(_load_registry, TAG_STR_L1)
def _load_str_l1(stream):
    l, = I1.unpack(stream.read(1))
    return stream.read(l)

@register(_load_registry, TAG_STR_L4)
def _load_str_l4(stream):
    l, = I4.unpack(stream.read(4))
    return stream.read(l)

# Float -----------------------

@register(_dump_registry, float)
def _dump_float(obj, stream):
    stream.append(TAG_FLOAT + F8.pack(obj))

@register(_load_registry, TAG_FLOAT)
def _load_float(stream):
    return F8.unpack(stream.read(8))[0]


# Unicode ---------------------

@register(_dump_registry, unicode)
def _dump_unicode(obj, stream):
    stream.append(TAG_UNICODE)
    _dump_str(obj.encode("utf8"), stream)

@register(_load_registry, TAG_UNICODE)
def _load_unicode(stream):
    obj = _load(stream)
    return obj.decode("utf-8")


# Tuple -----------------------

@register(_dump_registry, tuple)
def _dump_tuple(obj, stream):
    l = len(obj)
    if l == 0:
        stream.append(TAG_EMPTY_TUPLE)
    elif l == 1:
        stream.append(TAG_TUP1)
    elif l == 2:
        stream.append(TAG_TUP2)
    elif l == 3:
        stream.append(TAG_TUP3)
    elif l == 4:
        stream.append(TAG_TUP4)
    elif l < 256:
        stream.append(TAG_TUP_L1 + I1.pack(l))
    else:
        stream.append(TAG_TUP_L4 + I4.pack(l))
    for item in obj:
        _dump(item, stream)

@register(_load_registry, TAG_EMPTY_TUPLE)
def _load_empty_tuple(stream):
    return ()

@register(_load_registry, TAG_TUP1)
def _load_tup1(stream):
    return (_load(stream),)

@register(_load_registry, TAG_TUP2)
def _load_tup2(stream):
    return (_load(stream), _load(stream))

@register(_load_registry, TAG_TUP3)
def _load_tup3(stream):
    return (_load(stream), _load(stream), _load(stream))

@register(_load_registry, TAG_TUP4)
def _load_tup4(stream):
    return (_load(stream), _load(stream), _load(stream), _load(stream))

@register(_load_registry, TAG_TUP_L1)
def _load_tup_l1(stream):
    l, = I1.unpack(stream.read(1))
    return tuple(_load(stream) for i in range(l))

@register(_load_registry, TAG_TUP_L4)
def _load_tup_l4(stream):
    l, = I4.unpack(stream.read(4))
    return tuple(_load(stream) for i in xrange(l))


# Ints --------------------------

@register(_dump_registry, int)
def _dump_int(obj, stream):
    if obj in IMM_INTS:
        stream.append(IMM_INTS[obj])
    else:
        obj = str(obj)
        l = len(obj)
        if l < 256:
            stream.append(TAG_INT_L1 + I1.pack(l) + obj)
        else:
            stream.append(TAG_INT_L4 + I4.pack(l) + obj)

@register(_load_registry, TAG_INT_L1)
def _load_int_l1(stream):
    l, = I1.unpack(stream.read(1))
    return int(stream.read(l))

@register(_load_registry, TAG_INT_L4)
def _load_int_l4(stream):
    l, = I4.unpack(stream.read(4))
    return int(stream.read(l))


#==============================================================================
# Intermediate methods
#==============================================================================

def _undumpable(obj, stream):
    raise TypeError("cannot dump %r" % (obj,))

def _dump(obj, stream):
    _dump_registry.get(type(obj), _undumpable)(obj, stream)

def _load(stream):
    tag = stream.read(1)
    if tag in IMM_INTS_LOADER:
        return IMM_INTS_LOADER[tag]
    return _load_registry.get(tag)(stream)

#==============================================================================
# API
#==============================================================================

def dump(obj):
    """dumps the given object to a byte-string representation"""
    stream = []
    _dump(obj, stream)
    return "".join(stream)

def load(data):
    """loads the given byte-string representation to an object"""
    stream = StringIO(data)
    return _load(stream)

simple_types = frozenset([type(None), int, long, bool, str, float, unicode, 
    slice, complex, type(NotImplemented), type(Ellipsis)])

def dumpable(obj):
    """indicates whether the object is dumpable by brine"""
    if type(obj) in simple_types:
        return True
    if type(obj) in (tuple, frozenset):
        return all(dumpable(item) for item in obj)
    return False
