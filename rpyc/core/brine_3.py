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

from globals import TAG_PICKLED
from globals import TAG_PROXIED
from globals import TAG_LENGTH
from globals import Core_Exception



simple_brine_types = frozenset([type(None), type(NotImplemented), type(Ellipsis), 
                                bool, slice, int, str, float, complex, bytes])
complex_brine_types = frozenset([frozenset, tuple])
default_brine_types = frozenset(simple_brine_types | complex_brine_types)

#==============================================================================
# ERRORS
#==============================================================================

class Brine_Exception(Core_Exception):
    def __init__(self, err_string, err_type):
        self.args = (err_string, err_type)
        self.err_string = err_string
        self.type = err_type
    def __str__(self):
        return self.err_string
    def __repr__(self):
        return self.err_string

def _not_dumpable_err(obj):
    err_string = "cannot dump {0}".format(obj)
    raise Brine_Exception(err_string,  "not_dumpable")

def _not_loadable_err(obj):
    err_string = "cannot load {0}".format(obj)
    raise Brine_Exception(err_string, "not_loadable")

def _not_pickleable_err(obj):
    err_string = "cannot dump {0}".format(obj)
    raise Brine_Exception(err_string, "not_pickleable")

def _not_unpickleable_err(obj):
    err_string = "cannot load {0}".format(obj)
    raise Brine_Exception(err_string, "not_unpickleable")

def _other_err():
    err_string = "other error".format()
    raise Brine_Exception(err_string, "other error")

#==============================================================================
# Underbelly
#==============================================================================

def _pickle(obj):
    try:
        data = _pickler.dumps(obj, protocol = _pickler.HIGHEST_PROTOCOL)
    except _pickler.PicklingError:
        _not_pickleable_err(obj)
    return data
    
def _unpickle(bytes_object):
    try:
        data = _pickler.loads(bytes_object)
    except _pickler.UnpicklingError:
        _not_unpickleable_err(obj)
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
        _not_dumpable_err(obj)

def load(bytes_object):
    """loads the given byte-string representation to an object"""
    tag = bytes_object[0:TAG_LENGTH]
    if tag == TAG_PICKLED:
        return _unpickle(bytes_object[1:])
    elif tag == TAG_PROXIED:
        print("Trying to unpickle a proxy object")
        _not_loadable_err(bytes_object)
    else:
        print(tag)
        print(TAG_PICKLED)
        _other_err()

def dumpable(obj):
    """indicates whether the object is dumpable by brine"""
    if type(obj) in simple_brine_types:
        return True
    if type(obj) in complex_brine_types:
        return all(dumpable(item) for item in obj)
    return False 
