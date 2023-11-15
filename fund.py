from enum import Enum, auto
from abc import ABC, abstractmethod
from datetime import datetime, timedelta


class Frequency(Enum):
    MONTHLY = auto()
    SEMIMONTHLY = auto()
    BIWEEKLY = auto()
    ONCE = auto()


class Contribution(ABC):
    def __init__(self, amount: float, start_date: datetime):
        self.amount = amount
        self.last_contribution_date = start_date

    @abstractmethod
    def contribute_until_date(self, date: datetime) -> float:
        """
        Advances last contribution date to last date of contribution before date
        and returns the amount contributed in that time

        :param date: Date to contribute until
        :return: Amount contributed between the last contribution date and date
        """
        ...


class MonthlyContribution(Contribution):
    def contribute_until_date(self, date: datetime) -> float:
        months = 12*(date.year - self.last_contribution_date.year) + (date.month - self.last_contribution_date.month)
        self.last_contribution_date = datetime(self.last_contribution_date.year, self.last_contribution_date.month+months, self.last_contribution_date.day)
        return self.amount * months


class BiweeklyContribution(Contribution):
    def contribute_until_date(self, date: datetime) -> float:
        two_week_periods = ((date - self.last_contribution_date).days//7)//2
        self.last_contribution_date += timedelta(days=two_week_periods*14)
        return self.amount * two_week_periods


class Fund:
    def __init__(self):
        self.current_date = datetime.now()
        self.balance = 0.0
        self.contributions: list[Contribution] = []

    def contribute(self, amount: float, date: datetime = None, *, frequency: Frequency = Frequency.ONCE) -> None:
        if date is None:
            date = datetime.now()
        self.current_date = date
        if frequency == Frequency.ONCE:
            self.balance += amount
        if frequency == Frequency.MONTHLY:
            self.contributions.append(MonthlyContribution(amount, date))
        if frequency == Frequency.BIWEEKLY:
            self.contributions.append(BiweeklyContribution(amount, date))

    def get_balance(self) -> float:
        return self.balance

    def advance_time(self, new_date: datetime = None):
        if new_date is None:
            new_date = datetime.now()

        for contribution in self.contributions:
            self.balance += contribution.contribute_until_date(new_date)

        self.current_date = new_date

