#!/usr/bin/env python
# coding: utf-8

import socket, threading, sys, json
from merkle_t import check_merkle_proof

miners = []
nick_name = ""
transactions = {}
trans_id = 0

def handle_messages(miner_name, miner):
    """
    Handle the messages sent by the miners.
    """
    global miners, transactions
    while True:
        try:
            msg = miner.recv(1024)
            if msg:
                msg_split = msg.decode().split()
                if msg_split[0] == "/ID":
                    transactions[msg_split[1]] = " ".join(msg_split[2:])               
                    print("Transaction id is ", msg_split[1])
                elif msg_split[0] == "REP":
                    if msg_split[1] == "FALSE":
                        print(" ".join(msg_split[2:]))
                    else:
                        head = msg_split[2]
                        mp = json.loads("".join(msg_split[3:]))
                        print("Verifying if ", "".join(transactions[trans_id]), " is in the blockchain...")
                        trans_args = transactions[trans_id].split()
                        transaction = {
                                        "id": int(trans_id),
                                        "sender":trans_args[1],
                                        "recipient":trans_args[2],
                                        "value":trans_args[3],
                                    }
                        print(check_merkle_proof(head, mp, transaction))

                else:
                    miners = msg_split
                    print("List of miners:", miners)
                
            else:
                print("Miner", miner_name, "closed")
                miner.close()

                if len(miners) > 0:
                    print("Connecting to new miner...")
                    connect_miner(int(miners.pop(0)))
                else:
                    print("No available miner found")
                    
        except Exception as e:
            print('Error handling message from miner:', e)
            miner.close()
            break


def connect_miner(miner_name):
    """
    Connect to a miner
    """
    global nick_name, trans_id
    
    try:
        miner = socket.socket()
        miner.connect(('localhost', miner_name))

        miner.send(nick_name.encode())
        print('Connected to miner', miner_name)

        threading.Thread(target=handle_messages, args=[miner_name, miner]).start()

        while True:
            msg = input()
            if(msg.split()[0]=="/LIST"):
                print("List of transactions :\n", transactions)
            else:
                if msg.split()[0] == "/MP":
                    trans_id = msg.split()[1]
                miner.send(msg.encode())
            
    except Exception as e:
        print('Error connecting to miner socket:', e)
        return


def wallet():
    global nick_name
    nick_name = sys.argv[1]
    miner_name = int(sys.argv[2])
    connect_miner(miner_name)


wallet()

