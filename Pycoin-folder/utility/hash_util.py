import hashlib as hl
import json

def hash_string_256(string):
    return hl.sha256(string).hexdigest()

def hash_block(block):
    """Hashes a block and returns a string representation of it
    Arguments: 
        :block: The block that should be hashed
        Json.dumps turns the block into a stringified Json
        sort_keys = True, so that the k,v pair comes in the same order each time
        .encode encodes it into Utf-8
        .hexdigest to turn the hashlib from bytes to string
    """
    hashable_block = block.__dict__.copy()
    hashable_block['transactions'] = [tx.to_ordered_dict() for tx in hashable_block['transactions']]
    return hash_string_256(json.dumps(hashable_block, sort_keys=True).encode())