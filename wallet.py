from fastecdsa import keys, curve, ecdsa
import hashlib
from blockchain import BlockChain

ccurve = curve.P192


def concatenate_strings(*objs):
    return "".join(map(str, objs))


class Wallet(object):
    def __init__(self):
        self.private_key, self.publ
        ic_key = Wallet.generate_keypairs()

    @staticmethod
    def generate_keypairs():
        try:
            private_key = keys.gen_private_key(ccurve)
            public_key = keys.get_public_key(private_key, ccurve)
            return private_key, public_key
        except ecdsa.EcdsaError as encode_err:
            print("Error when generating key pairs: {0}".format(encode_err))
            raise


class Transaction(object):
    SEQUENCE = 0 # Roughly count how many transactions have been generated, should be a global value saved in database

    def __init__(self, sender, recipient, values):
        """

        :param sender: this should be public key of sender
        :param recipient: this should be public key of recipient
        :param values: the value of transaction
        """
        self.sender = sender
        self.recipient = recipient
        self.values = float(values)
        self.signature = None
        self.tx_inputs = list()
        self.tx_outputs = list()

    def calculate_hash(self):
        """

        :return: this function return the transaction hash (which will be used as its id)
        """
        Transaction.SEQUENCE += 1
        encode_id = concatenate_strings(self.sender, self.recipient, self.values, Transaction.SEQUENCE).encode()
        return hashlib.sha256(encode_id).hexdigest()

    def generate_signature(self, private_key):
        # Signs all the data we don't wish to be tampered with.
        data = concatenate_strings(self.sender, self.recipient, self.values)
        r, s = ecdsa.sign(data, private_key, curve=ccurve)
        self.signature = r, s

    def verify_signature(self):
        # Verifies the data we signed hasn't been tampered with
        data = concatenate_strings(self.sender, self.recipient, self.values)
        valid = ecdsa.verify(self.signature, data, self.sender, curve=ccurve)
        return valid

    def process_transaction(self):
        if not self.verify_signature():
            print('Transaction failed to verify')
            return False

        # Gather transaction input (make sure they are unspent)
        for i in self.tx_inputs:
            i.utxo = BlockChain.UTXOs.get(i.tx_output_id, None)

        # TODO: Check if chain is valid

        # Genrerate transaction outputs
        left_over = self.get_inputs_value() - self.values
        tx_id = self.calculate_hash()
        self.tx_outputs.extend(
            [TransactionOutput(self.recipient, self.values, tx_id),
             TransactionOutput(self.sender, left_over, tx_id)]
        )

        # Add output to Unspent lists
        for u in self.tx_outputs:
            BlockChain.UTXOs[u.id] = u

        # Remove transaction input from UTXO lists as spent
        for i in self.tx_inputs:
            try:
                BlockChain.UTXOs.pop(i.tx_output_id)
            except KeyError:
                continue

        return True

    def get_inputs_value(self):
        return float(sum([i.utxo.value for i in self.tx_inputs if i.utxo]))

    def get_output_value(self):
        return float(sum([o.value for o in self.tx_outputs]))

class TransactionInput(object):
    def __init__(self, tx_output_id):
        self.tx_output_id = tx_output_id
        self.utxo = None


class TransactionOutput(object):
    def __init__(self, recipient, value, parent_tx_id):
        self.recipient = recipient
        self.value = float(value)
        self.parent_tx_id = parent_tx_id
        self.id = concatenate_strings(self.recipient, self.value, self.parent_tx_id)

    # Check if coin belongs to you
    def is_mine(self, public_key):
        return public_key == self.recipient


if __name__ == '__main__':
    walletA = Wallet()
    walletB = Wallet()
    print('Private and Public key')
    print('Private key:' + str(walletA.private_key))
    print('Public key:' + str(walletA.public_key))
    # Create a test transaction from WalletA to walletB
    test_transaction = Transaction(walletA.public_key, walletB.public_key, 5)
    test_transaction.generate_signature(walletA.private_key)
    print('Is signature verified?: ' + str(test_transaction.verify_signature()))


