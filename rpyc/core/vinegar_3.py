"""
vinegar_3 ('when things go sour'): serialization/deserializer of exceptions.

"""
import sys
import traceback
import builtins
import inspect

import brine_3 as brine

from globals import EXCEPTION_STOP_ITERATION
from globals import Rpyc_Exception

inbuilt_expections = {xept: getattr(builtins, xept) for xept in dir(builtins) 
                      if inspect.isclass(getattr(builtins, xept)) 
                      and issubclass(getattr(builtins, xept), BaseException)}

_generic_exceptions_cache = {}

#==============================================================
# Errors
#==============================================================

class Vinegar_Exception(Rpyc_Exception):
    """Class of errors for the Vinegar module
    
    This class of exceptions is used for errors that occur
    when dealing with the encoding, passing, and decoding of errors.
    """
    def __init__(self, err_string=''):
        self.args = (err_string)   #This contains info about the error, cause etc, can be a tuple of a string, tuple in this case
        self.err_string = err_string
    def __str__(self):
        return self.err_string
    def __repr__(self):
        return self.err_string

class Vinegar_Dump_Exception(Vinegar_Exception):
    def __init__(self, err_string):
        super(Vinegar_Dump_Exception, self).__init__(err_string)

class Vinegar_Load_Exception(Vinegar_Exception):
    def __init__(self, err_string):
        super(Vinegar_Load_Exception, self).__init__(err_string)

class Vinegar_Import_Exception(Vinegar_Exception):
    def __init__(self, err_string):
        super(Vinegar_Import_Exception, self).__init__(err_string)

class Vinegar_Excepthook_Exception(Vinegar_Exception):
    def __init__(self, err_string):
        super(Vinegar_Excepthook_Exception, self).__init__(err_string)

def _dump_err():
    """This function is for raising couldn't dump exception type errors"""
    raise Vinegar_Dump_Exception("Vinegar: dump err")
    
def _load_err():
    """This function is for raising couldn't load exception type errors"""
    raise Vinegar_Load_Exception("Vinegar: load err")

def _import_err(module_name):
    """This function is for raising couldn't import module to make sense of custom exception"""
    raise Vinegar_Import_Exception("Vinegar: couldn't import {0} to get custom exception".format(module_name))

def _excepthook_err():
    """This error covers the event if the new exception handling hook which 
    handles remote tracebacks can't be installed"""
    raise Vinegar_Excepthook_Exception("Vinegar:: Couldn't find sys.excepthook")

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

#==============================================================
# Underbelly
#==============================================================

class GenericException(Exception):
    """This is used to create pseudo exceptions"""
    pass


def load(brined_xcept, import_custom_exceptions=False):
#def load(brined_xcept, import_custom_exceptions, instantiate_exceptions, instantiate_oldstyle_exceptions):
    """ Loads brined exception
    
    return exception returns an exception object that can be raised."""
    
    #Special case
    if brined_xcept == EXCEPTION_STOP_ITERATION:
        return StopIteration() # optimization short hand #Should this be StopIteration()
    
    #Pull out values
    try:
        (modname, clsname), args, attrs, traceback_txt = brined_xcept           #This matches return of dump func
    except ValueError:
        _load_err()
    
    #We may want to import a module to get a custom extension
    if import_custom_exceptions and modname not in sys.modules:
        
        try:   # Should use class name here
            print("errrmmm")
            mod = __import__(modname, None, None, fromlist=[clsname])    #Scarey to me could this not change a global and fuck the world !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        except ImportError:
            print("errrr")
            _import_err(modname)
    
    #Here we create a local representation of the exception
    if modname == "builtins":                       # Not valid in python3, exceptions have been moved to builtins
        cls = getattr(builtins, clsname, None)
        if not inspect.isclass(cls) and issubclass(cls, BaseException):
            load_err()
        exc = cls(*args)
    elif modname not in sys.modules:
        try:
            cls = getattr(sys.modules[modname], clsname, None)
        except KeyError:
            print("No such module has been imported and known")
            _import_err(modname)
        except AttributeError:
            print("couldn't find the class in the above module")
            _import_err(modname+"."+clsname)
        else:
            if not inspect.isclass(cls) and issubclass(cls, BaseException):
                load_err()
            exc = cls(*args)
    else:
        #print("Unknown module, making a generic representation of it")
        fullname = "{0}.{1}".format(modname, clsname)
        if fullname not in _generic_exceptions_cache:
            #fakemodule = {"__module__" : "{0}.{1}".format(__name__, modname)}
            fakemodule = {"__module__" : "{0}".format(modname)}
            _generic_exceptions_cache[fullname] = type(clsname, (GenericException,), fakemodule)  #!!!!!!!!!!!!!!!! why use this
        cls = _generic_exceptions_cache[fullname]
        exc = cls()
        exc.args = args         #Moved this!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
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
# No real point to this as both py2 and 3 store the original in sys.__excepthook__ anyway. :)
# ironpython forgot to implement excepthook, scheisse

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
    if not hasattr(sys, "excepthook"):
        print("Warning: sys doens't have excepthook, there be problems showing remote tracebacks")
        sys.excepthook = None
        sys.__excepthook__ = None
    
    try:
        sys.excepthook = rpyc_excepthook
    except:
        _excepthook_err()

def uninstall_rpyc_excepthook():
    """This changes sys.excepthook to the orginal standard python one"""
    try:
        sys.excepthook = sys.__excepthook__
    except:
        _excepthook_err()
