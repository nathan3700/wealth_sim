from enum import Enum, auto
from abc import ABC, abstractmethod
from datetime import date
from datetime import timedelta
from typing import List, Tuple
from fund_transaction import FundTransaction, FundTransactionType


class Frequency(Enum):
    MONTHLY = auto()
    SEMIMONTHLY = auto()
    BIWEEKLY = auto()
    ONCE = auto()
    NONE = auto()


class BaseContributionSchedule(ABC):
    null_date = date(1, 1, 1)

    def __init__(self, amount: float, start_date: date):
        """
        :param amount: The amount that is regularly contributed
        :param start_date: The date that starts a periodic schedule (history don't start until subsequent \
        periods AFTER this date)
        """
        self.frequency = Frequency.NONE
        self.amount = amount
        self.start_date = start_date
        self.last_contribution_date = None  # Must be overriden below
        self.future_one_time_contributions: List[Tuple[date, float]] = []

    @abstractmethod
    def get_contributions_until(self, next_date: date) -> List[FundTransaction]:
        """
        Advances last contribution date to last date of contribution before date
        and returns the amount contributed in that time
        :param next_date: Date to contribute until
        :return: Contributions between the last contribution date and date
        """
        ...

    def get_next_contribution_date(self) -> date:
        """
        :return: Returns the next date on which a contribution will occur
        """
        if (len(self.future_one_time_contributions)
                and (self.future_one_time_contributions[0].__getitem__(0)
                     < self.get_next_periodic_contribution_date() or (
                             self.get_next_periodic_contribution_date() == self.null_date))):
            return self.future_one_time_contributions[0].__getitem__(0)
        else:
            return self.get_next_periodic_contribution_date()

    @abstractmethod
    def get_next_periodic_contribution_date(self) -> date:
        """
        :return: Returns the next date on which a periodic contribution will occur
        """
        ...

    def add_one_time_contribution(self, amount: float, contribution_date: date):
        self.future_one_time_contributions.append((contribution_date, amount))
        # Ensure the list is sorted by date oldest to newest
        self.future_one_time_contributions.sort(key=lambda item: item[0])

    def get_one_time_contributions_to_date(self, next_date) -> List[FundTransaction]:
        contributions: List[FundTransaction] = []
        keep: List[Tuple[date, float]] = []
        for d, a in self.future_one_time_contributions:
            if d <= next_date:
                contributions.append(FundTransaction(d, a, FundTransactionType.ONE_TIME))
            else:
                keep.append((d, a))
        self.future_one_time_contributions = keep
        return contributions

    def inflate_contributions(self, inflation_percent_rate):
        self.amount *= (1 + inflation_percent_rate/100)
        for index in range(len(self.future_one_time_contributions)):
            one_time_date, one_time_value = self.future_one_time_contributions[index]
            new_value = one_time_value * (1 + inflation_percent_rate/100)
            self.future_one_time_contributions[index] = (one_time_date, new_value)


class NoneSchedule(BaseContributionSchedule):
    def __init__(self):
        super().__init__(0, self.null_date)
        self.frequency = Frequency.NONE
        self.last_contribution_date = self.null_date

    def get_contributions_until(self, next_date: date) -> List[FundTransaction]:
        self.last_contribution_date = next_date
        contributions = self.get_one_time_contributions_to_date(next_date)
        return contributions

    def get_next_periodic_contribution_date(self) -> date:
        return self.null_date


class MonthlySchedule(BaseContributionSchedule):
    def __init__(self, amount: float, start_date: date):
        super().__init__(amount, start_date)
        self.frequency = Frequency.MONTHLY
        self.contribution_day = start_date.day
        self.last_contribution_date = start_date
        self.last_contribution_date = self.get_relative_contribution_date(-1)  # Prime to get contribution on 1st day

    def get_contributions_until(self, next_date: date) -> List[FundTransaction]:
        contributions = []
        if next_date > self.last_contribution_date:
            months_elapsed = 12 * (next_date.year - self.last_contribution_date.year) + (
                    next_date.month - self.last_contribution_date.month)
            if months_elapsed > 0 and next_date.day < self.contribution_day:
                months_elapsed -= 1  # Pay day not reached for last month

            self.last_contribution_date = self.get_relative_contribution_date(months_elapsed)

            contributions += [FundTransaction(next_date, self.amount, FundTransactionType.PERIODIC, "Monthly") for i in
                              range(months_elapsed)]
            contributions += self.get_one_time_contributions_to_date(next_date)
        return contributions

    def get_relative_contribution_date(self, months_elapsed):
        year_rollover = (self.last_contribution_date.month - 1 + months_elapsed) // 12
        next_year = self.last_contribution_date.year + year_rollover
        next_month = (self.last_contribution_date.month - 1 + months_elapsed) % 12 + 1
        next_date = date(next_year, next_month, self.contribution_day)
        return next_date

    def get_next_periodic_contribution_date(self) -> date:
        return self.get_relative_contribution_date(1)


class BiweeklySchedule(BaseContributionSchedule):
    def __init__(self, amount: float, start_date: date):
        super().__init__(amount, start_date)
        self.last_contribution_date = start_date
        # Prime it with the last period's date to get a contribution on the 1st day
        self.last_contribution_date = self.get_relative_contribution_date(-1)
        self.frequency = Frequency.BIWEEKLY

    def get_contributions_until(self, next_date: date) -> List[FundTransaction]:
        contributions = []
        if next_date > self.last_contribution_date:
            two_week_periods = ((next_date - self.last_contribution_date).days // 7) // 2
            if two_week_periods < 0:
                two_week_periods = 0
            self.last_contribution_date = self.get_relative_contribution_date(two_week_periods)

            contributions += [FundTransaction(next_date, self.amount, FundTransactionType.PERIODIC, "Biweekly") for i in
                              range(two_week_periods)]
            contributions += self.get_one_time_contributions_to_date(next_date)
        return contributions

    def get_relative_contribution_date(self, two_week_periods) -> date:
        return self.last_contribution_date + timedelta(days=two_week_periods * 14)

    def get_next_periodic_contribution_date(self) -> date:
        return self.get_relative_contribution_date(1)


class SemiMonthlySchedule(BaseContributionSchedule):
    """
    Semi-Monthly schedule on the 1st and 15th of the month
    """
    def __init__(self, amount: float, start_date: date):
        super().__init__(amount, start_date)
        self.frequency = Frequency.SEMIMONTHLY
        # Prime to get contribution on 1st day of start_date
        self.last_contribution_date = self.get_nearest_1st_or_15th(start_date - timedelta(days=1))

    def get_contributions_until(self, next_date: date) -> List[FundTransaction]:
        contributions = []
        contributions += self.get_one_time_contributions_to_date(next_date)  # Handle these before changing next_date
        next_date = self.get_nearest_1st_or_15th(next_date)
        if next_date > self.last_contribution_date:
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

            contributions += [FundTransaction(next_date, self.amount, FundTransactionType.PERIODIC, "Semi-Monthly") for i in
                              range(elapsed_contributions)]
        return contributions

    @staticmethod
    def get_nearest_1st_or_15th(next_date):
        if next_date.day < 15:
            nearest_1st_or_15th = date(next_date.year, next_date.month, 1)
        else:
            nearest_1st_or_15th = date(next_date.year, next_date.month, 15)
        return nearest_1st_or_15th

    def get_next_periodic_contribution_date(self) -> date:
        # use a timedelta that ensures we wrap into the next month in case of a 31-day month
        return self.get_nearest_1st_or_15th(self.last_contribution_date + timedelta(days=20))
