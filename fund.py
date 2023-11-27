from contribution_schedule import *


class FundError(Exception):
    pass


class Fund:
    def __init__(self,  inception_date: date, name="No Name Fund"):
        self.history: List[FundTransaction] = []
        self.balance_history: List[FundTransaction] = []
        self.balance = 0.0
        self.apy = 0.0  # Annual Percentage Yield
        self.daily_rate = 0.0
        self.verbose = True
        self.name = name
        self.inception_date = inception_date
        self.current_date = inception_date
        self.contribution_schedule = NoneSchedule()

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
                self.print(
                    f"Fund {self.name}-contribution frequency is changing from {self.contribution_schedule.frequency} to {frequency}")
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
            next_contrib = self.contribution_schedule.get_next_contribution_date()
            if self.current_date < next_contrib <= new_date:
                self.advance_time_partial(next_contrib)
            else:
                self.advance_time_partial(new_date)
        self.balance_history.append(FundTransaction(new_date, self.get_balance(), FundTransactionType.BALANCE))

    def advance_time_partial(self, new_date: date):
        new_contributions = self.contribution_schedule.get_contributions_until(new_date)
        self.history += new_contributions

        # Apply growth first before new history
        elapsed_days = (new_date - self.current_date).days
        growth = self.balance * ((1 + self.daily_rate) ** elapsed_days) - self.balance
        self.history.append(FundTransaction(new_date, growth, FundTransactionType.GROWTH))

        self.balance += growth + self.add_up(new_contributions)
        self.current_date = new_date

    def set_apy(self, apy):
        self.apy = apy
        simple_daily_rate = apy/(365 * 100)
        annual_rate_with_simple_daily_rate = (1 + apy/36500) ** 365 - 1
        # Make the daily rate a little lower so that when compounded daily it will still come out to APY
        correction_factor = 1.0
        if apy > 0:
            correction_factor = (apy/100) / annual_rate_with_simple_daily_rate
        effective_daily_rate = simple_daily_rate * correction_factor
        self.daily_rate = effective_daily_rate

    def set_daily_rate(self, daily_rate):
        self.daily_rate = daily_rate
        self.apy = (1 + daily_rate) ** 365 - 1

    def get_balance(self) -> float:
        return self.balance

    def get_current_date(self):
        return self.current_date

    def print(self, info):
        if self.verbose:
            print(info)

    @staticmethod
    def add_up(contributions: List[FundTransaction]):
        amounts = [c.amount for c in contributions]
        return sum(amounts)
