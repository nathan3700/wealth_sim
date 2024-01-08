import math

from contribution_schedule import *


class FundError(Exception):
    pass


class Fund:
    def __init__(self,  inception_date: date, name="No Name Fund"):
        self.balance = 0.0
        self.apy = 0.0  # Annual Percentage Yield
        self.daily_rate = 0.0
        self.inflation_rate = 0
        self.verbose = True
        self.name = name
        self.inception_date = inception_date
        self.current_date = inception_date
        self.contribution_schedule = NoneSchedule()
        self.history: List[FundTransaction] = []
        self.total_contributions = 0.0
        self.contributions_this_year = 0.0
        self.total_growth = 0.0

    def contribute(self, amount: float, start_date: date, frequency: Frequency = Frequency.ONCE) -> None:
        if start_date <= self.current_date:
            raise FundError("Contributions must be scheduled in the future.\n" +
                            f"Fund's current date is {self.current_date}, contribution date is {start_date}")
        # There can only be one periodic schedule.  A new frequency will replace an old one.
        # ONCE is special in that it can be scheduled now without replacing a periodic schedule
        if frequency == Frequency.ONCE:
            self.contribution_schedule.add_one_time_contribution(amount, start_date)
        else:
            # The remaining types will cause a change to the schedule
            if self.contribution_schedule.frequency is not frequency:
                self.history.append(
                    FundTransaction(start_date, amount, FundTransactionType.PERIODIC_CHANGE,
                                    desc=f"Change from {self.contribution_schedule.frequency} to {frequency}"))

            if frequency == Frequency.NONE:
                self.contribution_schedule = NoneSchedule()
            elif frequency == Frequency.MONTHLY:
                self.contribution_schedule = MonthlySchedule(amount, start_date)
            elif frequency == Frequency.BIWEEKLY:
                self.contribution_schedule = BiweeklySchedule(amount, start_date)
            elif frequency == Frequency.SEMIMONTHLY:
                self.contribution_schedule = SemiMonthlySchedule(amount, start_date)

    def advance_time(self, new_date: date):
        if new_date < self.current_date:
            raise FundError(
                f"advance_time is advancing to a date in the past.  Current Fund Date {self.current_date}, Next Date {new_date}")
        while self.current_date < new_date:
            next_contrib_date = self.contribution_schedule.get_next_contribution_date()
            if self.current_date < next_contrib_date <= new_date:
                self.advance_time_partial(next_contrib_date)
            else:
                self.advance_time_partial(new_date)

    def advance_time_partial(self, new_date: date):
        if new_date.year > self.current_date.year:
            self.do_end_of_year_accounting()
        new_contrib_records = self.contribution_schedule.get_contributions_until(new_date)
        self.history += new_contrib_records
        new_contributions = self.add_up(new_contrib_records)
        self.contributions_this_year = self.nearest_hundredth(self.contributions_this_year + new_contributions)
        self.total_contributions = self.nearest_hundredth(self.total_contributions + new_contributions)

        # Apply growth first before new history
        elapsed_days = (new_date - self.current_date).days
        growth = self.nearest_hundredth(self.balance * ((1 + self.daily_rate) ** elapsed_days) - self.balance)
        self.history.append(FundTransaction(new_date, growth, FundTransactionType.GROWTH))
        self.total_growth = self.nearest_hundredth(self.total_growth + growth)

        self.balance = self.nearest_hundredth(self.balance + growth + new_contributions)
        if self.balance < 0:
            underflow = 0 - self.balance
            self.balance = 0
            self.history.append(FundTransaction(new_date, underflow, FundTransactionType.INSUFFICIENT_FUNDS))
        self.current_date = new_date

    def do_end_of_year_accounting(self):
        last_day_of_year = date(self.current_date.year, 12, 31)
        self.contribution_schedule.inflate_contributions(self.inflation_rate)
        self.history.append(FundTransaction(last_day_of_year, self.get_balance(), FundTransactionType.BALANCE))
        self.history.append(FundTransaction(last_day_of_year, self.apy, FundTransactionType.APY))
        self.history.append(FundTransaction(last_day_of_year, self.inflation_rate, FundTransactionType.INFLATION))
        self.history.append(
            FundTransaction(last_day_of_year, self.contributions_this_year, FundTransactionType.CONTRIBUTION_SUMMARY,
                            desc="Sum of contributions over the year"))
        self.contributions_this_year = 0.0

    def get_current_date(self):
        return self.current_date

    @classmethod
    def nearest_hundredth(cls, value):
        return round(value * 100) / 100

    def set_apy(self, apy):
        self.apy = apy
        # This equation solves for daily rate based on a desired
        # yearly yield assuming 365 days in the year
        # When the input is -100% (a total loss),
        # we must use an absolute value slightly less than 100 to prevent log(0)
        if apy == -100:
            apy = -99.9999
        self.daily_rate = math.exp(math.log((apy/100)+1)/365) - 1

    def set_daily_rate(self, daily_rate):
        self.daily_rate = daily_rate
        self.apy = self.nearest_hundredth((1 + daily_rate) ** 365 - 1) * 100

    def get_balance(self) -> float:
        return self.balance

    def set_inflation_rate(self, rate):
        self.inflation_rate = rate

    def print(self, info):
        if self.verbose:
            print(info)

    def add_up(self, contributions: List[FundTransaction]):
        amounts = [c.amount for c in contributions]
        return self.nearest_hundredth(sum(amounts))
