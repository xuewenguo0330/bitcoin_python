import socket
import threading

class Peer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.peers = []

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen()
        print("Listening for connections on %s:%d" % (self.host, self.port))
        accept_thread = threading.Thread(target=self.accept_connections)
        accept_thread.start()

    def accept_connections(self):
        while True:
            client, addr = s.accept()
            print("Connection from %s:%d" % (addr[0], addr[1]))
            client.send(b'Welcome to the P2P network')
            client.send(str.encode(str(self.peers)))
            client.close()
            self.peers.append(addr[0])
            print("Connected peers: %s" % self.peers)

    def connect(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.send(b'Hello from ' + str.encode(str(self.host)))
        peers = s.recv(1024)
        print("Connected peers: %s" % peers.decode())
        self.peers = self.peers + peers.decode().split(',')
        s.close()

if __name__ == '__main__':
    p = Peer('127.0.0.1', 12345)
    p.start()
    p.connect('127.0.0.1', 12346)
