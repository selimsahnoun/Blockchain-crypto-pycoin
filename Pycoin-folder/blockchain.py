from functools import reduce
import hashlib as hl
import json
import pickle
from block import Block
from transaction import Transaction
from utility.verification import Verification
from utility.hash_util import hash_block
from wallet import Wallet
import requests

# The reward we give to miners (for creating a new block)
MINING_REWARD = 10
print(__name__)

class Blockchain:
    def __init__(self, public_key, node_id):
        #genesis block is the starting block of the blockchain
        genesis_block = Block(0,'',[],100,0)
        # Initializing our (empty) blockchain list
        self.__peer_nodes = set()Ò
        self.chain=[genesis_block]
        self.__open_transactions=[]
        self.public_key = public_key
        self.node_id = node_id
        self.resolve_conflicts = False
        self.load_data()


    @property
    def chain(self):
        return self.__chain[:]
    @chain.setter
    def chain(self, val):
        self.__chain = val

    def get_open_transactions(self):
        return self.__open_transactions[:]

    def load_data(self):
        try: 
            with open('text-blockchain-{}.txt'.format(self.node_id), mode = 'r') as f:
                #file_content = pickle.loads(f.read()) 
                file_content = f.readlines()
                # blockchain = file_content['chain']
                # open_transactions = file_content['opent']
                #we serialize a string into a json format,  we don't take the /n so [:-1]  
                blockchain = json.loads(file_content[0][:-1])
                updated_blockchain=[]
                for block in blockchain:
                    converted_tx = [Transaction(tx['sender'], tx['recipient'], tx['signature'],tx['amount']) for tx in block['transactions']]
                    updated_block = Block(block['index'],block['previous_hash'],converted_tx,block['proof'],block['timestamp']) 
                    updated_blockchain.append(updated_block)
                self.chain = updated_blockchain
                self.__open_transactions = json.loads(file_content[1][:-1])
                updated_open_transactions = []
                for tx in self.__open_transactions:
                    updated_open_transaction = Transaction( tx['sender'], tx['recipient'], tx['signature'],  tx['amount'])
                    updated_open_transactions.append(updated_open_transaction) 
                    self.__open_transactions = updated_open_transactions 
                self.__peer_nodes = set(json.loads(file_content[2]))

        except (IOError, ValueError,IndexError): 
            print('File not Found!')
            pass
        finally: 
            print('Welcome to the blockchain {}'.format(self.public_key))

    def save_data(self):
        try: 
            with open('text-blockchain-{}.txt'.format(self.node_id), mode = 'w') as f:

                saveable_chain = [block.__dict__ for block in [Block(block_element.index, block_element.previous_hash, [tx.__dict__ for tx in block_element.transactions], block_element.proof,block_element.timestamp) for block_element in self.__chain]]
                f.write(json.dumps(saveable_chain))
                f.write('\n')
                saveable_tx = [tx.__dict__ for tx in self.__open_transactions]
                f.write(json.dumps(saveable_tx))
                f.write('\n')
                f.write(json.dumps(list(self.__peer_nodes)))
                # save_data = {
                #     'chain': blockchain,
                #     'opent':open_transactions
                # }
                # f.write(pickle.dumps(save_data))
        except IOError: 
            print('Saving failed!')

    def proof_of_work(self):
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0 
        #Try several proof of works until one succeed 
   
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof+=1
        return proof

    def get_balance(self, sender = None):
        if sender == None:
            if self.public_key == None:
                return None
            participant = self.public_key
        else: 
            participant = sender
        #Calculate the total amount of amount sent
        tx_sender = [[tx.amount for tx in block.transactions if tx.sender == participant] for block in self.__chain]
        open_tx_sender = [tx.amount for tx in self.__open_transactions if tx.sender == participant]
        tx_sender.append(open_tx_sender)
        amount_sent = reduce(lambda tx_sum, tx_amnt: tx_sum + sum(tx_amnt) if len(tx_amnt)>0 else tx_sum+0, tx_sender, 0)
        #Calculate the total amount of amount recieved
        tx_recipient = [[tx.amount for tx in block.transactions if tx.recipient == participant] for block in self.__chain]
        amount_recieved = reduce(lambda tx_sum, tx_amnt: tx_sum + sum(tx_amnt) if len(tx_amnt)>0 else tx_sum+0, tx_recipient, 0)
        return amount_recieved - amount_sent

    def get_last_blockchain_value(self):
        """ Returns the last value of the current blockchain. """
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    # This function accepts two arguments.
    # One required one (transaction_amount) and one optional one (last_transaction)
    # The optional one is optional because it has a default value => [1]

    def add_transaction(self, recipient, sender, signature, amount=1.0, is_receiving = False):
        """ Append a new value as well as the last blockchain value to the blockchain.

        Arguments:
            :sender: sender of the coins.
            :recipient: recipient of the coins.
            :amount: amount of coins sent with the transaction.
        """
        # if self.public_key == None:
        #     return False

        transaction = Transaction(sender, recipient, signature, amount)

        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()
            if not is_receiving:
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast-transaction'.format(node)
                    try:
                        response = requests.post(url, json = {'sender':sender,'recipient': recipient, 'amount': amount, 'signature':signature})
                        if response.status_code == 400 or response.status_code == 500:
                            print('transaction declined, needs resolving')
                        if response.status_code == 409:
                            self.resolve_conflicts = True
                    except requests.exceptions.ConnectionError:
                        continue 
            return True
        return False

    def mine_block(self):
        #check if there is a wallet
        if self.public_key == None:
            print('No wallet Found!')
            return None
        #fetch the last block of the blockchain
        last_block = self.__chain[-1]
        #hash the last block
        hashed_block = hash_block(last_block)
        #get the proof of work
        proof = self.proof_of_work()
        #reward to the miners
        #copy the transactions instead of manipulating the open transactions
        copied_transactions = self.__open_transactions[:]
        for tx in copied_transactions: 
            if not Wallet.verify_transaction(tx):
                return None
        #reward_transaction = { 'sender' : 'MINING', 'recipient':owner, 'amount': MINING_REWARD}
        reward_transaction= Transaction('MINING',self.public_key, '',MINING_REWARD)
        copied_transactions.append(reward_transaction)
        #define the new block
        block = Block(len(self.__chain),hashed_block,copied_transactions, proof)
        #add it to the blockchain
        self.__chain.append(block)
        self.__open_transactions=[]
        self.save_data()
        for node in self.__peer_nodes: 
            url = 'http://{}/broadcast-block'.format(node)
            converted_block = block.__dict__.copy()
            converted_block['transactions'] = [tx.__dict__ for tx in converted_block['transactions']]
            try:
                response = requests.post(url, json = {'block': converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Block declined, needs resolving')
                if response.status_code == 409:
                    self.resolve_conflicts = True
                    
            except requests.exceptions.ConnectionError:
                continue
        return block

    def add_block(self, block):
        transactions = [Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']]
        proof_is_valid = Verification.valid_proof(transactions[:-1], block['previous_hash'], block['proof'])
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False
        converted_block = Block(block['index'], block['previous_hash'], transactions, block['proof'],block['timestamp'])
        self.__chain.append(converted_block)
        stored_transactions = self.__open_transactions[:]
        # :itx: incoming transactions 
        for itx in block['transactions']:
            for opentx in stored_transactions:
                if opentx.sender == itx['sender'] and opentx.recipient == itx['recipient'] and opentx.amount == itx['amount'] and opentx.signature == itx['signature']:
                    try:
                        self.__open_transactions.remove(opentx)
                    except ValueError: 
                        print('item already removed')
        
        self.save_data()
        return True
    
    def resolve(self):
        winner_chain = self.chain
        replace = False
        for node in self.__peer_nodes:
            url = 'http://{}/chain'.format(node)
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [Block(block['index'], block['previous_hash'], [Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']], block['proof'],block['timestamp']) for block in node_chain]
                #node_chain.transactions = [Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in node_chain.transactions]
                node_chain_length = len(node_chain)
                local_chain_length = len(self.chain)
                if node_chain_length > local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        self.chain = winner_chain
        if replace:
            self.__open_transactions = []
        self.save_data()
        return replace

    def add_peer_node(self, node):
        """Adds a new node to the peer node set
        
        Arguments: 
            :node: The node URL which should be added
        """
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        """removes a node from the peer node set
        
        Arguments: 
            :node: The node URL which should be removed
        """
        self.__peer_nodes.discard(node)
        self.save_data() 

    def get_peer_nodes(self):
        """return a list of the nodes"""
        return list(self.__peer_nodes)
   





