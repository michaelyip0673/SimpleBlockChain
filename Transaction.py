import json
from typing import *


class Transaction:
    """
    存储交易信息的类
    包括交易发送人，交易接受人，交易数量信息
    """

    def __init__(self, sender: str, receiver: str, amount: int):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount

    def toJsonStr(self):
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount
        }
