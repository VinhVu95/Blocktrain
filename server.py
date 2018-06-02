from flask import Flask, jsonify, request
from uuid import uuid4
from blockchain import BlockChain
from database import MongoDb
import json
from textwrap import dedent
from pprint import pprint

# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = BlockChain()
db = MongoDb()
host = ""


def _initBlockChain(host):
    global blockchain
    result = db.get_chain_with_host(host)
    if not result:
        pprint("First time created!!!")
        blockchain = BlockChain()
        db.insert_new_chain(blockchain, host)
    else:
        pprint("Full chain information returned from database: {0}".format(result))
        blockchain = BlockChain(chain=result['chain'], nodes=db.get_nodes_from_network())


@app.route('/mine', methods=['Get'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    # TODO: handle if no chain ever exist for this node
    db.add_new_block(block, host)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():

    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    # The host receiving the request to register new nodes must be in the network itself
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    reg_success = []
    for node in nodes:
        if blockchain.register_node(node):
            reg_success.append(node)
            db.register_nodes_to_network([node])
            # Synchronise nodes in network
            blockchain.nodes = db.get_nodes_from_network()

    response = {
        'message': f'New nodes: {reg_success} have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
        db.delete_chain(host)
        db.insert_new_chain(blockchain, host)
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    host = 'localhost:'+str(port)
    _initBlockChain(host)

    app.run(host='0.0.0.0', port=port, threaded=True)



