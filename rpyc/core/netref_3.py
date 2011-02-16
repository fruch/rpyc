"""
NetRef - transparent network references implementation.

SURGEON GENERAL'S WARNING: Black magic is known to causes Lung Cancer,
Heart Disease, Emphysema, and May Complicate Pregnancy. Close your eyes!
"""
import sys
import inspect
import types
import pickle

#import cPickle as pickle   #This is now a default in python3 !!!!!!!!

from rpyc.core import globals as global_consts


class NetrefMetaclass(type):
    """a metaclass just to customize the __repr__ of netref classes"""
    __slots__ = ()
    def __repr__(self):
        if self.__module__:
            return "<netref class '%s.%s'>" % (self.__module__, self.__name__)
        else:
            return "<netref class '%s'>" % (self.__name__,)

#Had to change below, metaclass syntax has changed PEP 3115:
#class BaseNetref(object):
class BaseNetref(object, metaclass=NetrefMetaclass):
    """the base netref object, from which all netref classes derive"""
    #__metaclass__ = NetrefMetaclass         
    __slots__ = ["____conn__", "____oid__", "__weakref__"]

    def __init__(self, conn, oid):
        self.____conn__ = conn
        self.____oid__ = oid

    def __del__(self):
        try:
            asyncreq(self, global_consts.HANDLE_DEL)
        except:
            pass
    
    def __getattribute__(self, name):
        if name in _local_netref_attrs:
            if name == "__class__":
                cls = object.__getattribute__(self, "__class__")
                if cls is None:
                    cls = self.__getattr__("__class__")
                return cls
            elif name == "__doc__":
                return self.__getattr__("__doc__")
            elif name == "__members__": # sys.version_info < (2, 6)
                return self.__dir__()
            else:
                return object.__getattribute__(self, name)
        else:
            return syncreq(self, global_consts.HANDLE_GETATTR, name)
    
    def __getattr__(self, name):
        return syncreq(self, global_consts.HANDLE_GETATTR, name)
    
    def __delattr__(self, name):
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
    
    # support for metaclasses
    def __hash__(self):
        return syncreq(self, global_consts.HANDLE_HASH)
    def __cmp__(self, other):
        return syncreq(self, global_consts.HANDLE_CMP, other)
    def __repr__(self):
        return syncreq(self, global_consts.HANDLE_REPR)
    def __str__(self):
        return syncreq(self, global_consts.HANDLE_STR)
    
    # support for pickle
    def __reduce_ex__(self, proto):
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


#######################################



#===========Might need to do ================
#'__eq__'
#'__gt__'
#'__bases__' #Shows one level away subclasses 
#'__mro__'   #Shows the relsoution path for a class
# Have no clue what ___oid__ and ___conn__ are ?
#These are set in BaseNetref

#---
# Define attrs
#---
_local_netref_attrs = frozenset([
    '__del__', '__getattribute__', '__setattr__', '__getattr__',
    '__dir__',  '__hash__', '__cmp__', 
    '__repr__', '__str__', 
    '__reduce_ex__',
    # Unknown
    '____conn__', #Set in init
    '____oid__',  #Set in init
    # Need to check don't seem to be defined in class above
    '__delattr__', '__members__', '__methods__', '__weakref__', '__class__', '__dict__', '__slots__',
    '__reduce__', '__init__', '__metaclass__', '__module__', '__new__', '__doc__',
    ])

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

#---
#  builtin types
#---

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

def _make_method(name, doc):
    if name == "__call__":
        def __call__(_self, *args, **kwargs):
            kwargs = tuple(kwargs.items())
            return syncreq(_self, global_consts.HANDLE_CALL, args, kwargs)
        #why no __call__.__name__ = name ???????????????
        __call__.__doc__ = doc
        return __call__
    else:
        def method(_self, *args, **kwargs):
            kwargs = tuple(kwargs.items())
            return syncreq(_self, global_consts.HANDLE_CALLATTR, name, args, kwargs)
        method.__name__ = name
        method.__doc__ = doc
        return method

def class_factory(clsname, modname, methods):
    #Dunno why __slots__ below??????????? why not just {}
    #ns = {"__slots__": ()}  #Slots are used in classes instead of make __dict__. slightly faster can't add attrs.
    
    ns = {}
    
    for name, doc in methods:
        if name not in _local_netref_attrs:
            ns[name] = _make_method(name, doc)
    
    ns["__module__"] = modname
    if modname in sys.modules and hasattr(sys.modules[modname], clsname):
        ns["__class__"] = getattr(sys.modules[modname], clsname)
    elif (clsname, modname) in _normalized_builtin_types:
        ns["__class__"] = _normalized_builtin_types[clsname, modname]
    else:
        ns["__class__"] = None            # to be resolved by the instance
    
    return type(clsname, (BaseNetref,), ns)

def inspect_methods(obj):
    """returns a list of (method name, docstring) tuples of all the methods of 
    the given object not already in _local_netref_attrs"""
    methods = {}
    attrs = {}
    
    #Just a little debug
    if __debug__:
        try:
            type(obj).__mro__
        except AttributeError:
            print("Warning: This object is incompatable doesn't seem to have methods")
            return None
    
    # Get the inhertance tree, mro = method resolution order
    
    # Meta classes are all subclasses of type
    # Python goes futher than this, all classes are instances of type, instance of class is not.
    # To detect is a class is a metaclass use issubclass(cls, type)
    
    if isinstance(obj, type):                           # This asks is this a class.
        #Duplicated mro will be taken out at dict stage.
        #do I need the first bit to cover metaclasses?
        mros = list(reversed(type(obj).__mro__)) + list(reversed(obj.__mro__)) 
    else:                                               # Else must be an instance
        mros = reversed(type(obj).__mro__)
    
    #Iterate over all base classes and add an entry for all possible attributes
    for basecls in mros:
        attrs.update(basecls.__dict__)
    
    #Iterate over all attributes and filter out the call able ones.
    for name, attr in attrs.iteritems():
        if name not in _local_netref_attrs and hasattr(attr, "__call__"):
            methods[name] = inspect.getdoc(attr)
    
    #Return known methods, outside of local netref attrs
    return methods.items()  #Returns [(key, val), (key, val)]

_normalized_builtin_types = dict( ((t.__name__, t.__module__), t) for t in _builtin_types)

#Here we make a cache of builtins some are in types module etc.
builtin_classes_cache = {}
for cls in _builtin_types:
    builtin_classes_cache[cls.__name__, cls.__module__] = class_factory(
        cls.__name__, cls.__module__, inspect_methods(cls))
