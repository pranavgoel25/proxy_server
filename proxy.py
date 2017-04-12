import socket
import threading
import signal
import sys
import hashlib
import os
import urllib2

config = {
    "HOST_NAME": "127.0.0.1",
    "BIND_PORT": 20000,
    "MAX_REQUEST_LEN": 102400,
    "CONNECTION_TIMEOUT": 15
}
flag = 0
blacklisted = ("google","geeksforgeeks","wikipedia")

class Server:
    def __init__(self, config):
        signal.signal(signal.SIGINT, self.shutdown)  # Shutdown on Ctrl+C
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Re-use the socket
        self.serverSocket.bind(
            (config['HOST_NAME'], config['BIND_PORT']))  # bind the socket to a public host, and a port
        self.serverSocket.listen(10)  # become a server socket
        self.__clients = {}

    def do_GET(self, site_name, port, request):
        m = hashlib.md5()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        cache_file = site_name.split('.')[0]
        if os.path.exists(cache_file + ".cache"):
            print "Cache hit"
            data = open(cache_file + ".cache").readlines()
            return data
        else:
            print "Cache miss"
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(config['CONNECTION_TIMEOUT'])
            s.connect((site_name, port))
            s.sendall(request)  # send request to webserver
            data_full = ""
            while 1:
                data = s.recv(config['MAX_REQUEST_LEN'])  # receive data from web server
                open(cache_file + ".cache", 'wb').writelines(data)
                data_full += data
                if s:
                    s.close()
            return data_full
        # m.update(self.path)
        # cache_filename = m.hexdigest() + ".cached"
        # if os.path.exists(cache_filename):
        #   print "Cache hit"
        #   data = open(cache_filename).readlines()
        #   return ("hit", data)
        # else:
        #   print "Cache miss"
        #   data = urllib2.urlopen("http:/" + self.path).readlines()
        #   open(cache_filename, 'wb').writelines(data)
        #   return ("miss", data)
        # return
        #self.send_response(200)
        #self.end_headers()
        #self.wfile.writelines(data)

    def listenForClient(self):
        while True:
            (clientSocket, client_address) = self.serverSocket.accept()  # Establish the connection
            d = threading.Thread(name="Client", target=self.proxy_thread,
                                 args=(clientSocket, client_address))
            d.setDaemon(True)
            d.start()
        self.shutdown(0, 0)

    def proxy_thread(self, conn, client_addr):
        request = conn.recv(config['MAX_REQUEST_LEN'])  # get the request from browser
        print request
        first_line = request.split('\n')[0]  # parse the first line
        url = first_line.split(' ')[1]  # get url

        # find the webserver and port
        http_pos = url.find("://")  # find pos of ://
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]  # get the rest of url

        port_pos = temp.find(":")  # find the port pos (if any)

        # find end of web server
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1
        if port_pos == -1 or webserver_pos < port_pos:  # default port
            port = 80
            webserver = temp[:webserver_pos]
        else:  # specific port
            port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]

        flag = 0

        try:
            print webserver, port
            print "Webserver is "
            print webserver
            for i in range(len(blacklisted)):
                if blacklisted[i] in webserver:
                    flag = 1
            # create a socket to connect to the web server
            # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # s.settimeout(config['CONNECTION_TIMEOUT'])
            # if flag is 0:
            #     s.connect((webserver, port))
            #     s.sendall(request)  # send request to webserver
            #
            # if flag is 0:
            #     while 1:
            #         data = s.recv(config['MAX_REQUEST_LEN'])  # receive data from web server
            #         if len(data) > 0:
            #             conn.send(data)  # send to browser
            #         else:
            #             break
            data = self.do_GET(webserver, port, request)
            str1 = ''.join(data)
            conn.send(str1)
        except socket.error as error_msg:
            print 'ERROR: ', client_addr, error_msg
            if conn:
                conn.close()

    def _getClientName(self, cli_addr):
        """ Return the clientName.
        """
        return "Client"

    def shutdown(self, signum, frame):
        """ Handle the exiting server. Clean all traces """
        self.serverSocket.close()
        sys.exit(0)


if __name__ == "__main__":
    server = Server(config)
    server.listenForClient()
