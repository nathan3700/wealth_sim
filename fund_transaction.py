from datetime import date
from enum import Enum, auto


class FundTransactionType(Enum):
    PERIODIC = auto()
    ONE_TIME = auto()
    GROWTH = auto()


class FundTransaction:
    def __init__(self, txn_date: date = None, amount=0.0, txn_type: FundTransactionType = FundTransactionType.ONE_TIME,
                 desc=""):
        self.date = txn_date
        self.amount = amount
        self.type: txn_type
        self.description = desc
