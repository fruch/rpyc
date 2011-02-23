"""
Modified version - unsecure

brine - a simple, fast and secure object serializer for immutable objects,
the following types are supported: int, long, bool, str, float, unicode, 
slice, complex, tuple(of simple types), forzenset(of simple types)
as well as the following singletons: None, NotImplemented, Ellipsis

#===============================================
My description:  To allow the passing of immutable data from one computer to the next.  
But we want remote procedure calls, so only immutable data should be passed, the rest should be proxied first the brined.

Main api
dump      : takes an object and returns it serised
load      : takes serialsed data and returns and object
dumpable  : checks if data meats our requirements for dumpababilty, we have a list of immutable types

Other maybe used api
_pickle    : Just a tiny wrapper of native python pickle that interchanges a pickle exception for a brine type one
_unpickle  : Just a tiny wrapper of native python pickle that interchanges a pickle exception for a brine type one
"""

# This one is not as secure as orginal!  Security is overrated.
# ToDo
# Implement better errors, that can be imported from this module alone !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# See below

import pickle as _pickler # In python3 this one now attempt to import the cPickle one automatcially

"Protocol version 3 was added in Python 3.0. It has explicit support for bytes and cannot be unpickled by Python 2.x pickle modules. This is the current recommended protocol, use it whenever it is possible."

from global_consts import TAG_PICKLED
from global_consts import TAG_PROXIED
from global_consts import TAG_LENGTH
from global_consts import Rpyc_Exception

simple_brine_types = frozenset([type(None), type(NotImplemented), type(Ellipsis), 
                                bool, slice, int, str, float, complex, bytes])
complex_brine_types = frozenset([frozenset, tuple])

default_brine_types = frozenset(simple_brine_types | complex_brine_types)

#==============================================================================
# ERRORS
#==============================================================================

class Brine_Exception(Rpyc_Exception):
    def __init__(self, err_string):
        self.args = (err_string)
        self.err_string = err_string
    def __str__(self):
        return self.err_string
    def __repr__(self):
        return self.err_string

class Brine_Dump_Exception(Brine_Exception):
    def __init__(self, err_string):
        super().__init__(err_string="Brine_Dump_Exception")

class Brine_Load_Exception(Brine_Exception):
    def __init__(self, err_string):
        super().__init__(err_string="Brine_Load_Exception")

class Brine_Pickle_Exception(Brine_Exception):
    def __init__(self, err_string):
        super().__init__(err_string="Brine_Pickle_Exception")

class Brine_Unpickle_Exception(Brine_Exception):
    def __init__(self, err_string):
        super().__init__(err_string="Brine_Unpickle_Exception")

class Brine_Other_Exception(Brine_Exception):
    def __init__(self, err_string):
        super().__init__(err_string="Brine_Other_Exception")

def _not_dumpable_err(obj):
    err_string = "cannot dump {0}".format(obj)
    raise Brine_Dump_Exception(err_string)

def _not_loadable_err(obj):
    err_string = "cannot load {0}".format(obj)
    raise Brine_Load_Exception(err_string)

def _not_pickleable_err(obj):
    err_string = "cannot pickle {0}".format(obj)
    raise Brine_Pickle_Exception(err_string)

def _not_unpickleable_err(obj):
    err_string = "cannot unpickle {0}".format(obj)
    raise Brine_Unpickle_Exception(err_string)

def _other_err():
    err_string = "other error".format()
    raise Brine_Other_Exception(err_string)

#==============================================================================
# Underbelly
#==============================================================================

def _pickle(obj, protocol = _pickler.HIGHEST_PROTOCOL):
    try:
        data = _pickler.dumps(obj, protocol)
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
        print("Illegal tag {0}".format(tag))
        print("known tags TAG_PICKLED={0}, TAG_PROXIED={1}".format(TAG_PICKLED, TAG_PROXIED))
        _other_err()

def dumpable(obj):
    """indicates whether the object is dumpable by brine"""
    if type(obj) in simple_brine_types:
        return True
    if type(obj) in complex_brine_types:
        return all(dumpable(item) for item in obj)
    return False 
