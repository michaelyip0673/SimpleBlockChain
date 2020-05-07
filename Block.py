import json
from typing import List


class Block:
    def __init__(self, index: int, timestamp,
                 transactions: List, proof: int,
                 previous_Hash: str):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.proof = proof
        self.previous_Hash = previous_Hash

    def toJson(self):
        temp = {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [i.toJsonStr() for i in self.transactions],
            'proof': self.proof,
            'previous_Hash': self.previous_Hash
        }
        return temp
