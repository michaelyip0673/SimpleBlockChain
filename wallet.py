import random
from ecdsa.util import PRNG
from ecdsa import SigningKey


class Wallet:
    def __init__(self, id: int):
        self.id = id
        rng = PRNG(str(random.random()))
        self.privateKey = SigningKey.generate(entropy=rng)
        self.publicKey = self.privateKey.get_verifying_key()
        self.UTXOs = []

    def addUTXOs(self, utxo):
        self.UTXOs.append(utxo)

    def replaceUTXOs(self, index, utxo):
        self.UTXOs[index] = utxo