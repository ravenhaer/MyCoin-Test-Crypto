# -*- coding: utf-8 -*-
"""
Created on Sun Feb  6 10:51:13 2022

@author: ANWESHA
"""

#To be installed:
#Flask==0.12.2: pip install Flask==0.12.2
#Postman HTTP Client: https://www.getpostman.com/
#requests==2.18.4: pip install requests==2.18.4

#Importing libraries
import datetime
import hashlib    #this will help generation hash nos. using hash funcs. like the SHA256
import json 
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Part 1 Building the blockchain

class Blockchain:
    
    def __init__(self):
        self.chain = []   #initializing a list with []
    # init is a like the constructor in C++. Self keyword (similar to 'this' keyword in C++. But its a hidden argument in C++. We don't have to call it verytime we create a method) is used in Python to access all instances in a class. Self variable represents the instance of the object itself.
        self.transactions = []  #Transactions that get added to a block as soon as it is mined (not before that)
        self.create_block(proof = 1, previous_hash = '0')  #Our genesis block with 0 as hash of prev block
        self.nodes = set()  #empty set (mathematical set)
        
        
    def create_block(self, proof, previous_hash): #This func. creates all the blocks mined after genesis block. Since createblock func. called after mineblock func. , we take the proof of mining as arg. to create a block
        block = {'index' : len(self.chain) + 1,                    #This variable block is a dictionary  with the 4 keys : index is len. of blockchain + 1 because +1 is the index of new block, timestamp calls the datetime module inside datetime library alled at top at the time of block creation and hence the .now(), the last 2 keys take in the arguments of func. create_block we are inside
                 'timestamp' : str(datetime.datetime.now()),
                 'proof' : proof,
                 'previous_hash' : previous_hash,
                 'transactions' : self.transactions}
        self.transactions = [] #We make the transactions list from the init func. at top empty again because the transactions that were waiting have been added to the chain through the create block func. above
        self.chain.append(block) #append the new block reated to the blockhain
        return block
    
    def get_previous_block(self):
        return self.chain[-1]   #-1 is the index of previous block
    
    def proof_of_work(self, previous_proof):
        new_proof = 1 # This is what is commonly called the Nonce. We are calling it new_proof. To solve the proof problem, we will increment new_proof var. at each iteration of while loop until we get right proof/hash no.
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()    #the operation new_proof+prev_proof is symmetrical, i.e., new_proof+prev_proof=prev_proof+new_proof but it must be non-symmetrical otherwise we will get the same hash no. every 2 blocks. So we subtract  the square
            if hash_operation[:4] == '0000':     # :$ will give us first 4 indexes of string hash_operation ,i.e., 0, 1, 2, 3
                check_proof = True
            else:
                new_proof += 1
        
        return new_proof
    #The proof of work is the proof that miners have solved the problem we have created for them. The problem here is the hash no created by sha256 combined with hexdigest() fun should give a headeimal no. that starts with 4 leading zeroes(4 or any no of zeroes set by us); The more leading zeroes, the harder it is for miners to mine a block
  
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()     # .dumps() func. converts the block dictionary into a string so that we can do sha256 operation on it
        return hashlib.sha256(encoded_block).hexdigest()   
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block =block
            block_index += 1
        return True
    #To check the blockchain, check 2 things: 1. we check every block's hash func. has 4 leading zeroez 2. We see the previous_hash of each block matches hash no. of its prev. block
    
    def add_transaction(self, sender, receiver, amount):  #format for transactions. Appends transactions to list of transactions at top before they are integrated to a block
        self.transactions.append({'sender': sender,      #We are appending a new transaction to the list of waiting transactions
                                  'receiver': receiver,
                                  'amount': amount}) #The transactions are formatted as dictionaries with 3 key-value pairs: sender, receiver and amount
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1   #we return index of the block that we receive this transactions list
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)  #For sets, we have add insteaad of append
    
   
    def replace_chain(self):
        network = self.nodes  #Our set of nodes all around the world. This is the set from the func. above
        longest_chain = None
        max_length = len(self.chain)  #Length of longest chain. We initialize it with length og chain we are dealing with at the moment
        for node in network:      # for each 'node' in  set of 'nodes'    
            response = requests.get(f'http://{node}/get_chain')   #We are using the requests library imported at top and get_chain() method created with Flask below in this line.    The {node} here is the parsed_url.netloc ( =127.0.0.1:5000 in our test env.) because that is what we added as node in .add_node() above  #The diffrence b/w nodes is in ports i.e., 127.0.0.1 remains sames but what i 5000 here will diffrent no. for other nodes
            if response.status_code == 200:     #The 200 status code is returned by get_chain along with the json response  to tell everything is working fine               
                length = response.json()['length']
                chain = response.json()['chain'] 
                if length> max_length and self.is_chain_valid(chain): 
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False 
 #The .get() method from the requests library gives the whole address of the node plus the GET request we are using from below I.e., http://127.0.0.1:5000/get_chain    :  get_chain the the GET request and rest is address of one node we know for our cryptocurrency

                               
# Part 2 Mining the Blockchain
    
#Creating a Web App
app = Flask(__name__) 

#Creating an address for the node on port 5000
node_address = str(uuid4()).replace('-', '')   #uuid4 generates random and unique address   #We replace dashes(-) with nothin('')
    
#Creating a Blockchain
    
blockchain = Blockchain() #blockchain is instance of the class Blockchain created above
    
#Mining a new block
#Below we have the GET request to mine a new block
@app.route('/mine_block', methods = ['GET'])  #route() tells Flask which url should trigger our function. inside the route(), the url of the server runs. This url of server is http://127.0.0.1:5000/ but this portion is hidden.  the mine_block is appended after the last '/'   

def mine_block():
   previous_block = blockchain.get_previous_block() #We are calling this func. we created above
   previous_proof = previous_block['proof']
   proof = blockchain.proof_of_work(previous_proof)  #We the proof_of_work puzzle
   previous_hash = blockchain.hash(previous_block)
   blockchain.add_transaction( sender = node_address, receiver = 'Anwesha_new_pc', amount = 100)  #This transaction is the miner receiving reward coins. So sender is set to our(creator of that crypto) port addr.
   block = blockchain.create_block(proof, previous_hash)   #Once we get prrof or the hash no with 4 leading zeroes for the current block, we append it to the blockchain
   response = {'message': 'Congratulations, you just mined a block!',
               'index': block['index'],     #This is the response to the 'GET' request above. We show a UI message on Postman interface in JSON format using var. response here which is a dictionary
               'timestamp': block['timestamp'],
               'proof': block['proof'],
               'previous_hash': block['previous_hash'],
               'transactions' : block['transactions']}  #The words on left of ':' are keys of var. response and on right side we are using keys of block to give value to the keys on left
   return jsonify(response), 200   #200 is standard response for a successful HTTP request
     
#what we do in the mine_block() function above: 1. we find proof of work based on last proof given in last block. 2. Once we get proof, we get the other 3 keys ,i.e., index, timestamp and previous_hash 

#Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,      #The '.chain' on right side is the chain list you can see just below __init__ constructor. It has all the keys,i.e., index, timestamp, proof, previous_hash so we don't have to list them seperately
                'length': len(blockchain.chain)}
    return jsonify(response), 200

#Checking the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    validity = blockchain.is_chain_valid(blockchain.chain)
    if validity is True:
        response = {'message': 'Blockchain is valid.'}
    else:
        response = {'message': "Yikes! The blockchain is not valid."}
    return jsonify(response), 200

#Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json() #We creat a variable named json as a dictionary and store key-value from json request .get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys): #We check if the json format of a transaction has all 3 keys as the line above
        return 'Some elements of the transaction are missing', 400  #400 is http status code for bad request
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])  #The json mention here is the var. we created in begining of method
    response = {'message' : f'This transaction will be added to Block {index}'}   #The f' or f-string format is new addition to python 3.6
    return jsonify(response), 201 # 201 is http code for new creation
    #if everything is fine, we add the transaction to the correct block

# Part 3 Decentralizing our Blockchain

#Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')  # we fetch value of the key 'node' which is its address so we can pass it as argument to add_node method
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected. The MyCoin Blockchain now contains the following nodes :',
                'total_nodes': list(blockchain.nodes)}  #list here is a func.
    return jsonify(response), 201 
#We will have a seperate json file which will have all the nodes we want in our blockchain including the new ones we want to connect
#Whenever we want to connect a new node will add it to the json file having existing nodes

#Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()  #We created this method inside our blockchain class above
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest chain.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': "All good. The chain is the largest one.",
                    'actual_chain': blockchain.chain} 
    return jsonify(response), 200


#Running the App
app.run(host = '0.0.0.0', port = 5001)     #"app" object here and above is an instance of Flask class
#Adding the host argument above allows our server to become publicly available
 