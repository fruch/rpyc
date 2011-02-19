"""
The RPyC protocol 
"""
import sys
import select
import weakref
import itertools
import pickle
from threading import Lock

from rpyc.lib.lib import WeakValueDict, RefCountingColl

import brine_3 as brine
import vinegar_3 as vinegar
import netref_3 as netref
import global_consts
#from rpyc.core import global_consts, brine, vinegar, netref
#from rpyc.core.async import AsyncResult

#==============================================================
# Module Specfic Errors
#==============================================================

class Protocol_Exception(Rpyc_Exception):
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

class Protocol_Ping_Exception(Protocol_Exception):
    def __init__(self, err_string="PROTOCOL_PING_EXCEPTION"):
        super().__init__(err_string)

class Protocol_Unbox_Exception(Protocol_Exception):
    def __init__(self, err_string="PROTOCOL_UNBOX_EXCEPTION"):
        super().__init__(err_string)

#==============================================================
# Default Config
#==============================================================
#
# allow_safe_attrs
# allow_exposed_attrs
# allow_public_attrs
# allow_all_attrs
# safe_attrs
# exposed_prefix
# allow_getattr
# allow_setattr
# allow_delattr
# include_local_traceback
# instantiate_custom_exceptions
# import_custom_exceptions
# instantiate_oldstyle_exceptions
# propagate_SystemExit_locally
# allow_pickle
# connid
# credentials
# 
#==============================================================

DEFAULT_CONFIG = dict(
    # ATTRIBUTES
    allow_safe_attrs = True,
    allow_exposed_attrs = True,
    allow_public_attrs = False,
    allow_all_attrs = False,
    safe_attrs = set(['__abs__', '__add__', '__and__', '__cmp__', '__contains__', 
        '__delitem__', '__delslice__', '__div__', '__divmod__', '__doc__', 
        '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__', 
        '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
        '__idiv__', '__ifloordiv__', '__ilshift__', '__imod__', '__imul__', 
        '__index__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__',
        '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__', 
        '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__', 
        '__neg__', '__new__', '__nonzero__', '__oct__', '__or__', '__pos__', 
        '__pow__', '__radd__', '__rand__', '__rdiv__', '__rdivmod__', '__repr__',
        '__rfloordiv__', '__rlshift__', '__rmod__', '__rmul__', '__ror__', 
        '__rpow__', '__rrshift__', '__rshift__', '__rsub__', '__rtruediv__', 
        '__rxor__', '__setitem__', '__setslice__', '__str__', '__sub__', 
        '__truediv__', '__xor__', 'next', '__length_hint__', '__enter__', 
        '__exit__', ]),
    exposed_prefix = "exposed_",
    allow_getattr = True,
    allow_setattr = False,
    allow_delattr = False,
    # EXCEPTIONS
    include_local_traceback = True,
    instantiate_custom_exceptions = False,
    import_custom_exceptions = False,
    instantiate_oldstyle_exceptions = False, # which don't derive from Exception
    propagate_SystemExit_locally = False, # whether to propagate SystemExit locally or to the other party
    # MISC
    allow_pickle = False,
    connid = None,
    credentials = None,
    )

_connection_id_generator = itertools.count(1)


#==============================================================
# Main program
#==============================================================

class register_handler(object):
    """This is used to register the handlers in the _HANDLER dict in Connection"""
    def __init__(self, handler_constant, handler_register):
        self.handler_constant = handler_constant
        self.handler_register = handler_register
    
    def __call__(self, handler_method):
        self.handler_register[self.handler_constant] = handler_method
        return handler_method

class Connection(object):
    """The RPyC connection (also know as the RPyC protocol). 
    * service: the service to expose
    * channel: the channcel over which messages are passed
    * config: this connection's config dict (overriding parameters from the 
      default config dict)
    * _lazy: whether or not to initialize the service with the creation of the
      connection. default is True. if set to False, you will need to call
      _init_service manually later
    """
    
    _HANDLERS = {}
    
    def __init__(self, service, channel, config = {}, _lazy = False):
        """
        self._closed = bool status of connection, access through a property
        self._config = Settings for the connection, default = DEFAULT_CONFIG
        """
        self._closed = True
        
        self._config = DEFAULT_CONFIG.copy()
        self._config.update(config)
        if self._config["connid"] is None:
            self._config["connid"] = "conn%d" % (_connection_id_generator.next(),)
        
        self._channel = channel
        self._remote_root = None
        self._local_root = service(weakref.proxy(self))
        
        self._seqcounter = itertools.count()
        self._recvlock = Lock()
        self._sendlock = Lock()
        self._sync_replies = {}
        self._async_callbacks = {}
        self._local_objects = RefCountingColl()
        self._last_traceback = None
        self._proxy_cache = WeakValueDict()
        self._netref_classes_cache = {}
        
        if not _lazy:
            self._init_service()
        
        self._closed = False
    
    #---
    #  Startup
    #---
    def _init_service(self):
        """Dunno """ #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Seem to be a weak proxy to the service
        self._local_root.on_connect()
    
    #---
    #  Shutdown, cleanup and __del__
    #---
    def close(self, _catchall=True):
        if self._closed:
            return
        self._closed = True
        
        try:
            # Dunno this!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self._async_request(global_consts.HANDLE_CLOSE)
        except EOFError: 
            # Dunno this !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            pass
        except Exception:
            if not _catchall:
                raise
        finally:
            self._cleanup(_anyway=True)
    
    def _cleanup(self, _anyway=True):
        if self._closed and not _anyway:
            return
        self._closed = True
        self._channel.close()
        self._local_root.on_disconnect()
        self._sync_replies.clear()
        self._async_callbacks.clear()
        self._local_objects.clear()
        self._proxy_cache.clear()
        self._netref_classes_cache.clear()
        self._last_traceback = None
        self._last_traceback = None
        self._remote_root = None
        self._local_root = None
        #self._seqcounter = None
        #self._config.clear()
    
    def __del__(self):
        self.close()
    
    #---
    #Context manger
    #---
    def __enter__(self):
        """Context manager:: __enter__
        
        with Connection(...) as the_con:
            do stuff....
        """
        return self
    
    def __exit__(self, exc_class, exc_instance, traceback):
        """Context manager:: __exit__
        
        exc_class:        class object for exception that was raised
        exc_instance:     instance of that class that was raised
        exc_traceback:    traceback state of execution when exception was raised
        
        This class is width statement compatable
        
        with Connection(...) as the_con:
            do stuff....
        """
        self.close()
        
        if (exc_class, exc_instance, traceback) == (None, None, None):
            # Closed cleanly no exception was raised
            pass
        else:
            # An exception occured
            pass
            #return True to catch the error
            #return False to let them go, or implictly return None
    
    #------------------------------------------------------
    #  Representation 
    #------------------------------------------------------    
    
    def __repr__(self):
        a, b = object.__repr__(self).split(" object ")
        return "%s %r object %s" % (a, self._config["connid"], b)
    
    #------------------------------------------------------
    #  IO 
    #------------------------------------------------------
    
    @property
    def closed(self):
        """returns status of connection object"""
        return self._closed

    def fileno(self):
        return self._channel.fileno()
    
    def ping(self, data="the world is a vampire!" * 20, timeout=3):
        """assert that the other party is functioning properly"""
        res = self.async_request(global_consts.HANDLE_PING, data, timeout=timeout)
        if res.value != data:
            raise Protocol_Ping_Exception("echo mismatches sent data")
    
    def _send(self, msg, seq, args):
        data = brine.dump((msg, seq, args))
        self._sendlock.acquire()
        try:
            self._channel.send(data)
        finally:
            self._sendlock.release()

    def _send_request(self, handler, args):
        seq = self._seqcounter.next()
        self._send(global_consts.MSG_REQUEST, seq, (handler, self._box(args)))
        return seq

    def _send_reply(self, seq, obj):
        self._send(global_consts.MSG_REPLY, seq, self._box(obj))

    def _send_exception(self, seq, exctype, excval, exctb):
        exc = vinegar.dump(exctype, excval, exctb, 
            include_local_traceback=self._config["include_local_traceback"])
        self._send(global_consts.MSG_EXCEPTION, seq, exc)
    
    #------------------------------------------------------
    # Boxing
    #  In python everything is an object! and thus everything supports id and type
    #------------------------------------------------------
    def _box(self, obj):                  # Might be nice to have *obj
        """store a local object in such a way that it could be recreated on
        the remote party either by-value or by-reference"""
        if brine.dumpable(obj):
            return global_consts.LABEL_IMMUTABLE, obj
        
        elif type(obj) is tuple:
            return global_consts.LABEL_MUT_TUPLE, tuple(self._box(item) for item in obj)
        
        elif isinstance(obj, netref.BaseNetref) and obj.____conn__() is self:
            return global_consts.LABEL_EXISTING_PROXY, obj.____oid__
        
        else:
            self._local_objects.add(obj)
            cls = getattr(obj, "__class__", type(obj))
            return global_consts.LABEL_NEW_PROXY, (id(obj), cls.__name__, cls.__module__)
        
        # Should I check if obj in _local_objects, or empty it sometimes
        
        # inspect.getmodule (maybe this is better)
        # If can't get name or module what to do???
    
    def _unbox(self, package):
        """recreate a local object representation of the remote object: if the
        object is passed by value, just return it; if the object is passed by
        reference, create a netref to it"""
        label, value = package
        
        if label == global_consts.LABEL_IMMUTABLE:
            return value
        
        elif label == global_consts.LABEL_MUT_TUPLE:
            return tuple(self._unbox(item) for item in value)
        
        elif label == global_consts.LABEL_EXISTING_PROXY:
            return self._local_objects[value]
        
        elif label == global_consts.LABEL_NEW_PROXY:
            oid, clsname, modname = value
            if oid in self._proxy_cache:
                return self._proxy_cache[oid]
            proxy = self._netref_factory(oid, clsname, modname)
            self._proxy_cache[oid] = proxy
            return proxy
        
        else:
            raise Protocol_Unbox_Exception("Couldn't unbox, invalid label={label}".format(label=label))
    
    def _netref_factory(self, oid, clsname, modname):
        typeinfo = (clsname, modname)
        if typeinfo in self._netref_classes_cache:
            cls = self._netref_classes_cache[typeinfo]
        elif typeinfo in netref.builtin_classes_cache:
            cls = netref.builtin_classes_cache[typeinfo]
        else:
            info = self.sync_request(global_consts.HANDLE_INSPECT, oid)
            cls = netref.class_factory(clsname, modname, info)
            self._netref_classes_cache[typeinfo] = cls
        return cls(weakref.ref(self), oid)
    
    #------------------------------------------------------
    #  Dispatching
    #------------------------------------------------------
    def _dispatch_request(self, seq, raw_args):
        try:
            handler, args = raw_args
            args = self._unbox(args)
            res = self._HANDLERS[handler](self, *args)
        except KeyboardInterrupt:
            raise
        except:
            t, v, tb = sys.exc_info()
            self._last_traceback = tb
            if t is SystemExit and self._config["propagate_SystemExit_locally"]:
                raise
            self._send_exception(seq, t, v, tb)
        else:
            self._send_reply(seq, res)
    
    def _dispatch_reply(self, seq, raw):
        obj = self._unbox(raw)
        if seq in self._async_callbacks:
            self._async_callbacks.pop(seq)(False, obj)
        else:
            self._sync_replies[seq] = (False, obj)
    
    def _dispatch_exception(self, seq, raw):
        obj = vinegar.load(raw, 
            import_custom_exceptions=self._config["import_custom_exceptions"], 
            instantiate_custom_exceptions=self._config["instantiate_custom_exceptions"],
            instantiate_oldstyle_exceptions=self._config["instantiate_oldstyle_exceptions"])
        if seq in self._async_callbacks:
            self._async_callbacks.pop(seq)(True, obj)
        else:
            self._sync_replies[seq] = (True, obj)
    
    #------------------------------------------------------
    #  Serving
    #------------------------------------------------------
    def _recv(self, timeout, wait_for_lock):
        if not self._recvlock.acquire(wait_for_lock):
            return None
        try:
            if self._channel.poll(timeout):
                data = self._channel.recv()
            else:
                data = None
        except EOFError:
            self.close()
            raise
        finally:
            self._recvlock.release()
        return data
        
    def _dispatch(self, data):
        msg, seq, args = brine.load(data)
        if msg == global_consts.MSG_REQUEST:
            self._dispatch_request(seq, args)
        elif msg == global_consts.MSG_REPLY:
            self._dispatch_reply(seq, args)
        elif msg == global_consts.MSG_EXCEPTION:
            self._dispatch_exception(seq, args)
        else:
            raise ValueError("invalid message type: %r" % (msg,))

    def poll(self, timeout=0):
        """serve a single transaction, should one arrives in the given 
        interval. note that handling a request/reply may trigger nested 
        requests, which are all part of the transaction.
        
        returns True if one was served, False otherwise"""
        data = self._recv(timeout, wait_for_lock=False)
        if not data:
            return False
        self._dispatch(data)
        return True
    
    def serve(self, timeout=1):
        """serve a single request or reply that arrives within the given 
        time frame (default is 1 sec). note that the dispatching of a request
        might trigger multiple (nested) requests, thus this function may be 
        reentrant. returns True if a request or reply were received, False 
        otherwise."""
        
        data = self._recv(timeout, wait_for_lock=True)
        if not data:
            return False
        self._dispatch(data)
        return True
    
    def serve_all(self):
        """serve all requests and replies while the connection is alive"""
        try:
            while True:
                self.serve(0.1)
        except select.error:
            if not self.closed:
                raise
        except EOFError:
            pass
        finally:
            self.close()
    
    def poll_all(self, timeout=0):
        """serve all requests and replies that arrive within the given 
        interval. returns True if at least one was served, False otherwise"""

        at_least_once = False
        try:
            while self.poll(timeout):
                at_least_once = True
        except EOFError:
            pass
        return at_least_once
    
    #------------------------------------------------------
    #  Requests
    #------------------------------------------------------
    def sync_request(self, handler, *args):
        """send a request and wait for the reply to arrive"""
        seq = self._send_request(handler, args)
        while seq not in self._sync_replies:
            self.serve(0.1)
        isexc, obj = self._sync_replies.pop(seq)
        if isexc:
            print("dunno here")
            raise obj
        else:
            return obj
    
    def _async_request(self, handler, args=(), callback=(lambda a, b: None)):
        seq = self._send_request(handler, args)
        self._async_callbacks[seq] = callback

    def async_request(self, handler, *args, **kwargs):
        """send a request and return an AsyncResult object, which will 
        eventually hold the reply"""
        timeout = kwargs.pop("timeout", None)
        if kwargs:
            raise TypeError("got unexpected keyword argument %r" % (kwargs.keys()[0],))
        res = AsyncResult(weakref.proxy(self))
        self._async_request(handler, args, res)
        if timeout is not None:
            res.set_expiry(timeout)
        return res
    
    @property
    def root(self):
        """fetch the root object of the other party"""
        if self._remote_root is None:
            self._remote_root = self.sync_request(global_consts.HANDLE_GETROOT)
        return self._remote_root
    
    #------------------------------------------------------
    #  Attribute access
    #------------------------------------------------------
    def _check_attr(self, obj, name):
        if self._config["allow_exposed_attrs"]:
            if name.startswith(self._config["exposed_prefix"]):
                name2 = name
            else:
                name2 = self._config["exposed_prefix"] + name
            if hasattr(obj, name2):
                return name2
        if self._config["allow_all_attrs"]:
            return name
        if self._config["allow_safe_attrs"] and name in self._config["safe_attrs"]:
            return name
        if self._config["allow_public_attrs"] and not name.startswith("_"):
            return name
        return False
    
    def _access_attr(self, oid, name, args, overrider, param, default):
        if type(name) is not str:
            raise TypeError("attr name must be a string")
        obj = self._local_objects[oid]
        accessor = getattr(type(obj), overrider, None)
        if accessor is None:
            name2 = self._check_attr(obj, name)
            if not self._config[param] or not name2:
                raise AttributeError("cannot access %r" % (name,))
            accessor = default
            name = name2
        return accessor(obj, name, *args)
    
    #------------------------------------------------------
    #  Handlers
    #------------------------------------------------------
    @register_handler(global_consts.HANDLE_PING, _HANDLERS)
    def _handle_ping(self, data):
        return data
    
    @register_handler(global_consts.HANDLE_CLOSE, _HANDLERS)
    def _handle_close(self):
        self._cleanup()
    
    @register_handler(global_consts.HANDLE_GETROOT, _HANDLERS)
    def _handle_getroot(self):
        return self._local_root
    
    @register_handler(global_consts.HANDLE_DEL, _HANDLERS)
    def _handle_del(self, oid):
        self._local_objects.decref(oid)
    
    @register_handler(global_consts.HANDLE_REPR, _HANDLERS)
    def _handle_repr(self, oid):
        return repr(self._local_objects[oid])
    
    @register_handler(global_consts.HANDLE_STR, _HANDLERS)
    def _handle_str(self, oid):
        return str(self._local_objects[oid])
    
    @register_handler(global_consts.HANDLE_CMP, _HANDLERS)
    def _handle_cmp(self, oid, other):
        # cmp() might enter recursive resonance... yet another workaround
        #return cmp(self._local_objects[oid], other)
        obj = self._local_objects[oid]
        try:
            return type(obj).__cmp__(obj, other)
        except TypeError:
            return NotImplemented
    
    @register_handler(global_consts.HANDLE_HASH, _HANDLERS)
    def _handle_hash(self, oid):
        return hash(self._local_objects[oid])
    
    @register_handler(global_consts.HANDLE_CALL, _HANDLERS)
    def _handle_call(self, oid, args, kwargs):
        return self._local_objects[oid](*args, **dict(kwargs))
    
    @register_handler(global_consts.HANDLE_DIR, _HANDLERS)
    def _handle_dir(self, oid):
        return tuple(dir(self._local_objects[oid]))
    
    @register_handler(global_consts.HANDLE_INSPECT, _HANDLERS)
    def _handle_inspect(self, oid):
        return tuple(netref.inspect_methods(self._local_objects[oid]))
    
    @register_handler(global_consts.HANDLE_GETATTR, _HANDLERS)
    def _handle_getattr(self, oid, name):
        return self._access_attr(oid, name, (), "_rpyc_getattr", 
                                 "allow_getattr", getattr)
    
    @register_handler(global_consts.HANDLE_DELATTR, _HANDLERS)
    def _handle_delattr(self, oid, name):
        return self._access_attr(oid, name, (), "_rpyc_delattr", 
                                 "allow_delattr", delattr)
    
    @register_handler(global_consts.HANDLE_SETATTR, _HANDLERS)
    def _handle_setattr(self, oid, name, value):
        return self._access_attr(oid, name, (value,), "_rpyc_setattr", 
                                 "allow_setattr", setattr)
    
    @register_handler(global_consts.HANDLE_CALLATTR, _HANDLERS)
    def _handle_callattr(self, oid, name, args, kwargs):
        return self._handle_getattr(oid, name)(*args, **dict(kwargs))
    
    @register_handler(global_consts.HANDLE_PICKLE, _HANDLERS)
    def _handle_pickle(self, oid, proto):
        if not self._config["allow_pickle"]: 
            raise ValueError("pickling is disabled")
        return pickle.dumps(self._local_objects[oid], proto)
    
    @register_handler(global_consts.HANDLE_BUFFITER, _HANDLERS)
    def _handle_buffiter(self, oid, count):
        items = []
        obj = self._local_objects[oid]
        for i in xrange(count):
            try:
                items.append(obj.next())
            except StopIteration:
                break
        return tuple(items)
