
from nose.tools import raises

#import rpyc

#from rpyc.core.brine_3 import dumpable
#from rpyc.core.brine_3 import dump
#from rpyc.core.brine_3 import load
#from rpyc.core.brine_3 import _pickle
#from rpyc.core.brine_3 import Brine_Exception

from brine_3 import dumpable
from brine_3 import dump
from brine_3 import load
from brine_3 import _pickle
from brine_3 import Brine_Exception

def test_dump_load():
    x = ("he", 7, "llo", 8, (), 900, None, True, 18.2, 18.2j + 13, 
         slice(1, 2, 3), frozenset([5, 6, 7]), b"\11")
    assert dumpable(x)
    y = dump(x)
    z = load(y)
    print(x)
    print(y)
    print(z)
    assert x == z

@raises(Brine_Exception)
def test_undumpable():
    x = dump({1:2})

@raises(Brine_Exception)
def test_unloadable():
    x = ("he", 7, "llo", 8, (), 900, None, True, 18.2, 18.2j + 13, 
         slice(1, 2, 3), frozenset([5, 6, 7]), b"\11")
    y = dump(x)
    y = b"\02" + y
    z = load(y)

def test_pickle_direct():
    x = {1:2}
    y = _pickle(x)
    z =  load(b"\01"+y)
    assert x == z

@raises(Brine_Exception)
def test_unpickable():
    x = (NotImplemented)
    y = dump(x)

def test_dumpable():
    assert dumpable(1) == True
    assert dumpable((None, 1, 3)) == True
    assert dumpable((None, 1, {3:4})) == False