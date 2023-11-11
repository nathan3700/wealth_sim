from enum import Enum, auto
from datetime import datetime, timedelta


class Frequency(Enum):
    MONTHLY = auto()
    SEMIMONTHLY = auto()
    BIWEEKLY = auto()
    ONCE = auto()


class Fund:
    def __init__(self):
        self.start_date = datetime.now()
        self.current_date = datetime.now()
        self.balance = 0.0
        self.monthly_contribution = []
        self.biweekly_contribution = []

    def contribute(self, amount: float, date: datetime = None, *, frequency: Frequency = Frequency.ONCE) -> None:
        if date is None:
            date = datetime.now()
        self.start_date = date
        self.current_date = date
        if frequency == Frequency.ONCE:
            self.balance += amount
        if frequency == Frequency.MONTHLY:
            self.monthly_contribution.append(amount)
        if frequency == Frequency.BIWEEKLY:
            self.biweekly_contribution.append(amount)

    def get_balance(self) -> float:
        return self.balance

    def advance_time(self, new_date: datetime = None):
        if new_date is None:
            new_date = datetime.now()
        months = (new_date.year - self.current_date.year) * 12 + (new_date.month - self.current_date.month)
        weeks = (new_date - self.current_date).days//7
        for monthly in self.monthly_contribution:
            self.balance += months * monthly
        for biweekly in self.biweekly_contribution:
            self.balance += (weeks//2) * biweekly

        self.current_date = new_date

