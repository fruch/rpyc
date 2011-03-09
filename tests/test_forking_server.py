import rpyc
import sys
from nose import SkipTest

from rpyc.utils.server import ForkingServer
from rpyc import SlaveService
import threading, time

class Test_ForkingServer(object):
    def setup(self):
        if sys.platform == "win32":
            raise SkipTest("This test doesn't work on win32")
            
        self.server = ForkingServer(SlaveService, 
            hostname = "localhost", port=18812, auto_register=False)
        self.server.logger.quiet = False
        t = threading.Thread(target=self.server.start)
        t.start()
        
    def teardown(self):
        self.server.close()
        
    def test_conenction(self):
        c = rpyc.classic.connect("localhost", port=18812)
        print c.modules.sys
        print c.modules["xml.dom.minidom"].parseString("<a/>")
        c.execute("x = 5")
        assert c.namespace["x"] == 5
        assert c.eval("1+x") == 6
        c.close()