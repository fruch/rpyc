"""
NetRef - transparent network references implementation.

SURGEON GENERAL'S WARNING: Black magic is known to causes Lung Cancer,
Heart Disease, Emphysema, and May Complicate Pregnancy. Close your eyes!


The why
What it does

The common API


"""
import sys
import inspect
import types
import pickle

#from rpyc.core import global_consts
import global_consts
from global_consts import Rpyc_Exception

#==============================================================
# Module Specfic Errors
#==============================================================

class Netref_Exception(Rpyc_Exception):
    """Class of errors for the Vinegar module
    
    This class of exceptions is used for errors that occur
    when dealing with the encoding, passing, and decoding of errors.
    """
    def __init__(self, err_string=''):
        self.args = (err_string,)   #This contains info about the error, cause etc, can be a tuple of a string, tuple in this case
    def __str__(self):
        return self.args[0]
    def __repr__(self):
        return self.args[0]

class Netref_EG_Exception(Netref_Exception):
    def __init__(self, err_string="Netref_EG_Exception"):
        super().__init__(err_string)

#==============================================================
# Main program
#==============================================================

class NetrefMetaclass(type):
    """a metaclass just to customize the __repr__ of netref classes, 
    so repr(type(instance_base_net_ref)) will use this"""
    __slots__ = ()
    
    def __repr__(self):
        if self.__module__:
            return "<netref class '%s.%s'>" % (self.__module__, self.__name__)
        else:
            return "<netref class '%s'>" % (self.__name__,)

_local_netref_attrs = frozenset([
                                 #Ones we define in the BaseNetref class below
                                 "__del__", "__getattribute__", "__setattr__", "__getattr__", "__delattr__",
                                 "__dir__",  "__hash__", "__cmp__", 
                                 "__repr__", "__str__", 
                                 "__reduce_ex__",
                                 
                                 #Ignore please let to code work these out
                                 "__dict__", "__slots__",
                                 
                                 #Specfic ones specfic to the proxy
                                 "____conn__", "____oid__", "____local_netref_attrs__"        #These are attrs
                                 ])

#===========Might need to do ========================
#'__eq__'
#'__gt__'
#'__bases__' #Shows one level away subclasses 
#'__mro__'   #Shows the relsoution path for a class
#====================================================

class BaseNetref(object, metaclass=NetrefMetaclass):
    """the base netref object, from which all netref classes derive
    
    Specfics
    ___conn__ : weakref.ref to the connection class, maybe should use a Weakvalue dict etc as they clean themselves up.
    ___oid__ :  object id
    """
    __slots__ = ["____conn__", "____oid__", "____local_netref_attrs__", "__weakref__"]   # '__weakref__' so we support weak references to the instances
    
    def __init__(self, conn, oid):
        self.____conn__ = conn
        self.____oid__ = oid
        self.____local_netref_attrs__ = _local_netref_attrs
        #Could define here known methods so don't lookup ones that are unknown
    
    @property
    def __class__(self):
        cls = object.__getattribute__(self, "__class__")
        if cls is None:                    #<-------- I think this comes from the make_proxy_class
            cls = self.__getattr__("__class__")
        return cls
    
    def __del__(self):
        try:
            asyncreq(self, global_consts.HANDLE_DEL)
        except BaseException as error:
            try:
                print("Warning: netref BaseNetref __del__")
                print(error.args)
            except AttributeError:
                pass
    
    def __getattribute__(self, attrname):
        """Here we try for local access, else resolved remotely using __getattr__"""
        # Should I use super here?  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if attrname in object.__getattribute(self, _local_netref_attrs):
            return object.__getattribute__(self, name)
        else:
            return self.__getattr__(name)
    
    def __getattr__(self, name):
        """This is is a remote get attr call"""
        return syncreq(self, global_consts.HANDLE_GETATTR, name)
    
    def __delattr__(self, name):
        """This method will only effect the remote proxy not the local one !!!!!!!!!!!!!!!!!!!!!!!! Todo"""
        if name in _local_netref_attrs:
            object.__delattr__(self, name)
        else:
            syncreq(self, global_consts.HANDLE_DELATTR, name)
    
    def __setattr__(self, name, value):
        if name in _local_netref_attrs:
            object.__setattr__(self, name, value)
        else:
            syncreq(self, global_consts.HANDLE_SETATTR, name, value)
    
    def __dir__(self):
        return list(syncreq(self, global_consts.HANDLE_DIR))
    
    def __hash__(self):                 # support for metaclasses
        return syncreq(self, global_consts.HANDLE_HASH)
    
    def __cmp__(self, other):       # Could deal with dictionary specficly Could use pickle, Need to think here!!!!
        """Might need to iterate here to try and compare, anyway work to do here"""
        
        return syncreq(self, global_consts.HANDLE_CMP, other)
    def __repr__(self):
        return syncreq(self, global_consts.HANDLE_REPR)
    
    def __str__(self):
        return syncreq(self, global_consts.HANDLE_STR)
    
    def __reduce_ex__(self, proto):          # support for pickle
        return pickle.loads, (syncreq(self, global_consts.HANDLE_PICKLE, proto),)

def syncreq(proxy, handler, *args):
    """performs a synchronous request on the given proxy object"""
    conn = object.__getattribute__(proxy, "____conn__")
    oid = object.__getattribute__(proxy, "____oid__")
    return conn().sync_request(handler, oid, *args)

def asyncreq(proxy, handler, *args):
    """performs an asynchronous request on the given proxy object, 
    retuning an AsyncResult"""
    conn = object.__getattribute__(proxy, "____conn__")
    oid = object.__getattribute__(proxy, "____oid__")
    return conn().async_request(handler, oid, *args)

def _make_proxy_method(name, doc):
    """Make a proxy method that will call the original instance and return the result"""
    def method(_self, *args, **kwargs):
        kwargs = tuple(kwargs.items())
        return syncreq(_self, global_consts.HANDLE_CALLATTR, name, args, kwargs)
    
    def __call__(_self, *args, **kwargs):
        kwargs = tuple(kwargs.items())
        return syncreq(_self, global_consts.HANDLE_CALL, args, kwargs)
    
    if name == "__call__":
        proxy_method = __call__
    else:
        proxy_method = method
    
    proxy_method.__name__ = name
    proxy_method.__doc__ = doc
    return proxy_method

# inspect.getmro(cls)
# inspect.getmembers(obj, ismethod)   "#isroutine is any kind of function or method"

def inspect_methods(obj):
    """returns a list of (method name, docstring) tuples of all the methods given obj"""
    methods = {}
    attrs = {name:inspect.getdoc(attr) for name, attr in inspect.getmembers(obj)}   #Start from these, then we go through to mro to check for any other
    # as getmembers is based on dir which is can go to __dir__, so hit it twice.
    
    try:
        # Meta classes are all subclasses of type
        # Python goes futher than this, all classes are instances of type, instance of class is not.
        # To detect is a class is a metaclass use issubclass(cls, type)
        
        if isinstance(obj, type):                  # This asks is this a class, then the obj will have a __mro__
            # A Duplicated mro will be taken out at dict stage.  Don't actually care what method takes precence apart form the doc string !!!!!! need to check this !!!!!
            # Left lest important,  right most important
            mros = list(reversed(type(obj).__mro__)) + list(reversed(obj.__mro__)) 
        else:                                               # Else must be an instance
            mros = reversed(type(obj).__mro__)
        
        # mro = method resolution order, so we now have the inhertance tree,
        
    except AttributeError:
        print("Warning: This object is incompatable doesn't seem to have a method resolution order")
        return []
    
    #Iterate over all base classes and add an entry for all possible attributes
    for basecls in mros:
        attrs.update(basecls.__dict__)
    
    #Iterate over all attributes and filter out the callable ones and get the doc for them.
    for name, attr in attrs.items():
        if hasattr(attr, "__call__"):
            methods[name] = inspect.getdoc(attr)
    
    #Return known methods, outside of local netref attrs
    return methods #Returns [(meth_name, doc), (meth_name, doc)]

#==============================================================
# builtin types
#==============================================================

#==========Changes to 3=============
#http://docs.python.org/release/3.0.1/whatsnew/3.0.html#builtins
#basestring is gone
#unicode is gone
#long is gone
#types.InstanceType, types.ClassType both gone
#types.NoneType, types.DictProxyType both gone
#file is gone from builtins see the io module in py3
#bytes and bytearray is new
#memoryview is new
# Super is a class type thing in python3 think about this !!!!!!!!!!!!!!!!!!!!!!!!
#View and things are new!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# builtins!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#The below method more generic
#y=[getattr(builtins, x) for x in dir(builtins)]
#y=[x for x in y if inspect.isclass(x)]
#y=[x for x in y if not issubclass(x, BaseException)]

# types !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Would this be better? More future proof or just dangerous?
#Other  __module__ says these from builtins??
#[getattr(types, x) for x in dir(types) if not x.startswith('__')]
#"types - Define names for built-in types that aren't directly accessible as a builtin."

_builtin_types = [
                #From builtins
                Exception,
                type, object,
                bool,
                list, dict, tuple, set, frozenset,
                slice, range,
                str, 
                float, int, complex,
                bytes, bytearray,
                
                #From types
                types.BuiltinFunctionType, types.BuiltinMethodType,
                types.MethodType, types.FunctionType, types.ModuleType, 
                types.GetSetDescriptorType, types.LambdaType,
                types.GeneratorType,
                types.CodeType, types.FrameType, types.TracebackType, 
                
                #This looks like deep magic to me.!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                type(int.__add__),      # wrapper_descriptor
                type((1).__add__),      # method-wrapper
                type(iter([])),         # listiterator
                type(iter(())),         # tupleiterator
                type(iter(range(10))),  # rangeiterator
                type(iter(set())),      # setiterator
                ]

#==============================================================
# API
#==============================================================


def is_netref(obj):   #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    pass

def make_proxy_class(clsname, modname, methods):
    #Dunno why __slots__ below??????????? why not just {}
    #ns = {"__slots__": ()}  #Slots are used in classes instead of make __dict__. slightly faster can't add attrs.
    
    #Name space seems to be missing all the local_netref attrs
    namespace = {}
    
    for methname, methdoc in methods.items():
        if methname not in _local_netref_attrs:
            namespace[methname] = _make_proxy_method(methname, methdoc)
    
    namespace["__module__"] = modname
    if modname in sys.modules and hasattr(sys.modules[modname], clsname):
        namespace["__class__"] = getattr(sys.modules[modname], clsname)
    elif (clsname, modname) in _normalized_builtin_types:
        namespace["__class__"] = _normalized_builtin_types[clsname, modname]
    else:
        namespace["__class__"] = None            # to be resolved by the instance
    
    return type(clsname, (BaseNetref,), namespace)



# We get a dictionary of builtin types, key[name, module] = type
# I think this is the native dict of the classes
# RENAME!!!!!!!!!!!!!   native_type_dict
_normalized_builtin_types = dict( ((typ.__name__, typ.__module__), typ) for typ in _builtin_types)

# Here we make a cache of builtins some are in types module etc.
# This is used in protocal, I am guessing this is the remote type dict
# RENAME!!!!!!!!!!!!   remote_type_dict
builtin_classes_cache = {}
for cls in _builtin_types:
    typeinfo = (cls.__name__, cls.__module__)
    builtin_classes_cache[typeinfo] = make_proxy_class(
                        cls.__name__, cls.__module__, inspect_methods(cls))

#Inspect methods is the class namespace
