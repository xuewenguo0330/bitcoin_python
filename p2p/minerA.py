import socket,sys    
import os     
import threading

host = 'localhost'
miners = []
class Miner():
    def __init__(self):
        self.minerList=[]
    
    def start(self):
        port=int(input("Entrez votre port: "))
        miners.append(port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host,port))
        s.listen
        print("Attendre la connexion sur %s:%d"%(host,port))
        
        t=threading.Thread(target=self.init_connection, args=s)
        t.start()
        
    def init_connection(self,s):
        while True:
            client,addr=s.accept()
            print("miner demande de connecter %s:%d" %(addr[0],addr[1]))
            client.send(str.encode(str(self.minerList)))
            client.close()
            self.minerList.append(addr[0])
            print("les miners ont été connexté ", self.minerList)            
        
    def connect(self,port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.send(b'Hello from ' + str.encode(str(self.host)))
        peers = s.recv(1024)
        print("Connected peers: %s" % peers.decode())
        self.peers = self.peers + peers.decode().split(',')
        s.close()
        
        


if len( sys.argv ) != 2:
    print( "miner - V1.0" )
    print( "\tusage: python3 minerA.py nickname" )
    exit()

try:
  nickname = sys.argv[1]

  try: 
      p=Miner()
      p.start() 

  except socket.error:
      print("La connexion a échoué")
      
except ValueError: 
  print( "Error" )
  exit()
