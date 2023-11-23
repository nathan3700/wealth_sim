from contribution_schedule import *


class Fund:
    def __init__(self, name="No Name Fund"):
        self.contributions = 0.0
        self.balance = 0.0
        self.apy = 0.0  # Annual Percentage Yield
        self.daily_interest = 0.0
        self.verbose = True
        self.name = name
        self.current_date = date.today()
        self.contribution_schedule = NoneSchedule()

    def contribute(self, amount: float, reference_date: date = None, *, frequency: Frequency = Frequency.ONCE) -> None:
        if reference_date is None:
            reference_date = date.today()
        self.current_date = reference_date
        # ONCE is special, contribute *now*, not over time
        # And this can be done at any time without replacing a periodic schedule
        if frequency == Frequency.ONCE:
            self.balance += amount
        # The remaining types will cause a change to the schedule
        if self.contribution_schedule.frequency is not frequency:
            self.print(
                f"Fund {self.name}-contribution frequency is changing from {self.contribution_schedule.frequency} to {frequency}")
        if frequency == Frequency.NONE:
            self.contribution_schedule = NoneSchedule()
        elif frequency == Frequency.MONTHLY:
            self.contribution_schedule = MonthlySchedule(amount, reference_date)
        elif frequency == Frequency.BIWEEKLY:
            self.contribution_schedule = BiweeklySchedule(amount, reference_date)
        elif frequency == Frequency.SEMIMONTHLY:
            self.contribution_schedule = SemiMonthlySchedule(amount, reference_date)

    def set_apy(self, apy):
        self.apy = apy
        self.daily_interest = (apy/100)/365

    def get_balance(self) -> float:
        return self.balance

    def advance_time(self, new_date: date = None):
        if new_date is None:
            new_date = date.today()
        new_contributions = self.contribution_schedule.contribute_until_date(new_date)
        self.contributions += new_contributions
        self.balance += new_contributions
        elapsed_days = (new_date - self.current_date).days
        self.balance = self.balance * ((1 + self.daily_interest) ** elapsed_days)

        self.current_date = new_date

    def print(self, info):
        if self.verbose:
            print(info)

