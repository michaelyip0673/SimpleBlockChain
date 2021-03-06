# @Time    : 2020/5/7 17:45
# @Author  : ZHAO Zhipeng
# @FileName: db.py
# coding:utf-8
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
import json
from typing import *

engine = create_engine('mysql+mysqlconnector://root:yyl88325000@localhost:3306/blockchain')
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Block(Base):
    __tablename__ = 'blockchain'
    index = Column(Integer, primary_key=True)
    timestamp = Column(String(50), nullable=False)
    proof = Column(Integer, nullable=False)
    previous_hash = Column(String(200), nullable=False)
    transactions = Column(String(2000), nullable=False)


class Operator(object):
    def __init__(self):
        self.session = Session()

    def add_one(self, index: int, timestamp: str,
                proof: int, previous_hash: str, transactions):
        transactions_str = ''.join(str(i) for i in transactions)
        new_obj = Block(
            index=index,
            timestamp=str(timestamp),
            proof=proof,
            previous_hash=previous_hash,
            transactions=transactions_str
        )
        self.session.add(new_obj)
        self.session.commit()


def init_db():
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    init_db()


