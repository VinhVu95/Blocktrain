from fastecdsa import keys, curve, ecdsa
import hashlib

ccurve = curve.P192


def concatenate_strings(*objs):
    return "".join(map(str, objs))


class Wallet(object):
    def __init__(self):
        self.private_key, self.public_key = Wallet.generate_keypairs()

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

    def calculate_hash(self, sequence):
        """

        :return: this function return the transaction hash (which will be used as its id)
        """
        encode_id = concatenate_strings(self.sender, self.recipient, self.values, sequence).encode()
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


