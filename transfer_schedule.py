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


class BaseTransferSchedule(ABC):
    null_date = date(1, 1, 1)

    def __init__(self, amount: float, start_date: date):
        """
        :param amount: The amount that is regularly transferred
        :param start_date: The date that starts a periodic schedule (history don't start until subsequent \
        periods AFTER this date)
        """
        self.frequency = Frequency.NONE
        self.amount = amount
        self.start_date = start_date
        self.last_transfer_date = None  # Must be overriden below
        self.future_one_time_transfers: List[Tuple[date, float]] = []

    @abstractmethod
    def get_transfers_until(self, next_date: date) -> List[FundTransaction]:
        """
        Advances last transfer date to last date of transfer before date
        and returns the amount contributed in that time
        :param next_date: Date to contribute until
        :return: transfers between the last transfer date and date
        """
        ...

    def get_next_transfer_date(self) -> date:
        """
        :return: Returns the next date on which a transfer will occur
        """
        if (len(self.future_one_time_transfers)
                and (self.future_one_time_transfers[0].__getitem__(0)
                     < self.get_next_periodic_transfer_date() or (
                             self.get_next_periodic_transfer_date() == self.null_date))):
            return self.future_one_time_transfers[0].__getitem__(0)
        else:
            return self.get_next_periodic_transfer_date()

    @abstractmethod
    def get_next_periodic_transfer_date(self) -> date:
        """
        :return: Returns the next date on which a periodic transfer will occur
        """
        ...

    def add_one_time_transfer(self, amount: float, transfer_date: date):
        self.future_one_time_transfers.append((transfer_date, amount))
        # Ensure the list is sorted by date oldest to newest
        self.future_one_time_transfers.sort(key=lambda item: item[0])

    def get_one_time_transfers_to_date(self, next_date) -> List[FundTransaction]:
        transfers: List[FundTransaction] = []
        keep: List[Tuple[date, float]] = []
        for d, a in self.future_one_time_transfers:
            if d <= next_date:
                transfers.append(FundTransaction(d, a, FundTransactionType.ONE_TIME))
            else:
                keep.append((d, a))
        self.future_one_time_transfers = keep
        return transfers

    def inflate_transfer_amounts(self, inflation_percent_rate):
        self.amount *= (1 + inflation_percent_rate/100)
        for index in range(len(self.future_one_time_transfers)):
            one_time_date, one_time_value = self.future_one_time_transfers[index]
            new_value = one_time_value * (1 + inflation_percent_rate/100)
            self.future_one_time_transfers[index] = (one_time_date, new_value)


class NoneSchedule(BaseTransferSchedule):
    def __init__(self):
        super().__init__(0, self.null_date)
        self.frequency = Frequency.NONE
        self.last_transfer_date = self.null_date

    def get_transfers_until(self, next_date: date) -> List[FundTransaction]:
        self.last_transfer_date = next_date
        transfers = self.get_one_time_transfers_to_date(next_date)
        return transfers

    def get_next_periodic_transfer_date(self) -> date:
        return self.null_date


class MonthlySchedule(BaseTransferSchedule):
    def __init__(self, amount: float, start_date: date):
        super().__init__(amount, start_date)
        self.frequency = Frequency.MONTHLY
        self.transfer_day = start_date.day
        self.last_transfer_date = start_date
        self.last_transfer_date = self.get_relative_transfer_date(-1)  # Prime to get transfer on 1st day

    def get_transfers_until(self, next_date: date) -> List[FundTransaction]:
        transfers = []
        if next_date > self.last_transfer_date:
            months_elapsed = 12 * (next_date.year - self.last_transfer_date.year) + (
                    next_date.month - self.last_transfer_date.month)
            if months_elapsed > 0 and next_date.day < self.transfer_day:
                months_elapsed -= 1  # Pay day not reached for last month

            self.last_transfer_date = self.get_relative_transfer_date(months_elapsed)

            transfers += [FundTransaction(next_date, self.amount, FundTransactionType.PERIODIC, "Monthly") for i in
                              range(months_elapsed)]
            transfers += self.get_one_time_transfers_to_date(next_date)
        return transfers

    def get_relative_transfer_date(self, months_elapsed):
        year_rollover = (self.last_transfer_date.month - 1 + months_elapsed) // 12
        next_year = self.last_transfer_date.year + year_rollover
        next_month = (self.last_transfer_date.month - 1 + months_elapsed) % 12 + 1
        next_date = date(next_year, next_month, self.transfer_day)
        return next_date

    def get_next_periodic_transfer_date(self) -> date:
        return self.get_relative_transfer_date(1)


class BiweeklySchedule(BaseTransferSchedule):
    def __init__(self, amount: float, start_date: date):
        super().__init__(amount, start_date)
        self.last_transfer_date = start_date
        # Prime it with the last period's date to get a transfer on the 1st day
        self.last_transfer_date = self.get_relative_transfer_date(-1)
        self.frequency = Frequency.BIWEEKLY

    def get_transfers_until(self, next_date: date) -> List[FundTransaction]:
        transfers = []
        if next_date > self.last_transfer_date:
            two_week_periods = ((next_date - self.last_transfer_date).days // 7) // 2
            if two_week_periods < 0:
                two_week_periods = 0
            self.last_transfer_date = self.get_relative_transfer_date(two_week_periods)

            transfers += [FundTransaction(next_date, self.amount, FundTransactionType.PERIODIC, "Biweekly") for i in
                              range(two_week_periods)]
            transfers += self.get_one_time_transfers_to_date(next_date)
        return transfers

    def get_relative_transfer_date(self, two_week_periods) -> date:
        return self.last_transfer_date + timedelta(days=two_week_periods * 14)

    def get_next_periodic_transfer_date(self) -> date:
        return self.get_relative_transfer_date(1)


class SemiMonthlySchedule(BaseTransferSchedule):
    """
    Semi-Monthly schedule on the 1st and 15th of the month
    """
    def __init__(self, amount: float, start_date: date):
        super().__init__(amount, start_date)
        self.frequency = Frequency.SEMIMONTHLY
        # Prime to get transfer on 1st day of start_date
        self.last_transfer_date = self.get_nearest_1st_or_15th(start_date - timedelta(days=1))

    def get_transfers_until(self, next_date: date) -> List[FundTransaction]:
        transfers = []
        transfers += self.get_one_time_transfers_to_date(next_date)  # Handle these before changing next_date
        next_date = self.get_nearest_1st_or_15th(next_date)
        if next_date > self.last_transfer_date:
            months = 12 * (next_date.year - self.last_transfer_date.year) + (
                        next_date.month - self.last_transfer_date.month)
            elapsed_transfers = 0
            if months >= 0:
                elapsed_transfers = months * 2
                if next_date.day > self.last_transfer_date.day:
                    elapsed_transfers += 1
                elif next_date.day < self.last_transfer_date.day:
                    elapsed_transfers -= 1
            if elapsed_transfers:
                self.last_transfer_date = next_date

            transfers += [FundTransaction(next_date, self.amount, FundTransactionType.PERIODIC, "Semi-Monthly") for i in
                              range(elapsed_transfers)]
        return transfers

    @staticmethod
    def get_nearest_1st_or_15th(next_date):
        if next_date.day < 15:
            nearest_1st_or_15th = date(next_date.year, next_date.month, 1)
        else:
            nearest_1st_or_15th = date(next_date.year, next_date.month, 15)
        return nearest_1st_or_15th

    def get_next_periodic_transfer_date(self) -> date:
        # use a timedelta that ensures we wrap into the next month in case of a 31-day month
        return self.get_nearest_1st_or_15th(self.last_transfer_date + timedelta(days=20))
