"""
vinegar_3 ('when things go sour'): safe serialization of exceptions.

note that by changing the configuration parameters, this module can be
made non-secure
"""

import sys
#import exceptions                            # <- No longer exists !!!!!!!!!!!!!!!!!!!
import traceback
#from types import InstanceType, ClassType    # <- No longer exists !!!!!!!!!!!!!!!!!!!

from rpyc.core import brine_3 as brine
from rpyc.core import consts

from globals import Core_Exception

_generic_exceptions_cache = {}

STOP_ITERATION_MAGIC = 0                      # <--- Don't like the sound of this

#==============================================================
# Errors
#==============================================================

class Vinegar_Exception(Core_Exception):
    def __init__(self, err_string, err_type):
        self.args = (err_string, err_type)
        self.err_string = err_string
        self.type = err_type
    def __str__(self):
        return self.err_string
    def __repr__(self):
        return self.err_string

class GenericException(Exception):
    pass

def dump(typ, val, tb, include_local_traceback):
    if type(typ) is str:
        return typ
    if typ is StopIteration:
        return consts.EXC_STOP_ITERATION # optimization
    
    if include_local_traceback:
        tbtext = "".join(traceback.format_exception(typ, val, tb))
    else:
        tbtext = "<traceback denied>"
    attrs = []
    args = []
    for name in dir(val):
        if name == "args":
            for a in val.args:
                if brine.dumpable(a):
                    args.append(a)
                else:
                    args.append(repr(a))
        elif not name.startswith("_") or name == "_remote_tb":
            attrval = getattr(val, name)
            if not brine.dumpable(attrval):
                attrval = repr(attrval)
            attrs.append((name, attrval))
    return (typ.__module__, typ.__name__), tuple(args), tuple(attrs), tbtext

try:
    BaseException
except NameError:
    # python 2.4 compatible
    BaseException = Exception

def load(val, import_custom_exceptions, instantiate_custom_exceptions, 
         instantiate_oldstyle_exceptions):

    if val == consts.EXC_STOP_ITERATION:
        return StopIteration # optimization
    
    if type(val) is str:                          # Not in python3 remove
        return val # deprecated string exceptions
    
    (modname, clsname), args, attrs, tbtext = val
    if import_custom_exceptions and modname not in sys.modules:
        try:
            mod = __import__(modname, None, None, "*")
        except ImportError:
            pass
    if instantiate_custom_exceptions:
        cls = getattr(sys.modules[modname], clsname, None)
    elif modname == "exceptions":                  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        cls = getattr(exceptions, clsname, None)
    else:
        cls = None
    
    if not isinstance(cls, (type, ClassType)):
        cls = None
    elif issubclass(cls, ClassType) and not instantiate_oldstyle_exceptions:
        cls = None
    elif not issubclass(cls, BaseException):
        cls = None
    
    if cls is None:
        fullname = "%s.%s" % (modname, clsname)
        if fullname not in _generic_exceptions_cache:
            fakemodule = {"__module__" : "%s.%s" % (__name__, modname)}
            if isinstance(GenericException, ClassType):
                _generic_exceptions_cache[fullname] = ClassType(fullname, (GenericException,), fakemodule)
            else:
                _generic_exceptions_cache[fullname] = type(fullname, (GenericException,), fakemodule)
        cls = _generic_exceptions_cache[fullname]
    
    # support old-style exception classes
    if isinstance(cls, ClassType):
        exc = InstanceType(cls)
    else:
        exc = cls.__new__(cls)
    
    exc.args = args
    for name, attrval in attrs:
        setattr(exc, name, attrval)
    if hasattr(exc, "_remote_tb"):
        exc._remote_tb += (tbtext,)
    else:
        exc._remote_tb = (tbtext,)
    return exc


#==============================================================================
# customized except hook
#==============================================================================
# Here we change sys.excepthook to allow printing of remote tracebacks
#
# sys.excepthook(type, value, traceback) 
# is a function that prints out a given tranceback and exception to std.err
# 
# This used by python to print exceptions
#==============================================================================

# set module variable containing orginal exceptionhook
if hasattr(sys, "excepthook"):
    _orig_excepthook = sys.excepthook           #!!!!!!!!!!!!!!!!!!!!!  Look this up
else:
    # ironpython forgot to implement excepthook, scheisse
    _orig_excepthook = None

def rpyc_excepthook(typ, val, tb):
    """ This is a customised exception hook, so can print remote tracebacks
    
    The can be used instead of sys.excepthook"""
    if hasattr(val, "_remote_tb"):
        sys.stderr.write("======= Remote traceback =======\n")
        tbtext = "\n--------------------------------\n\n".join(val._remote_tb)
        sys.stderr.write(tbtext)
        sys.stderr.write("\n======= Local exception ========\n")
    _orig_excepthook(typ, val, tb)

def install_rpyc_excepthook():
    """This changes sys.excepthook to allow printing of remote tracebacks"""
    if _orig_excepthook is not None:
        sys.excepthook = rpyc_excepthook
    else:
        raise Vinegar_Exception("Couldn't find sys.excepthook", "excepthook_error")

def uninstall_rpyc_excepthook():
    """This changes sys.excepthook to the orginal standard python one"""
    if _orig_excepthook is not None:
        sys.excepthook = _orig_excepthook
    else:
        raise Vinegar_Exception("Couldn't find sys.excepthook", "excepthook_error")
