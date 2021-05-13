#Import RSA and Random to generate a private key
from Crypto.PublicKey import RSA
import Crypto.Random
#Import PKCS1 to create a signature
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from utility.hash_util import hash_string_256

import binascii

class Wallet: 
    def __init__(self, node_id):
        self.private_key = None
        self.public_key = None
        self.node_id = node_id
    
        
    def generate_keys(self):
        """Generate a new pair of private and public key."""
        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()

        return (binascii.hexlify(private_key.exportKey(format = 'DER')).decode('ascii'),binascii.hexlify(public_key.exportKey(format = 'DER')).decode('ascii') )

    def create_keys(self):
        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key
        
    def save_keys(self):
        if self.private_key != None and self.public_key != None:
            try:
                with open('wallet-{}.txt'.format(self.node_id),mode='w') as f:
                    f.write(self.public_key)
                    f.write('\n')
                    f.write(self.private_key)
                return True
            except(IOError,IndexError):
                return False 
    
    def load_keys(self):
        try:
            with open('wallet-{}.txt'.format(self.node_id), mode='r') as f:
                keys = f.readlines()
                public_key = keys[0][:-1]
                private_key = keys[1]
                self.public_key = public_key
                self.private_key = private_key
            return True
        except(IOError,IndexError):
            return False
    
    def sign_transaction(self, sender, recipient, amount):
        """Sign a transaction and return the signature.

        Arguments:
            :sender: The sender of the transaction.
            :recipient: The recipient of the transaction.
            :amount: The amount of the transaction.
        """
        signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        h = SHA.new((str(sender) + str(recipient) + str(amount)).encode('utf8'))
        signature = signer.sign(h)
        print(signature)
        
        return binascii.hexlify(signature).decode('ascii')

    @staticmethod
    def verify_transaction(transaction):
        public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier = PKCS1_v1_5.new(public_key)
        transaction_hash = SHA.new((str(transaction.sender)+str(transaction.recipient)+str(transaction.amount)).encode('utf8'))
        return verifier.verify(transaction_hash, binascii.unhexlify(transaction.signature))

