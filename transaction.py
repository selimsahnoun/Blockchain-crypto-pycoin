from collections import OrderedDict
from utility.printable import Printable

class Transaction(Printable):
    """ A transaction that will be added in a block of the blockchain

    Attributes: 
        :sender: The sender of the coins
        :recipient: the recipient of the coins
        :signature: the signature of the transaction
        :amount: the amount of coins sent
    
    """
    def __init__(self, sender, recipient, signature, amount):
        self.sender = sender 
        self.recipient = recipient
        self.amount = amount
        self.signature = signature

    def to_ordered_dict(self):
        return OrderedDict([('sender',self.sender),('recipient',self.recipient),('amount',self.amount)])
    

