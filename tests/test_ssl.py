import rpyc
import os.path
from rpyc.utils.authenticators import SSLAuthenticator
from rpyc.utils.server import ThreadedServer
from rpyc import SlaveService
import threading, time
import ssl

'''
created key like that
http://www.akadia.com/services/ssh_test_certificate.html

openssl req -newkey rsa:1024 -nodes -keyout mycert.pem -out mycert.pem
'''
class Test_SSL_classic(object):
    def setup(self):
        self.key = os.path.join( os.path.dirname(__file__) , "server.key")
        self.cert =  os.path.join( os.path.dirname(__file__) , "server.crt")
        print self.cert, self.key
        
        authenticator = SSLAuthenticator(self.key, self.cert, ssl_version=ssl.PROTOCOL_TLSv1)
        self.server = ThreadedServer(SlaveService, hostname = "localhost",port = 18812, 
            auto_register=False, authenticator = authenticator,  reuse_addr=True)
        self.server.logger.quiet = False
        t = threading.Thread(target=self.server.start)
        t.start()
        self.conn = rpyc.classic.ssl_connect("localhost", port = 18812, 
            keyfile=self.key, certfile=self.cert,
            ssl_version=ssl.PROTOCOL_TLSv1)
        

    def teardown(self):
        self.conn.close()
        self.server.close()
        time.sleep(1)
        
    def test_ssl_conenction(self):
        
        print self.conn.root.modules.sys
        print self.conn.modules["xml.dom.minidom"].parseString("<a/>")
        self.conn.execute("x = 5")
        assert self.conn.namespace["x"] == 5
        assert self.conn.eval("1+x") == 6
        self.conn.close()

import math

on_connect_called = False
on_disconnect_called = False

class MyService(rpyc.Service):
    def on_connect(self):
        global on_connect_called
        on_connect_called = True

    def on_disconnect(self):
        global on_disconnect_called
        on_disconnect_called = True
    
    def exposed_distance(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return math.sqrt((x2-x1)**2 + (y2-y1)**2)
        
class Test_SSL_Service(object):
    
    def setup(self):
        self.key = os.path.join( os.path.dirname(__file__) , "server.key")
        self.cert =  os.path.join( os.path.dirname(__file__) , "server.crt")
        print self.cert, self.key
        
        authenticator = SSLAuthenticator(self.key, self.cert, ssl_version=ssl.PROTOCOL_TLSv1)
        self.server = ThreadedServer(MyService, hostname = "localhost",port = 18812, 
            auto_register=False, authenticator = authenticator, reuse_addr=True)
        self.server.logger.quiet = False
        t = threading.Thread(target=self.server.start)
        t.start()
        self.conn = rpyc.ssl_connect("localhost", port = 18812, 
            keyfile=self.key, certfile=self.cert,
            ssl_version=ssl.PROTOCOL_TLSv1)
            
    def teardown(self):
        self.conn.close()
        self.server.close()
        time.sleep(1)
        
    def test_calling_service(self):
        assert self.conn.root.distance((2,7), (5,11)) == 5