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

class Netref_EG_Exception(Protocol_Exception):
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

#Had to change below, metaclass syntax has changed PEP 3115:
class BaseNetref(object, metaclass=NetrefMetaclass):
    """the base netref object, from which all netref classes derive
    
    Specfics
    ___conn__ : weakref.ref to the connection class, maybe should use a Weakvalue dict etc as they clean themselves up.
    ___oid__ :  object id
    """
    __slots__ = ["____conn__", "____oid__", "__weakref__"]   #Don't seem to use the __weakref__ slot!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    def __init__(self, conn, oid):
        self.____conn__ = conn
        self.____oid__ = oid
    
    def __del__(self):
        try:
            asyncreq(self, global_consts.HANDLE_DEL)
        except BaseException as error:
            try:
                print("Warning: netref BaseNetref __del__")
                print(error.args)
            except AttributeError:
                pass
    
    def __getattribute__(self, name):
        """Here we try for local access, else resolved remotely using __getattr__"""
        # Should I use super here?  Not sure about this code below could it not be simplier, is there a special case????
        #----- My version would be, need to check out why doc is resloved remote and why None given in class factory
        #
        if name in _local_netref_attrs:
            return object.__getattribute__(self, name)
        else:
            return self.__getattr__(name)
        #
        #-----
        
        #Doesn't this interecpt everything?!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
        #if name in _local_netref_attrs:
        #    if name == "__class__":
        #        cls = object.__getattribute__(self, "__class__")
        #        if cls is None:                    #<-------- I think this comes from the class_factory
        #            cls = self.__getattr__("__class__")
        #        return cls
        #    elif name == "__doc__":
        #        # Should doc resolve remotely?  Seems wrong to me!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        #        return self.__getattr__("__doc__")
        #    else:
        #        return object.__getattribute__(self, name)
        #else:
        #    return self.__getattr__(name)
    
    def __getattr__(self, name):
        """This is is a remote get attr call"""
        return syncreq(self, global_consts.HANDLE_GETATTR, name)
    
    def __delattr__(self, name):
        """ What the fuck!!!!!!!!!!!! will this just delete remotely and leave the rest"""
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Syncro problems
        #!!!!!!!!!!!!!!!!
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
        """Might need to iterate here to try and compare, anyway work to do here"""
        # Could deal with dictionary specficly
        # Could use pickle :)
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
#Removed support for __members__ and __methods__. 
#These are set in BaseNetref

#---
# Define attrs
#---

#Anything defined heregoes through
#return object.__getattribute__(self, name)
#not
#return syncreq(self, global_consts.HANDLE_GETATTR, name)

#Should this be dir(object) + special cases???????????????????????????????????????????????????????????????????????
#_local_netref_attrs = frozenset([
#    
#    #Defined in class
#    '__del__', '__getattribute__', '__setattr__', '__getattr__', '__delattr__',
#    '__dir__',  '__hash__', '__cmp__', 
#    '__repr__', '__str__', 
#    '__reduce_ex__',
#    
#    '__doc__', '__class__', '__init__','__new__',  '__reduce__',   #<----- from dir(object)
#    '__module__',                                                 #<-------- This comes from type, see dir(type)        ???
#    
#    #Are these not dangerous
#    '__dict__', '__slots__',
#    
#    # NetRef specfic
#    '____conn__', #Set in init
#    '____oid__',  #Set in init
#    
#    # Need to check don't seem to be defined in class above
#     '__weakref__', 
#    ])

_local_netref_attrs = frozenset([
                                 #Ones we define
                                 '__del__', '__getattribute__', '__setattr__', '__getattr__', '__delattr__',
                                 '__dir__',  '__hash__', '__cmp__', 
                                 '__repr__', '__str__', 
                                 '__reduce_ex__',
                                 
                                 #Ignore please
                                 '__dict__', '__slots__',
                                 
                                 #SPecfic ones
                                 '____conn__', '____oid__'
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
        __call__.__name__ = name
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
    
    #Name space seems to be missing all the local_netref attrs
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
    #getmembers #from the inpect module
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
    for name, attr in attrs.items():
        #Check why _local_netref_attrs is here !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if name not in _local_netref_attrs and hasattr(attr, "__call__"):
            methods[name] = inspect.getdoc(attr)
    
    #Return known methods, outside of local netref attrs
    return methods.items()  #Returns [(key, val), (key, val)]

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
    builtin_classes_cache[typeinfo] = class_factory(
                        cls.__name__, cls.__module__, inspect_methods(cls))

#Inspect methods is the class namespace
