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
class Test_SSL(object):
    def setup(self):
        self.key = os.path.join( os.path.dirname(__file__) , "server.key")
        self.cert =  os.path.join( os.path.dirname(__file__) , "server.crt")
        print self.cert, self.key
        
        authenticator = SSLAuthenticator(self.key, self.cert, ssl_version=ssl.PROTOCOL_TLSv1)
        self.server = ThreadedServer(SlaveService, hostname = "localhost",port = 18812, 
            auto_register=False, authenticator = authenticator)
        self.server.logger.quiet = False
        t = threading.Thread(target=self.server.start)
        t.start()

    def teardown(self):
        self.server.close()
        
    def test_ssl_conenction(self):
        c = rpyc.classic.ssl_connect("localhost", port = 18812, 
            keyfile=self.key, certfile=self.cert,
            ssl_version=ssl.PROTOCOL_TLSv1)
        print c.modules.sys
        print c.modules["xml.dom.minidom"].parseString("<a/>")
        c.execute("x = 5")
        assert c.namespace["x"] == 5
        assert c.eval("1+x") == 6
        c.close()