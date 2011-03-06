import rpyc
import os.path
from rpyc.utils.authenticators import SSLAuthenticator
from rpyc.utils.server import ThreadedServer
import thread, time
import ssl

'''
created key like that
http://www.akadia.com/services/ssh_test_certificate.html
'''
class Test_SSL(object):
    def setup(self):
        key = os.path.join( os.path.dirname(__file__) , "server.key")
        cert =  os.path.join( os.path.dirname(__file__) , "server.crt")
        print cert, key
        authenticator = SSLAuthenticator(key, cert, ssl_version=ssl.PROTOCOL_SSLv2)
        self.server = ThreadedServer(rpyc.SlaveService, hostname = "localhost", 
            authenticator = authenticator, auto_register=False, port=18812)
        self.server.logger.quiet = True
        thread.start_new(self.server.start, ())
        time.sleep(1) # make sure the server has initialized, etc.


    def teardown(self):
        self.server.close()
        
    def test_ssl_conenction(self):
        c = rpyc.classic.ssl_connect("localhost", keyfile="server.key", certfile="server.crt",
            ssl_version=ssl.PROTOCOL_SSLv2, port = 18812)
        self.log("server credentials = %r", c.root.getconn()._config["credentials"])
        self.log("%s", c.modules.sys)
        c.close()