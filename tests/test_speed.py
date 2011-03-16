import rpyc
import time
import threading
import unittest
import logging

from rpyc.utils.server import ThreadedServer
from rpyc.core.service import SlaveService

BIG = SMALL = connection = bgsrv = None
TARGET_HOSTNAME = "localhost" 
server = None

# import pushy
# def setup_pushy():
    # ''' connect and import the modules into globals'''
    # global BIG , SMALL , connection, server
    
    # server = threading.Thread(target=pushy.server.run)
    # server.start()
    
    # connection = pushy.client.connect("daemon:localhost")
    
    # BIG = connection.modules.win32con
    # SMALL = connection.modules.re
    
# def teardown_pushy():
    # '''  clean all services and stop connection '''
    # global BIG , SMALL , connection, server
    # del BIG 
    # del SMALL 
    # connection.close() 
    # del connection
    # del server
 
def setup_rpyc():
    ''' connect and import the modules into globals'''
    global BIG , SMALL , connection, bgsrv
     
    connection = rpyc.classic.connect_thread()
    #bgsrv = rpyc.BgServingThread(connection)
    bgsrv = None
    #connection.execute("import re; reload(asyncore)")
    #connection.execute("import msvcrt; reload(msvcrt)")
    
    BIG = connection.modules.win32con
    SMALL = connection.modules.re   

def teardown_rpyc():
    '''  clean all services and stop connection '''
    global BIG , SMALL , connection, bgsrv
    
    del BIG
    del SMALL  
    #bgsrv.stop()
    connection.close()
    del bgsrv
    del connection
    
def decorator(fn, module):
    def new(*args, **kargs):
        ret = fn(*args, **kargs)
        print "called: %s.%s returned: %s" % (module.__name__, fn.__name__,  str(ret))
        return ret
    return new
    
def add_decorators_to_module(moudle):    
    t = time.time()
    for c, v in moudle.__dict__.items():
        if hasattr(v, '__call__'):
            moudle.__dict__[c] = decorator(v, moudle)
    t1 = time.time()
    logging.debug("add_decorators_to_module [%s] : %0.6f" % 
        (moudle.__name__, (t1-t)) )

class Speed_Tests(unittest.TestCase):
    
    def setUp(self):
        setup_rpyc()
    def tearDown(self):
        teardown_rpyc()
    def test_import_locals_global_timing(self):
        def import_to_global(module):
            '''copy all public func from remote module into globals'''
            t = time.time()
            g = globals()
            for key, value in module.__dict__.items():
                if not key.startswith('_'):
                    g[key] = value
                else: pass
            t1 = time.time()
            logging.debug("import_to_global took [%d] : %0.6f" % 
                (len(module.__dict__.items()), (t1 - t)) )

        def import_to_local(module, loc):
            '''copy all public func from remote module into locals'''
            t = time.time()
            for key , value in module.__dict__.items():
                if not key.startswith('_'):
                    loc[key] = value
                else: pass
            t1 = time.time()
            logging.debug("import_to_local took [%d] : %0.6f" % 
                (len(module.__dict__.items()), (t1 - t)) )
        import_to_global(SMALL)
        import_to_local(SMALL, locals())
        import_to_global(BIG)
        import_to_local(BIG, locals())         

    def test_monkey_patching_remote(self):
        add_decorators_to_module(SMALL)
        add_decorators_to_module(BIG)

if __name__ == '__main__':
    
    FORMAT = "%(levelname)s: %(asctime)s | %(message)s"
    DATA_FORMAT = '%y/%m/%d %H:%M:%S'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt=DATA_FORMAT)
    unittest.main()