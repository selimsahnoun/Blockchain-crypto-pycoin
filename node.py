from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from wallet import Wallet
from blockchain import Blockchain

app = Flask(__name__)

CORS(app)
#--------------------------------------------------------------------------------------------------#
#----------------------------------------/---------------------------------------------------------#
#--------------------------------------------------------------------------------------------------#

"""Gather the funds of the actual blockchain public key"""
@app.route('/', methods = ['GET'])
def get_node_ui():
    return send_from_directory('ui','node.html')

#--------------------------------------------------------------------------------------------------#
#----------------------------------------/network--------------------------------------------------#
#--------------------------------------------------------------------------------------------------#

"""Gather the funds of the actual blockchain public key"""
@app.route('/network', methods = ['GET'])
def get_network_ui():
    return send_from_directory('ui','network.html')

#--------------------------------------------------------------------------------------------------#
#----------------------------------------/balance--------------------------------------------------#
#--------------------------------------------------------------------------------------------------#

"""Gather the funds of the actual blockchain public key"""
@app.route('/balance', methods = ['GET'])
def get_balance():
    balance = blockchain.get_balance()
    if balance != None:
        response = {'message':'Balance successfuly gathered',
        'amount': balance}
        return jsonify(response), 200
    else: 
        response={'message':'Gathering balance failed', 'wallet set up': wallet.public_key != None}
        return jsonify(response), 500

#--------------------------------------------------------------------------------------------------#
#----------------------------------------/wallet-POST----------------------------------------------#
#--------------------------------------------------------------------------------------------------#
"""Create a new pair of private and public keys """
@app.route('/wallet', methods = ['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        response = {'public_key': wallet.public_key, 'private_key': wallet.private_key, 'funds': blockchain.get_balance()}
        return jsonify(response), 201
    else: 
        response={'message':'Saving keys failed'}
        return jsonify(response), 500

#--------------------------------------------------------------------------------------------------#
#----------------------------------------/wallet-GET-----------------------------------------------#
#--------------------------------------------------------------------------------------------------#
"""load an existing pair of public and private keys"""
@app.route('/wallet', methods = ['GET'])
def load_keys():
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        response = {'public_key': wallet.public_key, 'private_key': wallet.private_key, 'funds': blockchain.get_balance()}
        return jsonify(response), 201
    else: 
        response={'message':'Loading keys failed'}
        return jsonify(response), 500

#--------------------------------------------------------------------------------------------------#
#----------------------------------------/transaction----------------------------------------------#
#--------------------------------------------------------------------------------------------------#
"""add a new transaction"""
@app.route('/transaction', methods = ['POST'])
def add_transaction():
    if wallet.public_key == None:
        response = {
            'message': 'no wallet set up'
        }
        return jsonify(response), 400
    values = request.get_json()
    if not values:
        response={'message':'No data found'}
        return jsonify(response), 400
    required_fields = ['recipient', 'amount']
    if not all(field in values for field in required_fields):
        response = { 'message': 'Required data is missing'}
        return jsonify(response), 400
    recipient = values['recipient']
    amount = values['amount']
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    print(recipient, amount, signature)
    success = blockchain.add_transaction(recipient, wallet.public_key, signature, amount)
    if success:
        response = {'Message':'Adding a transaction succeeded',
        'transaction':{
            'sender': wallet.public_key,
            'recipient': recipient,
            'amount':amount,
            'signature':signature},
        'funds':blockchain.get_balance()
        }
        return jsonify(response), 201
    else: 
        response = { 'Message':'Adding a transaction failed'
        }
        return jsonify(response), 500

#--------------------------------------------------------------------------------------------------#
#----------------------------------------/transactions----------------------------------------------#
#--------------------------------------------------------------------------------------------------#
"""fetch open transactions"""
@app.route('/transactions', methods = ['GET'])
def get_open_transactions():
    try:
        transactions = [tx.__dict__ for tx in blockchain.get_open_transactions()]
        response = {'message':'Open transactions successfully gathered', 'transactions': transactions}
        return response, 200
    except: 
        response = {'Message':'Open transactions failed to gather'}
        return response, 500


   

#--------------------------------------------------------------------------------------------------#
#----------------------------------------/mine-----------------------------------------------------#
#--------------------------------------------------------------------------------------------------#
"""Mine a new block in the blockchain after several transactions with the public key as a miner"""
@app.route('/mine', methods = ['POST'])
def mine():
    if blockchain.resolve_conflicts:
        response = {'message': 'Resolve conflicts first, block not added'}
        return jsonify(response), 409
    block = blockchain.mine_block()
    if block != None:
        block = block.__dict__.copy()
        block['transactions'] = [tx.__dict__ for tx in block['transactions']]
        response = {'message':'adding a block succeded',
        'wallet_set_up': wallet.public_key != None,
        'block': block,
        'funds': blockchain.get_balance()}
        return jsonify(response), 201
    else: 
        response = {'message':'adding a block failed',
        'wallet_set_up': wallet.public_key != None}
        return jsonify(response), 500

#--------------------------------------------------------------------------------------------------#
#----------------------------------------/resolve-conflicts----------------------------------------#
#--------------------------------------------------------------------------------------------------#
"""resolve conflicts by calling the resolve function in blockchain.py"""
@app.route('/resolve-conflicts', methods = ['POST'])
def resolve_conflicts():
    replaced = blockchain.resolve()
    if replaced:
        response = {'message': 'Chain replaced'}
    else: 
        response = {'message': 'Local chain kept'}
    return jsonify(response), 200

#--------------------------------------------------------------------------------------------------#
#----------------------------------------/nodes-GET------------------------------------------------#
#--------------------------------------------------------------------------------------------------#
"""fetch the set of nodes"""
@app.route('/nodes', methods = ['GET'])
def get_nodes():
   nodes = blockchain.get_peer_nodes()
   response = {'message' : 'nodes successfully fetched', 'all_nodes':nodes}
   return jsonify(response), 200 

#--------------------------------------------------------------------------------------------------#
#----------------------------------------/node-POST------------------------------------------------#
#--------------------------------------------------------------------------------------------------#
"""add a node to the set of nodes"""
@app.route('/node', methods = ['POST'])
def add_node():
    values = request.get_json()
    if not values: 
        response={'message':'no data attached'}
        return jsonify(response), 400

    if "node" not in values:
        response={"message":"no node data attached"}
        return jsonify(response), 400
    node = values["node"]
    blockchain.add_peer_node(node)
    response={"message":"node added successfully",
    "all_nodes":blockchain.get_peer_nodes()}
    return jsonify(response), 201

#--------------------------------------------------------------------------------------------------#
#----------------------------------------/node/<>-DELETE-------------------------------------------#
#--------------------------------------------------------------------------------------------------#
"""remove a node from the set of nodes"""
@app.route('/node/<node_url>', methods = ['DELETE'])
def remove_node(node_url):
    if node_url == '' or node_url == None:
        response = {'message':'No node found'}
        return jsonify(response), 400
    blockchain.remove_peer_node(node_url)
    response = {'message':'Node removed', 'all_nodes':blockchain.get_peer_nodes()}
    return jsonify(response), 200
    
#--------------------------------------------------------------------------------------------------#
#----------------------------------------/chain----------------------------------------------------#
#--------------------------------------------------------------------------------------------------#
"""Recieve a copy of the ledger"""
@app.route('/chain', methods = ['GET'])
def get_chain():
    chain_snapshot = [block.__dict__.copy() for block in blockchain.chain]
    for block in chain_snapshot:
        block['transactions'] = [tx.__dict__ for tx in block['transactions']]
    return jsonify(chain_snapshot), 200

#--------------------------------------------------------------------------------------------------#
#----------------------------------------/broadcast-transaction------------------------------------#
#--------------------------------------------------------------------------------------------------#
"""Broadcast a transaction to all the nodes"""
@app.route('/broadcast-transaction', methods = ['POST'])
def broadcast_transaction():
    values = request.get_json()
    if not values:
        response = {'message':'No data found'}
        return jsonify(response), 400
    required = ['sender','recipient','amount','signature']
    if not all(key in values for key in required):
        response = {'message':'Some data is missing'}
        return jsonify(response), 400
    success = blockchain.add_transaction(values['recipient'],values['sender'], values['signature'],values['amount'], is_receiving=True)
    if success:
        response = {'Message':'Adding a transaction succeeded',
        'transaction':{
            'sender': values['sender'],
            'recipient': values['recipient'],
            'amount':values['amount'],
            'signature':values['signature']},
        }
        return jsonify(response), 201
    else: 
        response = { 'Message':'Creating a transaction failed'}
        return jsonify(response), 500



    return None

#--------------------------------------------------------------------------------------------------#
#----------------------------------------/broadcast-block------------------------------------------#
#--------------------------------------------------------------------------------------------------#
"""Broadcast a block to all the nodes"""
@app.route('/broadcast-block', methods = ['POST'])
def broadcast_block():
    values = request.get_json()
    if not values:
        response = {'message':'No data found'}
        print(response)
        return jsonify(response), 400
    required = ['block']
    if not all(key in values for key in required):
        response = {'message':'Some data is missing'}
        print(response)
        return jsonify(response), 400
    block = values['block']
    
    if block['index'] == blockchain.chain[-1].index + 1 :
        if blockchain.add_block(block):
            response = {'message':'Block added'}
            print(response)
            return jsonify(response), 201
        else: 
            response = {'message':'Block seems invalid'}
            print(response)
            return jsonify(response), 409
    elif block['index'] > blockchain.chain[-1].index:
        response = {'message':'Blockchain seems to be diffrent from local blockchain, block not added'}
        blockchain.resolve_conflicts = True
        print(response)
        return jsonify(response), 200 
    else:
        response = {'message':'Blockchain seems to be shorter, block not added'}
        print(response)
        return jsonify(response), 409

    return None

#--------------------------------------------------------------------------------------------------#
#----------------------------------------Run the server--------------------------------------------#
#--------------------------------------------------------------------------------------------------#
"""-------------------------------Run the server-------------------------------"""
if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=5000)
    args = parser.parse_args()
    port = args.port
    wallet = Wallet(port)
    blockchain = Blockchain(wallet.public_key, port)
    app.run(host='0.0.0.0', port = port)