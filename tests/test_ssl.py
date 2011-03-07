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
        self.server = ThreadedServer(SlaveService, hostname = "localhost",port = 18815, auto_register=False, reuse_addr = True)
            #authenticator = authenticator, port=18815)
        self.server.logger.quiet = False
        t = threading.Thread(target=self.server.start)
        t.start()
        #time.sleep(1) # make sure the server has initialized, etc.


    def teardown(self):
        self.server.close()
        
    def test_ssl_conenction(self):
        c = rpyc.connect("localhost", port = 18815)
        #, keyfile=self.key, certfile=self.cert,
        #    ssl_version=ssl.PROTOCOL_TLSv1 ,port = 18815)
        print dir(c)
        print c.modules.sys
        print c.modules["xml.dom.minidom"].parseString("<a/>")
        c.execute("x = 5")
        assert c.namespace["x"] == 5
        assert c.eval("1+x") == 6
        c.close()