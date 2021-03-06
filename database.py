from pymongo import MongoClient
from urllib.parse import urlparse


class MongoDb(object):
    def __init__(self, host='localhost', port=27017):
        self.client = MongoClient(host, port)
        self.chains = self.client['block_chain'].chains

    def add_new_block(self, block, host):
        return self.chains.find_and_modify(
            query={'host': host},
            update={"$push": {"chain": block}}
        )

    def register_nodes_to_network(self, nodes):
        return self.chains.update_many(
            {'host': {"$in": [urlparse(n).netloc for n in nodes]}},
            {"$set": {"in_network": True}}
        )

    def get_nodes_from_network(self):
        return set([n['host'] for n in self.chains.find() if n.get("in_network")])

    def delete_chain(self, host):
        try:
            self.chains.delete_one({'host': host})
        except Exception as err:
            print("Exception when trying to delete one node's blockchain: ", err)
            raise

    def insert_new_chain(self, new_chain, host):
        data = {
            'host': host,
            'chain': new_chain.chain
        }

        result = self.chains.insert_one(data)
        print("New chain: {0} added with id {1} and host {2}".format(result, result.inserted_id, host))

        if result:
            return "Success"
        else:
            return "Insert failed"

    # To debug
    def get_full_chains(self):
        for chain in self.chains.find():
            yield chain

    def get_chain_with_host(self, host):
        return self.chains.find_one({'host': host})
