import hashlib
import json
import socket
from time import time
from urllib.parse import urlparse
import requests
from bchelper import get_merkle_root


def is_port_open(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    result = sock.connect_ex((ip, port))
    if result == 0:
        sock.shutdown(2)
        return True
    else:
        return False


class BlockChain(object):
    UTXOs = dict()

    def __init__(self, chain=[], genesis_tx=None, nodes=set()):
        self.chain = chain

        self.current_transactions = []

        self.nodes = nodes
        #Create the genesis block
        if not self.chain:
            self.new_transaction(genesis_tx)
            self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'merkle_root': get_merkle_root(self.current_transactions),
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, new_transaction):
        """
        Creates a new transaction to go into the next mined Block
        :param new_transaction: <Transaction> new transaction added to the list of current transactions
        :return: <int> The index of the Block that will hold this transaction
        """

        txn = {
            'id': new_transaction.tx_id,
            'sender': new_transaction.sender,
            'recipient': new_transaction.recipient,
            'amount': new_transaction.values,
        }

        # If genesis block, then no previous block
        if not self.last_block:
            self.current_transactions.append(txn)
            return 0, True

        if not new_transaction.process_transaction():
            print('Transaction failed to process. Discarded')
            return None, False

        self.current_transactions.append(txn)

        return self.last_block['index'] + 1, True

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: <dict> Block
        :return: <str>
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1] if len(self.chain) > 0 else None

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: <bool> True if the address of node is valid and node is up, False otherwise
        """

        parsed_url = urlparse(address)
        ip, port = tuple(parsed_url.netloc.split(':'))
        if is_port_open(ip, int(port)):
            self.nodes.add(parsed_url.netloc)
            print(f" List of nodes addresses are {self.nodes}")
            return True
        else:
            return False

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: <bool> True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        print('List of neighbours: ' + str(neighbours))
        new_chain = None

        # We are looking for chain longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False





