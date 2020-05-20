import hashlib
import json
from Block import Block
from time import time

from Transaction import Transaction

"""
区块链的简单实现类
完成了区块链的简单操作
"""


class BlockChain:
    publicBlock = Block(1, 100000000.00000001, [], 520, "No previous hash value")

    def __init__(self):
        self.transactions = []
        self.chain = []
        self.chain.append(BlockChain.publicBlock)

    def createBlock(self, proof: int):
        index = len(self.chain) + 1
        hashValue = self.hash(self.chain[len(self.chain)-1])
        block = Block(index, time(),
                      self.transactions,
                      proof, hashValue
                      )
        # Set to null when all the transactions has been patched
        self.transactions = []
        # Add this new block to the chain
        self.chain.append(block)
        return block

    def addTransaction(self, sender: int, receiver: int, amount: float) -> int:
        """
        生成新的交易信息，将信息加入到待挖区块中
        :param sender: 交易的发送方
        :param receiver: 交易的接受方
        :param amount: 交易数量
        :return: 返回的是交易要插入的区块的index
        """
        newTransaction = Transaction(sender, receiver, amount)
        self.transactions.append(newTransaction)
        return self.lastBlock().index + 1

    def hash(self, block) -> str:
        """
        Hash value of block
        """
        blockInfo = json.dumps(block.toJson(), sort_keys=True).encode()
        return hashlib.sha256(blockInfo).hexdigest()

    def proofWork(self, lastProof: int) -> int:
        """
        :param lastProof: Last proof of POW
        :return: Value of POW
        """
        proof = 0
        while not self.validProof(lastProof, proof):
            proof += 1
        return proof

    @staticmethod
    def validProof(lastproof: int, proof: int) -> bool:
        """
        Verify if the first four bits of hash value are all 0
        :param lastproof: POW of last block
        :param proof: POW of test
        :return: Verify if POW here meets the requirement
        """
        test = f'{lastproof}{proof}'.encode()
        hashStr = hashlib.sha256(test).hexdigest()
        return hashStr[0:4] == "0000"

    def lastBlock(self):
        """
        Retrieve last chain on the blockchain
        """
        try:
            obj = self.chain[-1]
            return obj
        except:
            return None
