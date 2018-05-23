from pymongo import MongoClient


class MongoDb(object):
    def __init__(self, host='localhost', port=27017):
        self.client = MongoClient(host, port)
        self.chains = self.client['block_chain'].chains

    def add_new_block(self, block):
        pass

    def delete_chain(self):
        pass

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

    def get_full_chains(self):
        for chain in self.chains.find():
            yield chain

    def get_chain_with_host(self, host):
        return self.chains.find_one({'host': host})
