from datetime import date
from enum import Enum, auto


class FundTransactionType(Enum):
    INSUFFICIENT_FUNDS = auto()
    PERIODIC = auto()
    ONE_TIME = auto()
    PERIODIC_CHANGE = auto()
    GROWTH = auto()
    BALANCE = auto()
    CONTRIBUTION_SUMMARY = auto()
    APY = auto()
    INFLATION = auto()


class FundTransaction:
    def __init__(self, txn_date: date = None, amount=0.0, txn_type: FundTransactionType = FundTransactionType.ONE_TIME,
                 desc=""):
        self.date = txn_date
        self.amount = amount
        self.type = txn_type
        self.description = desc
