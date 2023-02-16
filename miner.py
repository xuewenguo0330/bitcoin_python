#!/usr/bin/env python
# coding: utf-8

import socket, threading, sys, time
import hashlib
import json
import json
from merkle_t import *

# Global variables
miners = {}
wallets = {}
miner_name = ""
response = ""
blockchain = ""
MINING_REWARD = 1
MINING_DIFFICULTY = 2
nb_trans = 0
trans_block = {}
len_chain_max = 0
merkle_trees = {}

class BlockChain(object):
    """ Main BlockChain class """
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.id_trans = 0
        # create the genesis block
        self.new_block(previous_hash='00', nonce=0)
    

    @staticmethod
    def hash(block):
        # hashes a block
        # also make sure that the transactions are ordered otherwise we will have insonsistent hashes!
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def new_block(self, nonce, previous_hash=None):
        global merkle_trees
        # construct the merkle tree
        merkle_tree = ""
        if len(self.current_transactions ) > 1:
            merkle_tree = build_merkle_tree(self.current_transactions)

        # creates a new block in the blockchain
        block = {
            'index': len(self.chain)+1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'nonce': nonce,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        merkle_trees[block['previous_hash']] = merkle_tree

        # reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

    @property
    def last_block(self):
        # returns last block in the chain
        return self.chain[-1]

    def new_transaction(self, idx, sender, recipient, amount):
        # adds a new transaction into the list of transactions
        # these transactions go into the next mined block
        self.current_transactions.append({
            "id": idx,
            "sender":sender,
            "recipient":recipient,
            "value":amount,
        })
        next_block_idx = int(self.last_block['index'])+1
        print("Transaction will be added to the Block ", next_block_idx)
        return next_block_idx

    def proof_of_work(self):
        """
        Proof of work algorithm
        """
        last_block = self.chain[-1]
        last_hash = self.hash(last_block)

        nonce = 0
        while self.valid_proof(self.current_transactions, last_hash, nonce) is False:
            nonce += 1

        return nonce

    def valid_proof(self, transactions, last_hash, nonce, difficulty=MINING_DIFFICULTY):
        """
        Check if a hash value satisfies the mining conditions. This function is used within the proof_of_work function.
        """
        guess = (str(transactions)+str(last_hash)+str(nonce)).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:difficulty] == '0'*difficulty

    def valid_chain(self, chain):
        """
        check if a bockchain is valid
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            # Delete the reward transaction
            transactions = block['transactions'][:-1]
            if not self.valid_proof(transactions, block['previous_hash'], block['nonce'], MINING_DIFFICULTY):
                return False

            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """
        Resolve conflicts between blockchain's nodes
        by replacing our chain with the longest one in the network.
        """
        global response
        response = ""
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in miners:
            miners[node].send(("/CHAIN").encode())
            #time.sleep(0.2)

            while not response:
                pass

            #print("chain of other miner ", response)
            length = len(response)
            chain = response

            # Check if the length is longer and the chain is valid
            if length > max_length:
                max_length = length
                new_chain = chain
            
            response = ""
        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

###############################################################################################
def resolve_conflicts():
    """
    Update the current chain
    """
    #print("resolving conflicts...")
    replaced = blockchain.resolve_conflicts()

    if replaced:
        print('Our chain was replaced')
        # reset the current list of transactions
        blockchain.current_transactions = []
        return True
    else:
        print('Our chain is authoritative')
        return False


def get_last_id_trans():
    """
    Get the id of the last transaction.
    """
    global response, len_chain_max
    len_chain_max = len(blockchain.chain)
    response = ""
    for node in miners:
        miners[node].send(("/ID").encode())
        #time.sleep(0.2)

        while not response:
            pass
        
        id_trans = int(response[0])
        len_chain = int(response[1])
        if id_trans > blockchain.id_trans:
            blockchain.id_trans = id_trans  
        if len_chain > len(blockchain.chain):
            len_chain_max = len_chain

    response = "" 
    blockchain.id_trans += 1
    print("The id of the next transaction is ", blockchain.id_trans)

def mine():
    """
    Add a new block to the chain
    """
    global miner_name, blockchain
    print("Checking if the blockchain is up to date..")
    if resolve_conflicts():
        print("Nothing to mine")
    else:
        # first we need to run the proof of work algorithm to calculate the new proof..
        last_block = blockchain.last_block
        proof = blockchain.proof_of_work()

        # we must recieve reward for finding the proof in form of receiving 1 Coin
        get_last_id_trans()
        blockchain.new_transaction(
        idx = blockchain.id_trans,
        sender=0,
        recipient=miner_name,
        amount=1,
        )

        # forge the new block by adding it to the chain
        previous_hash = blockchain.hash(last_block)
        block = blockchain.new_block(proof, previous_hash)

        resp = {
        'message': "Forged new block.",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['nonce'],
        'previous_hash': block['previous_hash'],
        }
        print(resp)


def remove_connection(nick_name):
    """
    Remove the connection of a miner or a wallet
    """
    if nick_name in miners.keys():
        miners[nick_name].close()
        miners.pop(nick_name)
        print("Miner", nick_name, "is removed")
        print("List of miners:", list(miners.keys()))
        send_list_miner()
        
    if nick_name in wallets.keys():
        wallets[nick_name].close()
        wallets.pop(nick_name)
        print("wallet", nick_name, "is removed")


def send_list_miner():
    """
    Send the list of miners to the wallets
    """
    for w in wallets.keys():
        wallets[w].send(" ".join(list(miners.keys())).encode())


def connect_to_neighbor(m):
    """
    Connect the miner m to the others miners
    """
    global miner_name
    if m not in miners.keys():
        try:
            miner_nb = socket.socket()
            miner_nb.connect(('localhost', int(m)))
            miners[m] = miner_nb

            miner_nb.send(("/CONNECT MINER-" + miner_name).encode())
            print('Connected to', m)

            threading.Thread(target=handle_miner_connection, args=[m, miner_nb]).start()

        except Exception as e: 
            print('Error connecting to neighbor:', e)
            remove_connection(m)
    else:
        print(miner_name, "is already connected with", m)

    print("List of miners:", list(miners.keys()))


def get_merkle_proof_head(trans_idx):
    # Synchronise the blockchain first
    resolve_conflicts()

    msg_to_send = "REP "
    # check if block is valid
    len_chain = len(blockchain.chain)
    if trans_idx not in trans_block or len_chain < trans_block[trans_idx] + 6:
        msg_to_send += "FALSE The block is not valid yet. Try again later..."
    else:
        for block in blockchain.chain:
            for transaction in block['transactions']:
                if str(transaction['id']) == str(trans_idx):
                    merkle_tree = merkle_trees[block['previous_hash']]
                    msg_to_send += "TRUE " + merkle_tree.value + " " + json.dumps(get_merkle_proof(merkle_tree, hash(transaction)))
                    return msg_to_send
    return msg_to_send

###############################################################################################
def handle_wallet_connection(nick_name, conn):
    global trans_block, len_chain_max
    """
    Handle the messages sent by the wallets
    """
    while True:
        try:
            msg = conn.recv(1024).decode()
            if msg:
                print(nick_name, ":", msg)
                # send wallet message to others miners
                msg_split = msg.split()
                if msg_split[0] == "/TRANS":
                    get_last_id_trans()
                    print("The current length of the blockchain is ", len_chain_max)
                    trans_block[str(blockchain.id_trans)] = len_chain_max
                    # Send to the wallet the id of his transaction: /ID idx_trans TRANS a b 2
                    conn.send(("/ID " + str(blockchain.id_trans) + " " + msg).encode())
                    msg_to_send = "/MSG WALLET-" + nick_name + " " + msg + " " + str(blockchain.id_trans) + " " + str(len_chain_max)
                else:
                    msg_to_send = "/MSG WALLET-" + nick_name + " " + msg

                for m in miners.keys():
                    miners[m].send(msg_to_send.encode())
                
                # treat message for current miner
                # New transaction: /TRANS Dung Yeya 10
                msg_split = msg.split()
                if msg_split[0] == "/TRANS":
                    #print("Adding new transaction...")
                    index = blockchain.new_transaction(
                    idx = blockchain.id_trans,
                    sender = msg_split[1],
                    recipient = msg_split[2],
                    amount = msg_split[3]
                    )
                    print("New transaction id added: ", trans_block)


                # check if a transaction t is in the blockchain: /MP trans_idx
                # return liste mp and block head: REP head list
                if msg_split[0] == "/MP":
                    mp_head = get_merkle_proof_head(msg_split[1])
                    conn.send(mp_head.encode())
            else:
                raise Exception("wallet " + nick_name + " is closed")
                    
        except Exception as e:
            print('Error to handle wallet connection:', e)
            remove_connection(nick_name)
            break


def handle_miner_connection(nick_name, miner_nb):
    """
    Handle the messages sent by the miners
    """
    global response, trans_block
    response = ""
    while True:
        try:
            msg = miner_nb.recv(1024).decode()
            if msg:
                # /MSG WALLET-wallet_name /TRANS A B or /CONNECT MINER-miner_name
                msg_split = msg.split()
                #print("miner thread got: ", msg)
                # message from a miner to connect with new miner
                if msg_split[0] == "/CONNECT":
                    msg_split = msg_split[1].split("-")
                    connect_to_neighbor(msg_split[1])

                #We have a reponse
                if msg_split[0] == "REP":
                    if msg_split[1] == "CHAIN":
                        response = json.loads("".join(msg_split[2:]))
                        #print("response updated")
                    if msg_split[1] == "ID":
                        response = msg_split[2:]
                        #print("resp = ", response)
                    
                # Return the id of transaction
                if msg_split[0] == "/ID":
                    #print("Im here ", ("REP ID "+ str(blockchain.id_trans)))
                    miner_nb.send(("REP ID "+ str(blockchain.id_trans) + " " + str(len(blockchain.chain))).encode())

                # Return the chain of the current miner: CHAIN
                if msg_split[0] == "/CHAIN":
                    response = blockchain.chain
                    miner_nb.send(("REP CHAIN "+ json.dumps(response)).encode())
                
                # message from a wallet
                if msg_split[0] == "/MSG":
                    wallet_name = msg_split[1].split("-")[1]
                    msg_split = msg_split[2:]
                    print(wallet_name, ":", " ".join(msg_split))
                    
                    # New transaction: /TRANS Dung Yeya 10 idx_trans len_chain_max
                    if msg_split[0] == "/TRANS":
                        #print("Adding new transaction...")
                        index = blockchain.new_transaction(
                        idx = msg_split[4],
                        sender = msg_split[1],
                        recipient = msg_split[2],
                        amount = msg_split[3]
                        )
                        trans_block[msg_split[4]] = msg_split[5]
                        print("New transaction id added: ", trans_block)

                 
            ## miner closed
            else:
                raise Exception("Miner " + nick_name + " is closed")
                
        except Exception as e:
            print('Error to handle miner connection:', e)
            remove_connection(nick_name)
            break


def handle_miner_ops():
    """
    Handle the input from the miners
    """
    global miner_name
    while True:
        try:
            msg = input()
            if msg:
                msg_split = msg.split(" ")
                # Return the chain of the current miner: CHAIN
                if msg_split[0] == "/CHAIN":
                    print(blockchain.chain)

                # Return the current transactions: /BLOCK
                if msg_split[0] == "/BLOCK":
                    print(blockchain.current_transactions)

                # Mine
                if msg_split[0] == "/MINE":
                    mine()

                # Resolve conflicts
                if msg_split[0] == "/RESOLVE":
                    resolve_conflicts()

            ## miner closed
            else:
                raise Exception("Miner " + miner_name + " is closed")
            
        except Exception as e:
            print('Error to handle miner connection:', e)
            remove_connection(miner_name)
            break


###############################################################################################
def miner():
    global miner_name
    global blockchain
    blockchain = BlockChain()
    try:
        miner_name = sys.argv[1]
        miner = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        miner.bind(('localhost', int(miner_name)))
        miner.listen(100)
        
        if len(sys.argv) == 3:
            connect_to_neighbor(sys.argv[2])

        print('Miner', miner_name, 'is running!')
        
        threading.Thread(target=handle_miner_ops).start()

        while True:
            conn, addr = miner.accept()
            
            msg = conn.recv(1024).decode()
            msg_split = msg.split(" ")
            
            ## new connect is a MINER
            if msg_split[0] == '/CONNECT':
                msg_split = msg_split[1].split("-")
                nick_name = msg_split[1]
                
                if nick_name not in miners.keys():
                    # demand new miner connect with neighbors
                    for name in miners.keys():
                        conn.send(("/CONNECT MINER-" + name).encode())
                        # avoid receive multi mess in same time (ex of error: MINER-8000MINER-8001)
                        time.sleep(1) 
                
                    miners[nick_name] = conn
                    threading.Thread(target=handle_miner_connection, args=[nick_name, conn]).start()
                    print("Miner", nick_name, "is connected")
                    print("List of miners:", list(miners.keys()))
                    
                    # send list miner to wallet
                    send_list_miner()
                    
            ## new connect is wallet
            else:
                nick_name = msg
                
                if nick_name not in wallets.keys():
                    wallets[nick_name] = conn
                    threading.Thread(target=handle_wallet_connection, args=[nick_name, conn]).start()
                    print('Welcome', nick_name, 'to MINER-' + miner_name)
                    
                    #send_list_miner()
                    conn.send(" ".join(list(miners.keys())).encode())
            
    except Exception as e:
        print('An error has occurred when instancing socket:', e)
        miner.close()
        return


miner()