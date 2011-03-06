"""
vinegar_3 ('when things go sour'): serialization/deserializer of exceptions.

"""

import sys
import traceback
import builtins
import inspect

#from types import InstanceType, ClassType    # <- No longer exists !!!!!!!!!!!!!!!!!!!
#import exceptions                            # <- No longer exists !!!!!!!!!!!!!!!!!!!

import brine_3 as brine

from globals import EXCEPTION_STOP_ITERATION as EXCEPTION_STOP_ITERATION
from globals import Rpyc_Exception

inbuilt_expections = {xept: getattr(builtins, xept) for xept in dir(builtins) 
                      if inspect.isclass(getattr(builtins, xept)) 
                      and issubclass(getattr(builtins, xept), BaseException)}

_generic_exceptions_cache = {}

#==============================================================
# Errors
#==============================================================

class Vinegar_Exception(Rpyc_Exception):
    def __init__(self, err_string, err_type):
        self.args = (err_string, err_type)
        self.err_string = err_string
        self.type = err_type
    def __str__(self):
        return self.err_string
    def __repr__(self):
        return self.err_string

def _dump_err():
    return Vinegar_Exception("Vinegar: dump err", "dump_error")
    
def _load_err():
    return Vinegar_Exception("Vinegar: load err", "load_error")

def _import_err(module_name):
    return Vinegar_Exception("Vinegar: couldn't import {0} to get custom exception".format(module_name), "import_error")

def _excepthook_err():
    raise Vinegar_Exception("Vinegar:: Couldn't find sys.excepthook", "excepthook_error")

#==============================================================
# Underbelly
#==============================================================

class GenericException(Exception):
    pass


#==============================================================
# API
#==============================================================

def dump(exception_class, exception_instance, traceback_obj, include_local_traceback=True):
    """ Dumps given exception in brinable format
    
    This picks the args tuple and the _remote_tb instance out.  Stores the traceback text" Also stores non _ args.
    PS. StopIteration is handled specially
    
    args::------
    
    exception_class:: Exception type, class object
    exception_instance:: Exception Value, class instance
    traceback_obj      
            Exception objects now store their traceback as the 
            __traceback__ attribute.  This means that an exception 
            object now contains all the information pertaining to 
            an exception. Don't need sys.exc_info() as much.
            This can cause a circular reference if assigned local in function handling it.
            
    include_local_traceback:: Flag that say where or not to display local traceback.

    return vals:-----
    
    (exception_class.__module__, exception_class.__name__):: exception module and name
    tuple(args):: Stuff plucked from exception_instance.args 
    tuple(attrs):: From    # support old-style exception classes
    if isinstance(cls, ClassType):
        exc = InstanceType(cls)
    else:
        exc = cls.__new__(cls)
    
    GenericException
    
    exc.args = args
    for name, attrval in attrs:
        setattr(exc, name, attrval)

    if hasattr(exc, "_remote_tb"):
        exc._remote_tb += (traceback_txt,)
    else:
        exc._remote_tb = (traceback_txt,)

    return exc non startswith('_') attrs and _remote_tb
    tracebacktext:: text of the traceback
    """
    
    if issubclass(exception_class, BaseException) and isinstance(exception_instance, exception_class):
        pass
    else:
        _dump_err()
    
    #Special case
    if exception_class is StopIteration:
        return EXCEPTION_STOP_ITERATION                           # optimization   #<-------Is this really needed?!!!!!!!!!!!!!!!
    
    # Get traceback_obj message
    if include_local_traceback:                             # mmm must be true false, no default given???????
        traceback_txt = "".join(traceback.format_exception(exception_class, exception_instance, traceback_obj))   # already contains a new line
    else:
        traceback_txt = "<traceback denied>"                #-----------??? denied, why not just no
    
    def make_dumpable(obj):
        if brine.dumpable(obj):
            return obj
        else:
            return repr(obj)
    
    # get attributes and arguments given to exception, keep tag _remote_tb
    attrs = []
    args = []
    for name in dir(exception_instance):
        if name == "args":
            for arg in exception_instance.args:
                d_arg = make_dumpable(arg)
                args.append(d_arg)
        elif (not name.startswith("_") and not name == "with_traceback") or name == "_remote_tb" :
            attr_val = getattr(exception_instance, name)
            d_attr_val = make_dumpable(attr_val)
            attrs.append((name, d_attr_val))
    
    return (exception_class.__module__, exception_class.__name__), tuple(args), tuple(attrs), traceback_txt

def load(brined_xcept, import_custom_exceptions=False, instantiate_custom_exceptions=False):
#def load(brined_xcept, import_custom_exceptions, instantiate_custom_exceptions, instantiate_oldstyle_exceptions):
    """ Loads brined exception
    
    return exception returns an exception object that can be raised."""
    #I'd like defaults here!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    #Special case
    if brined_xcept == EXCEPTION_STOP_ITERATION:
        return StopIteration() # optimization short hand #Should this be StopIteration()
    
    #Pull out values
    try:
        (modname, clsname), args, attrs, traceback_txt = brined_xcept  #This matches return of dump func
    except ValueError:
        _load_err()
    
    # import the relevent module
    if import_custom_exceptions and modname not in sys.modules:
        try:
            mod = __import__(modname, None, None, "*")    #Scarey to me could this not change a global and fuck the world !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        except ImportError:
            _import_err(modname)
    
    #Here we define the execption class
    if instantiate_custom_exceptions:
        cls = getattr(sys.modules[modname], clsname, None)
    elif modname == "builtins":                       # Not valid in python3, exceptions have been moved to builtins
        cls = getattr(builtins, clsname, None)
    else:
        #print("Unknown module, making a generic representation of it")
        cls = None                                       # What effect does this have better to raise an error??
    
    # Check class is an Exception
    if cls != None:
        if not inspect.isclass(cls):
            load_err()
            #cls = None
        if not issubclass(cls, BaseException):
            load_err()
            #cls = None
    
    if cls != None:
        exc = cls(*args)
    else:              # If counldn't import exception class make a dummy class
        fullname = "{0}.{1}".format(modname, clsname)
        if fullname not in _generic_exceptions_cache:
            #fakemodule = {"__module__" : "{0}.{1}".format(__name__, modname)}
            fakemodule = {"__module__" : "{0}".format(modname)}
            _generic_exceptions_cache[fullname] = type(clsname, (GenericException,), fakemodule)
        cls = _generic_exceptions_cache[fullname]
        exc = cls()
        exc.args = args #Moved this!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    for name, attrval in attrs:
        setattr(exc, name, attrval)

    if hasattr(exc, "_remote_tb"):
        exc._remote_tb += (traceback_txt,)
    else:
        exc._remote_tb = (traceback_txt,)

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
    _orig_excepthook = sys.excepthook
else:
    # ironpython forgot to implement excepthook, scheisse
    _orig_excepthook = None

def rpyc_excepthook(typ, val, tb):
    """ This is a customised exception hook, so can print remote tracebacks
    
    The can be used instead of sys.excepthook"""
    
    if hasattr(val, "_remote_tb"):
        sys.stderr.write("======= Remote traceback =======\n")
        traceback_txt = "\n--------------------------------\n\n".join(val._remote_tb)
        sys.stderr.write(traceback_txt)
        sys.stderr.write("\n======= Local exception ========\n")
    _orig_excepthook(typ, val, tb)

def install_rpyc_excepthook():
    """This changes sys.excepthook to allow printing of remote tracebacks"""
    if _orig_excepthook is not None:
        sys.excepthook = rpyc_excepthook
    else:
        _excepthook_err()

def uninstall_rpyc_excepthook():
    """This changes sys.excepthook to the orginal standard python one"""
    if _orig_excepthook is not None:
        sys.excepthook = _orig_excepthook
    else:
        _excepthook_err()
