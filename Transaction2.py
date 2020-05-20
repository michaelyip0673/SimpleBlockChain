import json
from typing import *
import hashlib

class Transaction2:
    """
    存储交易信息的类
    包括交易发送人，交易接受人，交易数量信息
    """

    def __init__(self, index: int, address: str, amount: float, pre_transaction_ID: str, pre_index: str, signature: str ):
        self.index = index
        self.address = address
        self.amount = amount
        self.pre_transaction_ID = pre_transaction_ID
        self.transaction_ID = ""
        self.pre_index = pre_index
        self.signature = signature

    def toJsonStr(self):
        return {
            'index' : self.index,
            'address': self.address,
            'amount': self.amount,
            'Transaction_ID': self.transaction_ID,
            'Previous_transaction_ID': self.pre_transaction_ID,
            'Previous index': self.pre_index,
            'Signature': self.signature
        }

    def minetransaction_ID(self):
        content = ((str(self.index) + str(self.address) + str(self.amount))).encode()
        self.transaction_ID = hashlib.sha256(content).hexdigest()

    def normaltransaction_ID(self):
        content = ((str(self.index) + str(self.address) + str(self.amount) + self.pre_transaction_ID)).encode()
        self.transaction_ID = hashlib.sha256(content).hexdigest()




