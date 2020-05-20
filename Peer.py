import hashlib
import json
from argparse import ArgumentParser
import requests
from flask import Flask, jsonify, request

from Block import Block
from BlockChain import BlockChain
from db import Operator
from redis_conn import redis_conn_pool
from wallet import Wallet
from Transaction2 import Transaction2

r = redis_conn_pool()



class Peer:
    def __init__(self):

        self.blockchain = BlockChain()

        self.neighbours = []
        self.address = 0
        self.pub_key_list = {}
        self.wallet = {}

    def setAddress(self, addr):
        self.address = addr

    def addpubkey(self, key, value):
        self.pub_key_list[key] = value

    def addwallet(self, address, peer_wallet):
        self.wallet[address] = peer_wallet

    def addNeighbour(self, neighbour):
        """
        Add a new neighbour
        """
        self.neighbours.append(neighbour)

    def validChain(self, chain) -> bool:
        """
        Check if the chain is valid by verifying the proof of work(Used in function resolveConflicts())
        :param chain: A blockchain
        :return: False Return true if valid, otherwise false
        """
        index = 1
        lastBlock = chain[0]
        length = len(chain)
        while index < length:
            block = chain[index]
            # Check if the hash is correct
            lastBlockHash = hashlib.sha256(json.dumps(lastBlock).encode()).hexdigest()
            if block['previous_Hash'] != lastBlockHash:
                return False
            # Check if the proof of work is correct
            if not self.blockchain.validProof(lastBlock['proof'], block['proof']):
                return False
            lastBlock = block
            index += 1
        return True

    def resolveConflicts(self) -> bool:

        newChain = None
        # Find the longest chain in terms of the consensus algorithm
        maxLen = len(self.blockchain.chain)
        # Traverse all neighbor nodes, determine the similarities and differences between the neighbor node chain and its own
        # If the neighbor node's chain is longer than its own, and the chain is legal, temporarily store this chain as the final
        # Select the longest chain

        for node in self.neighbours:
            response = requests.get(
                f'http://localhost:{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > maxLen and self.validChain(chain):
                    maxLen = length
                    newChain = chain
        if newChain:
            self.blockchain.chain = []
            for temp in newChain:
                transactions = []
                transet = temp['transactions']
                for t in transet:
                    transactions.append(Transaction2(t['index'], t['address'], t['amount'], t['Previous_transaction_ID'], t['Previous index'], t['Signature'], t['Transaction_ID']))
                self.blockchain.chain.append(
                    Block(temp['index'], temp['timestamp'], transactions, temp['proof'], temp['previous_Hash'])
                )
            return True
        return False

peer = Peer()
app = Flask(__name__)


@app.route("/chain", methods=['GET'])
def getChian():
    """
    Retrieve information from the chain
    """
    temp = peer.blockchain.chain
    json_chain = []
    for block in temp:
        json_chain.append(block.toJson())
    response = {
        'chain': json_chain,
        'length': len(temp)
    }
    return jsonify(response), 200


@app.route('/transaction/new', methods=['POST'])
def addNewTransaction():
    if int(peer.address) !=5000:
        return "Only default node 5000 supports transaction function",400
    else:
        # Check if the parameter is complete:
        sender = int(request.values.get("sender"))
        receiver = int(request.values.get("receiver"))
        amount = float(request.values.get("amount"))
        if sender == None or receiver == None or amount == None:
            return "Not enough parameters", 400

        # Check if the sender and the receiver are the same person
        if sender == receiver:
            return "The sender and the receiver are the same guys, transaction fails ", 400

        # Check whether the sender and the receiver are on the node lists.
        if sender == peer.address or str(sender) in peer.neighbours and receiver == peer.address or str(
                receiver) in peer.neighbours:
            if sender in peer.wallet and receiver in peer.wallet:
                print("transaction begin")
                sender_peer_wallet: Wallet = peer.wallet[sender]
                index = 0
                find_transaction = False
                while(index < len(sender_peer_wallet.UTXOs) and find_transaction == False):
                    print("Excute while")
                    temp_transaction: Transaction2 = sender_peer_wallet.UTXOs[index]
                    if temp_transaction.amount >= amount:
                        print("Excute transaction")
                        find_transaction = True
                        # Send amount to the receiver and the left is sent to the sender
                        send_amount = amount
                        left_amount = temp_transaction.amount - amount

                        # Generate 2 new block
                        # One output is the receiver
                        # And the other one is the input
                        sender_pubkey = peer.pub_key_list[sender]
                        receiver_pubkey = peer.pub_key_list[receiver]
                        pre_transaction_ID = temp_transaction.transaction_ID
                        pre_index = temp_transaction.index
                        transaction_index = pre_index + 1
                        send_receiver_transaction = Transaction2(index=transaction_index, address=receiver_pubkey, amount=send_amount, pre_transaction_ID=pre_transaction_ID, pre_index=pre_index, signature=None, transaction_ID=None)
                        send_self_transaction = Transaction2(index=transaction_index, address=sender_pubkey, amount=left_amount, pre_transaction_ID=pre_transaction_ID, pre_index=pre_index, signature=None, transaction_ID=None)
                        send_receiver_transaction.normaltransaction_ID()
                        send_self_transaction.normaltransaction_ID()
                        sender_peer_wallet.replaceUTXOs(index=index, utxo=send_self_transaction)
                        peer.blockchain.addTransaction(send_self_transaction)

                        # Node amount
                        sender_amount = float(r.get(sender))
                        receiver_amount = float(r.get(receiver))
                        r.set(sender, sender_amount - amount)
                        r.set(receiver, receiver_amount + amount)

                        if receiver in peer.wallet:
                            receiver_peer_wallet: Wallet = peer.wallet[receiver]
                            receiver_peer_wallet.addUTXOs(send_receiver_transaction)
                            peer.blockchain.addTransaction(send_receiver_transaction)
                    else:
                        index = index + 1
            response = {
                "System response": "Add new transaction",
            }
            return jsonify(response), 201

        else:
            return "Some of the nodes are not in this network, transaction fails", 400


@app.route("/mine", methods=['GET'])
def mine():

    # Last block's content
    last_block = peer.blockchain.lastBlock()
    last_proof = last_block.proof
    proof = peer.blockchain.proofWork(last_proof)

    # Mine reward：
    receiver_pubkey = peer.pub_key_list[peer.address]
    mine_transaction = Transaction2(index=1, address=receiver_pubkey, amount=50, pre_transaction_ID=None, pre_index=None, signature=None, transaction_ID=None)
    mine_transaction.minetransaction_ID()
    peer.blockchain.addTransaction(newTransaction=mine_transaction)

    # Create a new block, send last block's proof into the new block
    block = peer.blockchain.createBlock(proof)

    if peer.address in peer.wallet:
        peer_wallet: Wallet = peer.wallet[peer.address]
        peer_wallet.addUTXOs(mine_transaction)
        for each_transaction in peer_wallet.UTXOs:
            each_transaction_object: Transaction2 = each_transaction
            print(each_transaction_object.toJsonStr())

    # Store block in database
    operator = Operator()
    operator.add_one(block.index, block.timestamp, block.proof, block.previous_hash, [t.toJsonStr()for t in block.transactions])

    # Consensus
    for neighbour in peer.neighbours:
        requests.get(f'http://127.0.0.1:{neighbour}/consensus')

    # Node amount + 50
    amount = float(r.get(peer.address))
    r.set(peer.address,amount+50)


    response = {
        "message": "New block created",
        "index": block.index,
        "transactions": [t.toJsonStr()
                         for t in block.transactions],
        "proof": block.proof,
        "previous_Hash": block.previous_hash
    }
    return jsonify(response), 200


@app.route("/neighbour/add", methods=['POST'])
def addNeighbour():
    """
    Add a neighbour node
    """
    node = request.values.get("node")
    print(node)
    print("------------")
    if node == None:
        return "Lack of parameter", 400
    peer.addNeighbour(node)
    print(peer.neighbours)
    pub_key_response = requests.get(f'http://127.0.0.1:{node}/Pubkey')
    if pub_key_response.status_code == 200:
        response_data = pub_key_response.json()
        key = response_data['Address']
        value = response_data['Public key']
        peer.addpubkey(int(key), value)
        peer.addwallet(int(key), Wallet(int(key)))

    for key in peer.pub_key_list:
        print(str(key) + ':' + str(peer.pub_key_list[key]))

    for key in peer.wallet:
        each_wallet = peer.wallet[key]
        print(type(each_wallet))
        print(str(key) + ':' + str(each_wallet.id))
    response = {
        "System response": "Successfully add a new neighbour",
        "Node address": peer.address,
        "Number of neighbour nodes": len(peer.neighbours)
    }
    return jsonify(response), 200


@app.route("/consensus")
def consensus():
    replaced = peer.resolveConflicts()
    if replaced:
        response = {
            "message": "The chain has been updated",
            "length": len(peer.blockchain.chain)
        }
    else:
        response = {
            "message": "The chain remains unchange",
            "length": len(peer.blockchain.chain)
        }
    return jsonify(response), 200

# Check the amount of this current node
@app.route("/amount", methods=['GET'])
def amount():
    amount = float(r.get(peer.address))
    response = {
        "Address": peer.address,
        "Amount": amount,

    }
    return jsonify(response), 200

# Check transactions that are not in the block
@app.route("/transaction", methods=['GET'])
def transaction():
    if peer.blockchain.transactions is not None:
        response = {
            "Transaction": [t.toJsonStr() for t in peer.blockchain.transactions]
        }
        return jsonify(response), 200
    else:
        response = {
            "Transaction": None
        }
        return jsonify(response), 400

# Check public key
@app.route("/Pubkey", methods = ["GET"])
def pub_key():
    response = {
        "Address": peer.address,
        "Public key": str(wallet.publicKey.to_string())

    }
    return jsonify(response), 200

@app.route("/Viewtransaction", methods = ["GET"])
def view_transaction():
    transaction_list = []
    peer_wallet: Wallet = peer.wallet[peer.address]
    for each_transaction in peer_wallet.UTXOs:
        each_transaction_object: Transaction2 = each_transaction
        transaction_list.append(each_transaction_object.toJsonStr())
    response = {
        'Transaction': transaction_list
    }
    return jsonify(response), 200

if __name__ == '__main__':
    """
    Create P2P network
    """
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", default=5000, type=int, help="Monitor port")
    port = parser.parse_args().port
    peer.setAddress(port)
    wallet = Wallet(int(port))
    peer.addpubkey(port, str(wallet.publicKey.to_string()))
    peer.addwallet(port, wallet)
    r.set(peer.address, 0)
    app.run(host='127.0.0.1', port=port, debug=True)
