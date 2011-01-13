"""
Modified version - unsecure

brine - a simple, fast and secure object serializer for immutable objects,
the following types are supported: int, long, bool, str, float, unicode, 
slice, complex, tuple(of simple types), forzenset(of simple types)
as well as the following singletons: None, NotImplemented, Ellipsis
"""

# This one is not as secure as orginal!  Security is overrated.
# ToDo
# Implement better errors, that can be imported from this module alone !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# See below

import pickle as _pickler # In python3 this one now attempt to import the cPickle one automatcially

"Protocol version 3 was added in Python 3.0. It has explicit support for bytes and cannot be unpickled by Python 2.x pickle modules. This is the current recommended protocol, use it whenever it is possible."

TAG_PICKLED = b"\x01"
TAG_PROXIED = b"\x02"

simple_brine_types = frozenset([type(None), type(NotImplemented), type(Ellipsis), 
                                bool, slice, int, str, float, complex, bytes])
complex_brine_types = frozenset([frozenset, tuple])
default_brine_types = frozenset(simple_brine_types | complex_brine_types)

#==============================================================================
# Underbelly
#==============================================================================

def _pickle(obj):
    try:
        data = _pickler.dumps(obj, protocol = _pickler.HIGHEST_PROTOCOL)
    except _pickler.PicklingError:
        raise
    return data
    
def _unpickle(bytes_object):
    try:
        data = _pickler.loads(bytes_object)
    except _pickler.UnpicklingError:
        raise
    return data

#==============================================================================
# API
#==============================================================================

def dump(obj):
    """dumps the given object to a byte-string representation"""
    if type(obj) in default_brine_types:
        data = _pickle(obj)
        return TAG_PICKLED + data
    else:
        _undumpable(obj)

def load(bytes_object):
    """loads the given byte-string representation to an object"""
    tag = bytes_object[0]
    if tag == TAG_PICKLED:
        return _unpickle(bytes_object[1:])
    elif tag == TAG_PROXIED:
        print "Tring to unpickel a proxy object"
        _unloadable(bytes_object)

def dumpable(obj):
    """indicates whether the object is dumpable by brine"""
    if type(obj) in simple_brine_types:
        return True
    if type(obj) in complex_brine_types:
        return all(dumpable(item) for item in obj)
    return False 

#==============================================================================
# ERRORS
#==============================================================================

# implement my own errors in here !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

def _undumpable(obj):
    raise TypeError("cannot dump %r" % (obj,))

def _unloadable(obj):
    raise TypeError("cannot load %r" % (obj,))

