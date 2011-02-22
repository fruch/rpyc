"""
various library utilities (also for compatibility with python2.4)
"""
from weakref import WeakValueDictionary     # Just using the inbuilt one since moved to py3, old one at bottom
import weakref
from collections import Counter
from threading import Lock, RLock, Event
from collections import MutableMapping

def callable(thing):
    """This function was replaced in python3 with the below"""
    return hasattr(thing, '__call__')

class Locking_dict(MutableMapping):
    """note to self,  what is weak about this, should the weak stuff be included, else call it a locking dictionary
    
    Could do something with descriptor to implement count
    
    Could have just inherited dict and changed __get, set, del
    """
    def __init__(self):
        self._lock = Lock()
        self._obj_dict = {}
    
    def __getitem__(self, oid):
        with self._lock:
            print("locked: (get)")
            ret_val = self._obj_dict.__getitem__(oid)
        print("unlocked: (get)")
        return ret_val
    
    def __setitem__(self, oid, value):
        with self._lock:
            print("locked: (set)")
            ret_val = self._obj_dict.__setitem__(oid, value)
        print("unlocked: (set)")
        return ret_val
    
    def __delitem__(self, oid):
        with self._lock:
            print("locked: del")
            ret_val = self._obj_dict.__delitem__(oid)
        print("unlocked: del")
        return ret_val
    
    def __iter__(self):
        """Return a generator which iterates over known keys at time first called"""
        with self._lock:
            oids = self._obj_dict.keys()
        return (oid for oid in oids)
    
    def __len__(self):
        with self._lock:
            print("locked: len")
            length = len(self._obj_dict)
        print("unlocked: len")
        return length
    
    def __repr__(self):
        with self._lock:
            print("locked: repr")
            repr_string = repr(self._obj_dict)
        print("unlocked: repr")
        return repr_string
    
    def do_nothing_place_holder(self, oid):
        pass

#===============================================================================
# 
# # Orginal version   Only protocoll uses this, and only add clear and getitem and decref are ever called, never seems to use the count either
# class RefCountingColl(object):
#    """a set-like object that implements refcounting on its contained objects"""
#    __slots__ = ("_lock", "_dict")
#    def __init__(self):
#        self._lock = Lock()
#        self._dict = {}
#    
#    def __repr__(self):
#        return repr(self._dict)
#    
#    def add(self, obj):
#        self._lock.acquire()
#        try:
#            key = id(obj)
#            slot = self._dict.get(key, None)
#            if slot is None:
#                slot = [obj, 0]
#            else:
#                slot[1] += 1
#            self._dict[key] = slot
#        finally:
#            self._lock.release()
#    
#    def clear(self):
#        self._lock.acquire()
#        try:
#            self._dict.clear()
#        finally:
#            self._lock.release()
#    
#    def decref(self, key):
#        self._lock.acquire()
#        try:
#            slot = self._dict[key]
#            if slot[1] <= 1:
#                del self._dict[key]
#            else:
#                slot[1] -= 1
#                self._dict[key] = slot
#        finally:
#            self._lock.release()
#    
#    def __getitem__(self, key):
#        self._lock.acquire()
#        try:
#            return self._dict[key][0]
#        finally:
#            self._lock.release()
# 
# 
# 
#    #def incref(self, key):  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#    #    self[key] += 1
#    # 
#    #def decref(self, key):
#    #    if self[key] > 1:
#    #        self[key] -= 1
#    #    else:
#    #        self[key] = 0
#===============================================================================

#===============================================================================
#  Removed from Origial version using the builtin instead, keeping just incase
#  need to implement a thread safe one later
#===============================================================================
# #Original Version
# class WeakValueDict(object):
#    """a light-weight version of weakref.WeakValueDictionary"""
#    __slots__ = ("_dict",)
#    def __init__(self):
#        self._dict = {}
#    def __repr__(self):
#        return repr(self._dict)
#    def __iter__(self):
#        return self.iterkeys()
#    def __len__(self):
#        return len(self._dict)
#    def __contains__(self, key):
#        try:
#            self[key]
#        except KeyError:
#            return False
#        else:
#            return True
#    def get(self, key, default = None):
#        try:
#            return self[key]
#        except KeyError:
#            return default
#    def __getitem__(self, key):
#        obj = self._dict[key]()
#        if obj is None:
#            raise KeyError(key)
#        return obj
#    def __setitem__(self, key, value):
#        def remover(wr, _dict = self._dict, key = key):
#            _dict.pop(key, None)
#        self._dict[key] = weakref.ref(value, remover)
#    def __delitem__(self, key):
#        del self._dict[key]
#    def iterkeys(self):
#        return self._dict.iterkeys()
#    def keys(self):
#        return self._dict.keys()
#    def itervalues(self):
#        for k in self:
#            yield self[k]
#    def values(self):
#        return list(self.itervalues())
#    def iteritems(self):
#        for k in self:
#            yield k, self[k]
#    def items(self):
#        return list(self.iteritems())
#    def clear(self):
#        self._dict.clear()
# 
# #My replacement
# class WeakValueDict2(dict):
#    """My version of above"""
#    def __init__(self, *args, **kwargs):
#        super().__init__(self, *args, **kwargs)
#    
#    def __setitem__(self, key, value):
#        def remover(weak_ref, _dict = super(), key = key):
#            """Callback to remove reference
#            
#            This function is not deleted, seems like shifting the problem, goes it later get gced?"""
#            print("In callback")
#            _dict.pop(key)
#        super().__setitem__(key, weakref.ref(value, remover))
#===============================================================================

