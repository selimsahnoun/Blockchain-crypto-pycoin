# Blockchain-crypto-pycoin

A Python blockchain app, running transactions of a cryptocurrency named Pycoin.
### Important : This project is for educational purposes only and the source code shouldn't be use in production as it doesn't have good security, doesn't scale well and lacks many important features. 

[<img src="https://img.youtube.com/vi/AJNHsBMKJDQ/maxresdefault.jpg" width="50%">](https://youtu.be/AJNHsBMKJDQ)

The github repository contains a basic implementation of a blockchain and its client using Python. This blockchain has the following features:

## Possibility of adding multiple nodes to the blockchain

  - Proof of Work (PoW)
  - Simple conflict resolution between nodes
  - Transactions with RSA encryption
  
## The blockchain client has the following features:

  - Wallets generation using Public/Private key encryption (based on RSA algorithm)
  - Generation of transactions with RSA encryption
 
## Dependencies

  - Works with Python 3.8
  - Anaconda's Python distribution contains all the dependencies for the code to run.
 
 ## How to run the code
 
  To start a blockchain node, go to Pycoin folder and execute the command below: 
  
  ```bash
  python node.py -p 5000
  ```
  You can access the blockchain frontend dashboards from your browser by going to localhost:5000
  You can add a new node to blockchain by executing the same command and specifying a port that is not already used. For example, 
  
   ```bash
  python node.py -p 5001
  ```
  
  To connect the 2 nodes, go to Network and add "localhost:5001" on the dashboard of the node 5000, for example.
  
  
