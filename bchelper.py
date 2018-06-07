import hashlib


def get_merkle_root(transactions):
    count = len(transactions)
    previous_tree_layer = [tx.tx_id for tx in transactions]
    tree_layer = previous_tree_layer
    while count > 1:
        tree_layer = list()
        for i in range(1, len(previous_tree_layer)):
            encoded = hashlib.sha256((previous_tree_layer[i - 1] + previous_tree_layer[i]).encode()).hexdigest()
            tree_layer.append(encoded)
        count = len(tree_layer)
        previous_tree_layer = tree_layer
    return tree_layer[0] if len(tree_layer) == 1 else ""


