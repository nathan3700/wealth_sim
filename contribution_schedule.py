from enum import Enum, auto
from abc import ABC, abstractmethod
from datetime import date
from datetime import timedelta
from typing import List, Tuple

class Frequency(Enum):
    MONTHLY = auto()
    SEMIMONTHLY = auto()
    BIWEEKLY = auto()
    ONCE = auto()
    NONE = auto()


class BaseContributionSchedule(ABC):
    def __init__(self, amount: float, start_date: date):
        """
        :param amount: The amount that is regularly contributed
        :param start_date: The date that starts a periodic schedule (contributions don't start until subsequent \
        periods AFTER this date)
        """
        self.frequency = Frequency.NONE
        self.amount = amount
        self.start_date = start_date
        self.last_contribution_date = None  # Must be overriden below
        self.future_one_time_contributions: List[Tuple[date, float]] = []

    @abstractmethod
    def contribute_until_date(self, next_date: date) -> float:
        """
        Advances last contribution date to last date of contribution before date
        and returns the amount contributed in that time
        :param next_date: Date to contribute until
        :return: Amount contributed between the last contribution date and date
        """
        ...

    @abstractmethod
    def get_next_contribution_date(self) -> date:
        """
        :return: Returns the next date on which a contribution will occur
        """
        ...

    def add_one_time_contribution(self, amount: float, contribution_date: date):
        self.future_one_time_contributions.append((contribution_date, amount))
        # Ensure the list is sorted by date oldest to newest
        self.future_one_time_contributions.sort(key=lambda item: item[0])

    def get_one_time_contributions_to_date(self, next_date) -> List[float]:
        contributions: List[float] = []
        keep: List[Tuple[date, float]] = []
        for d, a in self.future_one_time_contributions:
            if d <= next_date:
                contributions.append(a)
            else:
                keep.append((d, a))
        self.future_one_time_contributions = keep
        return contributions


class NoneSchedule(BaseContributionSchedule):
    def __init__(self):
        super().__init__(0, date(1, 1, 1))
        self.frequency = Frequency.NONE
        self.last_contribution_date = date(1, 1, 1)

    def contribute_until_date(self, next_date: date) -> float:
        self.last_contribution_date = next_date
        return self.amount

    def get_next_contribution_date(self) -> date:
        return date(1, 1, 1)


class MonthlySchedule(BaseContributionSchedule):
    def __init__(self, amount: float, start_date: date):
        super().__init__(amount, start_date)
        self.frequency = Frequency.MONTHLY
        self.contribution_day = start_date.day
        self.last_contribution_date = start_date
        self.last_contribution_date = self.get_relative_contribution_date(-1)  # Prime to get contribution on 1st day

    def contribute_until_date(self, next_date: date) -> float:
        if next_date > self.last_contribution_date:
            months_elapsed = 12 * (next_date.year - self.last_contribution_date.year) + (
                        next_date.month - self.last_contribution_date.month)
            if months_elapsed > 0 and next_date.day < self.contribution_day:
                months_elapsed -= 1  # Pay day not reached for last month

            self.last_contribution_date = self.get_relative_contribution_date(months_elapsed)
            contributions = []
            for i in range(months_elapsed):
                contributions.append(self.amount)
            contributions += self.get_one_time_contributions_to_date(next_date)
            return sum(contributions)
        else:
            return 0.0

    def get_relative_contribution_date(self, months_elapsed):
        year_rollover = (self.last_contribution_date.month - 1 + months_elapsed) // 12
        next_year = self.last_contribution_date.year + year_rollover
        next_month = (self.last_contribution_date.month - 1 + months_elapsed) % 12 + 1
        next_date = date(next_year, next_month, self.contribution_day)
        return next_date

    def get_next_contribution_date(self) -> date:
        return self.get_relative_contribution_date(1)


class BiweeklySchedule(BaseContributionSchedule):
    def __init__(self, amount: float, start_date: date):
        super().__init__(amount, start_date)
        self.last_contribution_date = start_date
        # Prime it with the last period's date to get a contribution on the 1st day
        self.last_contribution_date = self.get_relative_contribution_date(-1)
        self.frequency = Frequency.BIWEEKLY

    def contribute_until_date(self, next_date: date) -> float:
        if next_date > self.last_contribution_date:
            two_week_periods = ((next_date - self.last_contribution_date).days // 7) // 2
            if two_week_periods < 0:
                two_week_periods = 0
            self.last_contribution_date = self.get_relative_contribution_date(two_week_periods)
            contributions = []
            for i in range(two_week_periods):
                contributions.append(self.amount)
            contributions += self.get_one_time_contributions_to_date(next_date)
            return sum(contributions)
        else:
            return 0.0

    def get_relative_contribution_date(self, two_week_periods) -> date:
        return self.last_contribution_date + timedelta(days=two_week_periods * 14)

    def get_next_contribution_date(self) -> date:
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

    def contribute_until_date(self, next_date: date) -> float:
        contributions = []
        contributions += self.get_one_time_contributions_to_date(next_date)

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
            for i in range(elapsed_contributions):
                contributions.append(self.amount)
        return sum(contributions)

    @staticmethod
    def get_nearest_1st_or_15th(next_date):
        if next_date.day < 15:
            nearest_1st_or_15th = date(next_date.year, next_date.month, 1)
        else:
            nearest_1st_or_15th = date(next_date.year, next_date.month, 15)
        return nearest_1st_or_15th

    def get_next_contribution_date(self) -> date:
        # use a timedelta that ensures we wrap into the next month in case of a 31-day month
        return self.get_nearest_1st_or_15th(self.last_contribution_date + timedelta(days=20))
