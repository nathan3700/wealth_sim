from enum import Enum, auto
from abc import ABC, abstractmethod
from datetime import date
from datetime import timedelta


class Frequency(Enum):
    MONTHLY = auto()
    SEMIMONTHLY = auto()
    BIWEEKLY = auto()
    ONCE = auto()
    NONE = auto()


class BaseContributionSchedule(ABC):
    def __init__(self, amount: float, reference_date: date):
        """
        :param amount: The amount that is regularly contributed
        :param reference_date: The date that starts a periodic schedule (contributions don't start until subsequent \
        periods AFTER this date)
        """
        self.frequency = Frequency.NONE
        self.amount = amount
        self.last_contribution_date = reference_date

    @abstractmethod
    def contribute_until_date(self, date: date) -> float:
        """
        Advances last contribution date to last date of contribution before date
        and returns the amount contributed in that time
        :param date: Date to contribute until
        :return: Amount contributed between the last contribution date and date
        """
        ...


class NoneSchedule(BaseContributionSchedule):
    def __init__(self):
        super().__init__(0, date(1900, 1, 1))
        self.frequency = Frequency.NONE

    def contribute_until_date(self, next_date: date) -> float:
        self.last_contribution_date = next_date
        return self.amount


class MonthlySchedule(BaseContributionSchedule):
    def __init__(self, amount: float, reference_date: date):
        super().__init__(amount, reference_date)
        self.frequency = Frequency.MONTHLY

    def contribute_until_date(self, next_date: date) -> float:
        months = 12 * (next_date.year - self.last_contribution_date.year) + (
                    next_date.month - self.last_contribution_date.month)
        elapsed_contributions = months
        if next_date.day < self.last_contribution_date.day:
            elapsed_contributions -= 1  # Pay day not reached for last month

        if elapsed_contributions < 0:
            elapsed_contributions = 0
        self.last_contribution_date = \
            date(self.last_contribution_date.year + elapsed_contributions // 12,
                 self.last_contribution_date.month + elapsed_contributions % 12,
                 self.last_contribution_date.day)
        return self.amount * elapsed_contributions


class BiweeklySchedule(BaseContributionSchedule):
    def __init__(self, amount: float, reference_date: date):
        super().__init__(amount, reference_date)
        self.frequency = Frequency.BIWEEKLY

    def contribute_until_date(self, next_date: date) -> float:
        two_week_periods = ((next_date - self.last_contribution_date).days // 7) // 2
        if two_week_periods < 0:
            two_week_periods = 0
        self.last_contribution_date += timedelta(days=two_week_periods * 14)
        return self.amount * two_week_periods


class SemiMonthlySchedule(BaseContributionSchedule):
    """
    Semi-Monthly schedule on the 1st and 15th of the month
    """

    def __init__(self, amount: float, reference_date: date):
        super().__init__(amount, reference_date)
        self.frequency = Frequency.SEMIMONTHLY
        self.last_contribution_date = self.get_nearest_1st_or_15th(self.last_contribution_date)

    def contribute_until_date(self, next_date: date) -> float:
        next_date = self.get_nearest_1st_or_15th(next_date)

        months = 12 * (next_date.year - self.last_contribution_date.year) + (
                    next_date.month - self.last_contribution_date.month)
        elapsed_contributions = 0
        if months >= 0:
            elapsed_contributions = months * 2
            if next_date.day > self.last_contribution_date.day:
                elapsed_contributions += 1
            elif next_date.day < self.last_contribution_date.day:
                elapsed_contributions -= 1
        if elapsed_contributions:
            self.last_contribution_date = next_date
        return self.amount * elapsed_contributions

    @staticmethod
    def get_nearest_1st_or_15th(next_date):
        if next_date.day < 15:
            nearest_1st_or_15th = date(next_date.year, next_date.month, 1)
        else:
            nearest_1st_or_15th = date(next_date.year, next_date.month, 15)
        return nearest_1st_or_15th
