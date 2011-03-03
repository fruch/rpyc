"""
NetRef - transparent network references implementation.

SURGEON GENERAL'S WARNING: Black magic is known to causes Lung Cancer,
Heart Disease, Emphysema, and May Complicate Pregnancy. Close your eyes!


Native = Full object,  ie the real original object
Proxy  = Proxy object, ie objects that derefence across machines till they reach the real orginal object


The why
What it does

The common API


"""
import sys
import inspect
import types
import pickle
import builtins

import global_consts
from global_consts import Rpyc_Exception

#==============================================================
# Globals
#==============================================================

#These are set during the initialization of this module

BASE_NETREF_METHODS = None        #This gets set after BaseNetref cls defined, as it contains it's base methods
NATIVE_BUILTIN_TYPE_DICT = None   # NATIVE_BUILTIN_TYPE_DICT is a  dictionary of builtin types,             {(cls.name, cls.module) : class }
PROXY_BUILTIN_TYPE_DICT = None    # PROXY_BUILTIN_TYPE_DICT is a dictionary of proxies of builtin types     {(cls.name, cls.module): proxy_class}

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

#Could use the meta class to gather

class NetrefMetaclass(type):
    """a metaclass just to customize the __repr__ of netref classes, 
    so repr(type(instance_base_net_ref)) will use this"""
    __slots__ = ()
    #base_methods = set()
    #def __new__(self, name, bases, dict):
    #    [meth for meth in dict(BaseNetref.__dict__) if hasattr(getattr(BaseNetref, meth), "__call__")]
    
    def __repr__(self):
        print("DEBUG_in_NetrefMetaclass_repr")
        if self.__module__:
            return "<netref class '{0}.{1}'>".format(self.__module__, self.__name__)
        else:
            return "<netref class '{0}'>".format(self.__name__,)

class BaseNetref(object):#, metaclass=NetrefMetaclass):
    """the base netref object, from which all netref classes derive
    
    Specfics
    ___conn__ : weakref.ref to the connection class, maybe should use a Weakvalue dict etc as they clean themselves up.
    ___oid__ :  object id
    
    ToDo
    #Could define here known methods so don't lookup ones that are unknown
    """
    __slots__ = ["____conn__", "____oid__", "____local_netref_attrs__", "__weakref__"]   # '__weakref__' so we support weak references to the instances
    
    def __init__(self, conn, oid):
        
        print("DEBUG_in_proxy_init")
        
        instance_attrs = ["____conn__", "____oid__", "____local_netref_attrs__"]
        local_attrs = ["__dict__", "__slots__", "__weakref__", "__new__"]                    #Not sure if I need these
        self.____local_netref_attrs__ = frozenset(instance_attrs + local_attrs + BASE_NETREF_METHODS)
        
        self.____conn__ = conn
        self.____oid__ = oid
        print("DEBUG_FINSIHED_proxy_init")
    
    @property
    def __class__(self):
        cls = object.__getattribute__(self, "locally_known_class")
        if cls is None:                    #<-------- I think this comes from the make_proxy_class
            cls = self.__getattr__("__class__")
        return cls
    
    @property
    def __doc__(self):
        doc = self.__getattr__("__doc__")
        return doc
    
    def __new__(cls, *args, **kwargs):
        #return super().__new__(cls, *args, **kwargs)
        return object.__new__(cls)   # object.__new__ does nothing with extra args, they still will be passed to init
    
    def __del__(self): # __del__ is a trick one to get right todo!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        try:
            asyncreq(self, global_consts.HANDLE_DEL)
        except BaseException as error:
            try:
                print("Warning: netref BaseNetref __del__")
                print(error.args)
            except AttributeError:
                print("on __del__ got AttributeError")
                pass
    
    def __getattribute__(self, attrname):
        """Here we try for local access, else resolved remotely using __getattr__"""
        # Should I use super here?  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        print("DEBUG_in_getattribute for", attrname)
        if attrname in object.__getattribute__(self, "____local_netref_attrs__"):
            print("DEBUG_getting local getattribute", attrname)
            return object.__getattribute__(self, attrname)
        else:
            print("DEBUG_getting remote getattribute", attrname)
            return object.__getattribute__(self, attrname)
            #return self.__getattr__(attrname)
    
    def __getattr__(self, attrname):
        """This is is a remote get attr call"""
        print("DEBUG_in_getattr for", attrname)
        return syncreq(self, global_consts.HANDLE_GETATTR, attrname)
    
    def __delattr__(self, attrname):
        """This method will only effect the remote proxy not the local one !!!!!!!!!!!!!!!!!!!!!!!! Todo"""
        if attrname in self.____local_netref_attrs__:
            object.__delattr__(self, attrname)
        else:
            syncreq(self, global_consts.HANDLE_DELATTR, attrname)
    
    def __setattr__(self, attrname, value):
        if attrname ==  "____local_netref_attrs__":
            print("DEBUG_setting ____local_netref_attrs__")
            object.__setattr__(self, attrname, value)
        elif attrname in self.____local_netref_attrs__:
            print("DEBUG_determined local, settattr for", attrname, value)
            object.__setattr__(self, attrname, value)
        else:
            syncreq(self, global_consts.HANDLE_SETATTR, attrname, value)
    
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
        print("string on proxy called")
        return syncreq(self, global_consts.HANDLE_STR)
    
    def __reduce_ex__(self, proto):          # support for pickle
        return pickle.loads, (syncreq(self, global_consts.HANDLE_PICKLE, proto),)

# This is a bit of a hack I don't really like it at all.
BASE_NETREF_METHODS = [meth for meth in dict(BaseNetref.__dict__) if hasattr(getattr(BaseNetref, meth), "__call__")]# + ["__new__"]


#==============================================================
#  IO
#==============================================================

def syncreq(proxy, handler, *args):
    """performs a synchronous request on the given proxy object"""
    print("DEBUG_Proxy sync request", proxy.____oid__, handler, args)
    conn = object.__getattribute__(proxy, "____conn__")
    oid = object.__getattribute__(proxy, "____oid__")
    return conn.sync_request(handler, oid, *args)   #<----------- Should the () beside conn be there????????????

def asyncreq(proxy, handler, *args):
    """performs an asynchronous request on the given proxy object, 
    retuning an AsyncResult"""
    print("DEBUG_Proxy Async request", proxy.____oid__, handler, args)
    conn = object.__getattribute__(proxy, "____conn__")
    oid = object.__getattribute__(proxy, "____oid__")
    return conn.async_request(handler, oid, *args)  #<------------------- Same as above ???????????????????

#==============================================================
#  Misc
#==============================================================

def _make_proxy_method(name, doc):
    """Make a proxy method that will call the original instance and return the result"""
    def method(_self, *args, **kwargs):
        kwargs = tuple(kwargs.items())
        print("DEBUG_in_method_call", name, doc)
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

_cls_from_builtins = [getattr(builtins, x) for x in dir(builtins)]
_flitered_builtins = [x for x in _cls_from_builtins if inspect.isclass(x) and not issubclass(x, BaseException)]

_cls_from_types = [getattr(types, x) for x in dir(types) if not x.startswith('__')]
_cls_from_other = [ Exception,
                type(int.__add__),      # wrapper_descriptor
                type((1).__add__),      # method-wrapper
                type(iter([])),         # listiterator
                type(iter(())),         # tupleiterator
                type(iter(range(10))),  # rangeiterator
                type(iter(set())),      # setiterator
                ]

_builtin_types = _flitered_builtins + _cls_from_types + _cls_from_other

#===============================================================================
#  Old way
#===============================================================================
# _builtin_types = [
#                #From builtins
#                Exception,
#                type, object,
#                bool,
#                list, dict, tuple, set, frozenset,
#                slice, range,
#                str, 
#                float, int, complex,
#                bytes, bytearray,
#                memoryview,
#                
#                #From types
#                types.BuiltinFunctionType, types.BuiltinMethodType,
#                types.MethodType, types.FunctionType, types.ModuleType, 
#                types.GetSetDescriptorType, types.LambdaType,
#                types.GeneratorType,
#                types.CodeType, types.FrameType, types.TracebackType, 
#                
#                #This looks like deep magic to me.!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#                type(int.__add__),      # wrapper_descriptor
#                type((1).__add__),      # method-wrapper
#                type(iter([])),         # listiterator
#                type(iter(())),         # tupleiterator
#                type(iter(range(10))),  # rangeiterator
#                type(iter(set())),      # setiterator
#                ]
#===============================================================================

def generate_proxy_builtin_type_dict(builtin_types):
    """ Here we make a cache of builtins some are in types module etc.
        This is used in protocal, I am guessing this is the remote type dict
        RENAME!!!!!!!!!!!!   remote_type_dict
    """
    _proxy_builtin_type_dict = {}
    for cls in builtin_types:
        typeinfo = (cls.__name__, cls.__module__)
        _proxy_builtin_type_dict[typeinfo] = make_proxy_class(cls.__name__, cls.__module__, inspect_methods(cls))
    return _proxy_builtin_type_dict


#==============================================================
# API
#==============================================================

#---------------------

def is_netref(obj):
    """Returns True if obi is an instance of BaseNetref"""
    return isinstance(obj, BaseNetref)

#---------------------

def make_proxy_class(clsname, modname, methods):
    """returns a netref class that with methods that will deference to original object when appropreate
    
    Create instances, supplying values for conn and oid, 
    these connection objects and object ids are used to find the orginal object
    
    #--------------------------
    Internal workings notes
    #--------------------------
    
    _local_netref_attrs is the method attributes local within proxy, (things that don't need a remote deref).
    name space will hold the method attributes not held in BaseNetref
    callable attributes are handled here as they need the ability to pass arguments etc.
    the class created can be instantioed with any connection 
    as it's init method contains ___conn__ and ___oid__
    if the __class__ object is unknown on this box, it is left blank 
    
    To Do
    # I changed this, bad idea to throw out stuff you don't understand
    #ns = {"__slots__": ()}  #Slots are used in classes instead of make __dict__. slightly faster can't add attrs.
    """
    
    namespace = {}
    
    for methname, methdoc in methods:
        if methname not in BASE_NETREF_METHODS:
            namespace[methname] = _make_proxy_method(methname, methdoc)
    
    namespace["__module__"] = modname
    if modname in sys.modules and hasattr(sys.modules[modname], clsname):
        namespace["locally_known_class"] = getattr(sys.modules[modname], clsname)
    elif (clsname, modname) in NATIVE_BUILTIN_TYPE_DICT:
        namespace["locally_known_class"] = NATIVE_BUILTIN_TYPE_DICT[clsname, modname]
    else:
        namespace["locally_known_class"] = None     # to be resolved by the instance, see __class__ property of BaseNetref
    
    return type(clsname, (BaseNetref,), namespace)

#--------------------

def inspect_methods(obj):
    """returns a tuple of ((method name: docstring)...) of all the methods in given obj
    ToDo
    
    Consider
    # inspect.getmro(cls)
    # inspect.getmembers(obj, ismethod)   "#isroutine is any kind of function or method"
    """
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
    return tuple(methods.items())

#--------------------

NATIVE_BUILTIN_TYPE_DICT = dict( ((typ.__name__, typ.__module__), typ) for typ in _builtin_types)
# NATIVE_BUILTIN_TYPE_DICT is a  dictionary of builtin types,             {(cls.name, cls.module) : class }

PROXY_BUILTIN_TYPE_DICT = generate_proxy_builtin_type_dict(_builtin_types) 
# PROXY_BUILTIN_TYPE_DICT is a dictionary of proxies of builtin types     {(cls.name, cls.module): proxy_class}
